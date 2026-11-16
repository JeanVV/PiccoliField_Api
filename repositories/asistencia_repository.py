from datetime import datetime, timedelta

class AsistenciaRepository:
    def __init__(self, connection):
        self.connection = connection

    # ── 1. RESUMEN DEL DÍA ───────────────────────────────────────────────────
    def get_resumen(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    COUNT(u.idUsuario) AS total,
                    COALESCE(SUM(CASE WHEN a.estado IN ('A_TIEMPO', 'TARDANZA') THEN 1 ELSE 0 END), 0) AS presentes,
                    COALESCE(SUM(CASE WHEN a.estado = 'A_TIEMPO' THEN 1 ELSE 0 END), 0) AS aTiempo,
                    COALESCE(SUM(CASE WHEN a.estado = 'TARDANZA' THEN 1 ELSE 0 END), 0) AS tardanzas
                FROM USUARIOS u
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE()
                    AND a.tipo = 'INGRESO'
                WHERE u.estado = 'ACTIVO' AND u.rol != 'ADMINISTRADOR'
            """
            cursor.execute(sql)
            return cursor.fetchone()
        finally:
            cursor.close()

    # ── 2. ASISTENCIAS RECIENTES ─────────────────────────────────────────────
    def get_recientes(self, limite=10):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    a.idAsistencias,
                    a.idAsistencias AS id_turno,
                    a.tipo,
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.url_foto AS foto_perfil,
                    s.sede,
                    a.estado,
                    DATE_FORMAT(a.fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_dispositivo,
                    DATE_FORMAT(a.fecha_hora_servidor, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_servidor,
                    a.minutos_tardanza,
                    a.latitud,
                    a.longitud
                FROM ASISTENCIAS a
                INNER JOIN USUARIOS u ON a.idUsuario = u.idUsuario
                INNER JOIN SEDES s ON u.idSede = s.idSede
                WHERE DATE(a.fecha_hora_servidor) = CURDATE()
                ORDER BY a.fecha_hora_servidor DESC
                LIMIT %s
            """
            cursor.execute(sql, (limite,))
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 3. LISTA DE COLABORADORES CON ESTADO Y JUSTIFICACIÓN ─────────────────
    def get_colaboradores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.url_foto AS foto_perfil,
                    s.sede,
                    a.idAsistencias,
                    COALESCE(a.estado, 'SIN_REGISTRO') AS estado,
                    DATE_FORMAT(a.fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_dispositivo,
                    COALESCE(a.minutos_tardanza, 0) AS minutos_tardanza,
                    a.latitud,
                    a.longitud,
                    j.motivo AS motivoJustificacion,
                    j.descripcion AS justificacion,
                    j.estado AS estadoJustificacion
                FROM USUARIOS u
                INNER JOIN SEDES s ON u.idSede = s.idSede
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE() 
                    AND a.tipo = 'INGRESO'
                LEFT JOIN JUSTIFICACIONES j ON a.idAsistencias = j.idAsistencias
                WHERE u.estado = 'ACTIVO' AND u.rol != 'ADMINISTRADOR'
                ORDER BY a.fecha_hora_servidor DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 4. HISTORIAL DE TURNOS DE UN USUARIO ─────────────────────────────────
    def get_historial(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idAsistencias AS id_turno,
                    tipo,
                    DATE_FORMAT(fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora,
                    idUsuario
                FROM ASISTENCIAS
                WHERE idUsuario = %s
                ORDER BY fecha_hora_dispositivo DESC
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 5. MARCAR ASISTENCIA (INGRESO / SALIDA) ──────────────────────────────
    def marcar_asistencia(self, id_usuario, tipo, latitud, longitud, fecha_hora_disp, observacion=None):
        cursor = self.connection.cursor()
        try:
            dt_disp = self._parse_datetime(fecha_hora_disp)
            estado = 'A_TIEMPO'
            minutos_tardanza = 0

            if tipo.upper() == 'INGRESO':
                cursor.execute("""
                    SELECT clave, valor
                    FROM CONFIGURACION
                    WHERE clave IN (
                        'HORA_ENTRADA_OFICIAL',
                        'TOLERANCIA_MINUTOS',
                        'HORA_LIMITE_FALTA'
                    )
                """)
                # Soporta tanto cursores de tupla como de diccionario
                filas = cursor.fetchall()
                configuracion = {}
                for f in filas:
                    if isinstance(f, dict):
                        configuracion[f["clave"]] = f["valor"]
                    else:
                        configuracion[f[0]] = f[1]

                hora_entrada = datetime.strptime(
                    configuracion.get("HORA_ENTRADA_OFICIAL", "09:30:00"),
                    "%H:%M:%S"
                ).time()
                tolerancia_minutos = int(
                    configuracion.get("TOLERANCIA_MINUTOS", "10")
                )
                hora_limite_falta = datetime.strptime(
                    configuracion.get("HORA_LIMITE_FALTA", "10:30:00"),
                    "%H:%M:%S"
                ).time()

                hora_marcado = dt_disp.time()
                hora_inicio_dt = datetime.combine(dt_disp.date(), hora_entrada)
                hora_tolerancia = (
                    hora_inicio_dt + timedelta(minutes=tolerancia_minutos)
                ).time()

                if hora_marcado > hora_limite_falta:
                    estado = 'FALTA'
                elif hora_marcado > hora_tolerancia:
                    estado = 'TARDANZA'
                    hora_marcado_dt = datetime.combine(dt_disp.date(), hora_marcado)
                    minutos_tardanza = int(
                        (hora_marcado_dt - hora_inicio_dt).total_seconds() // 60
                    )

            sql = """
                INSERT INTO ASISTENCIAS (
                    tipo, 
                    fecha_hora_dispositivo, 
                    estado, 
                    minutos_tardanza, 
                    latitud, 
                    longitud, 
                    observacion,
                    idUsuario
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                tipo.upper(),
                dt_disp.strftime('%Y-%m-%d %H:%M:%S'),
                estado,
                minutos_tardanza,
                latitud,
                longitud,
                observacion,
                id_usuario
            ))
            self.connection.commit()
            
            return {
                "idAsistencias": cursor.lastrowid,
                "tipo": tipo.upper(),
                "estado": estado,
                "minutosTardanza": minutos_tardanza,
                "fechaHora": dt_disp.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    # ── 6. REGISTRAR JUSTIFICACIÓN ───────────────────────────────────────────
    def registrar_justificacion(self, id_usuario, motivo, descripcion, fecha):
        cursor = self.connection.cursor()
        try:
            # 1. Buscar si ya existe una asistencia para esa fecha
            sql_buscar = """
                SELECT idAsistencias 
                FROM ASISTENCIAS 
                WHERE idUsuario = %s AND DATE(fecha_hora_dispositivo) = %s
                ORDER BY idAsistencias DESC LIMIT 1
            """
            cursor.execute(sql_buscar, (id_usuario, fecha))
            asistencia = cursor.fetchone()

            # 2. Si no marcó asistencia, se crea el registro previo de FALTA (cumpliendo FK idAsistencias NOT NULL)
            if not asistencia:
                sql_crear_asistencia = """
                    INSERT INTO ASISTENCIAS (
                        tipo, fecha_hora_dispositivo, estado, minutos_tardanza, 
                        marcacion_observada, observacion, idUsuario
                    ) VALUES (
                        'INGRESO', CONCAT(%s, ' 09:00:00'), 'FALTA', 0, 
                        1, 'Inasistencia con justificación', %s
                    )
                """
                cursor.execute(sql_crear_asistencia, (fecha, id_usuario))
                id_asistencia = cursor.lastrowid
            else:
                id_asistencia = asistencia.get("idAsistencias") if isinstance(asistencia, dict) else asistencia[0]

            # 3. Insertar o actualizar justificación (evitando duplicado en UNIQUE idAsistencias)
            sql_check_just = "SELECT idJustificacion FROM JUSTIFICACIONES WHERE idAsistencias = %s"
            cursor.execute(sql_check_just, (id_asistencia,))
            existe_just = cursor.fetchone()

            if existe_just:
                sql_upsert = """
                    UPDATE JUSTIFICACIONES 
                    SET motivo = %s, descripcion = %s, estado = 'PENDIENTE', fecha_registro = CURRENT_TIMESTAMP
                    WHERE idAsistencias = %s
                """
                cursor.execute(sql_upsert, (motivo, descripcion, id_asistencia))
            else:
                sql_upsert = """
                    INSERT INTO JUSTIFICACIONES (motivo, descripcion, estado, idAsistencias, idUsuario)
                    VALUES (%s, %s, 'PENDIENTE', %s, %s)
                """
                cursor.execute(sql_upsert, (motivo, descripcion, id_asistencia, id_usuario))

            self.connection.commit()
            return {"idAsistencias": id_asistencia, "idUsuario": id_usuario, "estado": "ENVIADA"}
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    # ── 7. OBTENER ÚLTIMA JUSTIFICACIÓN DE UN USUARIO ────────────────────────
    def get_justificacion_usuario(self, id_usuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    j.idJustificacion,
                    j.motivo,
                    j.motivo AS motivoJustificacion,
                    j.descripcion,
                    j.descripcion AS justificacion,
                    j.estado,
                    j.estado AS estadoJustificacion,
                    DATE_FORMAT(j.fecha_registro, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_registro,
                    DATE_FORMAT(j.fecha_registro, '%%Y-%%m-%%d %%H:%%i:%%s') AS fechaJustificacion,
                    j.idAsistencias,
                    j.idUsuario
                FROM JUSTIFICACIONES j
                WHERE j.idUsuario = %s
                ORDER BY j.fecha_registro DESC
                LIMIT 1
            """
            cursor.execute(sql, (id_usuario,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def _parse_datetime(self, valor_str):
        if not valor_str:
            return datetime.now()
        for formato in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(str(valor_str).strip(), formato)
            except ValueError:
                pass
        return datetime.now()


    # ── 8. OBTENER ÚLTIMA ASISTENCIA DEL USUARIO ─────────────────────────────
    def obtener_ultima_asistencia(self, id_usuario):
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
                SELECT 
                    idAsistencias AS id,
                    DATE_FORMAT(fecha_hora_servidor, '%Y-%m-%d') AS fecha,
                    DATE_FORMAT(fecha_hora_servidor, '%H:%i:%s') AS hora,
                    latitud,
                    longitud,
                    observacion AS direccion
                FROM ASISTENCIAS
                WHERE idUsuario = %s
                ORDER BY idAsistencias DESC
                LIMIT 1
            """
            cursor.execute(query, (id_usuario,))
            resultado = cursor.fetchone()
            
            # Convertir Decimal de MySQL a float para evitar error de serialización JSON
            if resultado:
                if resultado.get('latitud') is not None:
                    resultado['latitud'] = float(resultado['latitud'])
                if resultado.get('longitud') is not None:
                    resultado['longitud'] = float(resultado['longitud'])
            
            return resultado
        finally:
            cursor.close()

    # ── 9. REVISAR (APROBAR/RECHAZAR) JUSTIFICACIÓN COMO ADMINISTRADOR ───────
    def revisar_justificacion(self, id_usuario_colaborador, estado_nuevo, comentario_admin, id_revisor):
        cursor = self.connection.cursor()
        try:
            # Mapeo de estados ('APROBADA', 'RECHAZADA')
            estado_enum = 'APROBADA' if estado_nuevo.upper() in ['APROBADA', 'APROBADO'] else 'RECHAZADA'
            
            query = """
                UPDATE JUSTIFICACIONES
                SET 
                    estado = %s,
                    comentario_revision = %s,
                    fecha_revision = NOW(),
                    idRevisor = %s
                WHERE idUsuario = %s AND estado = 'PENDIENTE'
                ORDER BY idJustificacion DESC
                LIMIT 1
            """
            cursor.execute(query, (estado_enum, comentario_admin, id_revisor, id_usuario_colaborador))
            filas_afectadas = cursor.rowcount
            self.connection.commit()
            return filas_afectadas > 0
        finally:
            cursor.close()