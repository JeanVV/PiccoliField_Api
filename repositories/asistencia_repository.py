from datetime import datetime, timedelta

class AsistenciaRepository:
    def __init__(self, connection):
        self.connection = connection

    # ── 1. RESUMEN DEL DÍA ───────────────────────────────────────────────────
    def get_resumen(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    COUNT(u.idUsuario) AS total,
                    COALESCE(SUM(CASE WHEN a.estado IN ('A_TIEMPO', 'TARDANZA') THEN 1 ELSE 0 END), 0) AS presentes,
                    COALESCE(SUM(CASE WHEN a.estado = 'A_TIEMPO' THEN 1 ELSE 0 END), 0) AS aTiempo,
                    COALESCE(SUM(CASE WHEN a.estado = 'TARDANZA' THEN 1 ELSE 0 END), 0) AS tardanzas,
                    COALESCE(SUM(CASE WHEN a.estado = 'FALTA' THEN 1 ELSE 0 END), 0) AS faltas,
                    COALESCE(SUM(CASE WHEN a.idAsistencias IS NULL THEN 1 ELSE 0 END), 0) AS sinMarcar
                FROM USUARIOS u
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE()
                    AND a.tipo = 'INGRESO'
                WHERE u.estado = 'ACTIVO' AND u.rol NOT IN ('ADMINISTRADOR', 'SUPERVISOR')
            """
            cursor.execute(sql)
            resumen = cursor.fetchone() or {}
            total = resumen.get('total', 0)
            presentes = resumen.get('presentes', 0)
            resumen['porcentaje'] = int((presentes / total * 100)) if total > 0 else 0
            return resumen
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
                # Verificar si ya existe una marca de INGRESO hoy para este idUsuario
                cursor.execute("""
                    SELECT idAsistencias, DATE_FORMAT(fecha_hora_dispositivo, '%H:%i:%s') AS hora, estado
                    FROM ASISTENCIAS
                    WHERE idUsuario = %s AND tipo = 'INGRESO' AND DATE(fecha_hora_servidor) = CURDATE()
                    LIMIT 1
                """, (id_usuario,))
                ingreso_existente = cursor.fetchone()

                if ingreso_existente:
                    hora_existente = ingreso_existente.get("hora", "") if isinstance(ingreso_existente, dict) else ingreso_existente[1]
                    estado_existente = ingreso_existente.get("estado", "A_TIEMPO") if isinstance(ingreso_existente, dict) else ingreso_existente[2]
                    id_existente = ingreso_existente.get("idAsistencias") if isinstance(ingreso_existente, dict) else ingreso_existente[0]
                    return {
                        "idAsistencias": id_existente,
                        "tipo": "INGRESO",
                        "estado": estado_existente,
                        "minutosTardanza": 0,
                        "yaRegistrado": True,
                        "message": f"Ya has registrado tu ingreso hoy a las {hora_existente}"
                    }

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
    def registrar_justificacion(self, id_usuario, motivo, descripcion, fecha, ruta_sustento=None):
        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()
        try:
            # 1. Verificar si ya existe una asistencia para esa fecha
            sql_check = """
                SELECT idAsistencias FROM ASISTENCIAS 
                WHERE idUsuario = %s AND (DATE(fecha_hora_servidor) = %s OR DATE(fecha_hora_dispositivo) = %s)
                ORDER BY idAsistencias DESC LIMIT 1
            """
            cursor.execute(sql_check, (id_usuario, fecha, fecha))
            asistencia = cursor.fetchone()

            if asistencia:
                id_asistencia = asistencia['idAsistencias'] if isinstance(asistencia, dict) else asistencia[0]
            else:
                # Si no existe asistencia previa, se crea el registro de FALTA
                sql_insert_asistencia = """
                    INSERT INTO ASISTENCIAS (
                        idUsuario, tipo, estado, fecha_hora_servidor, fecha_hora_dispositivo, observacion
                    ) VALUES (
                        %s, 'INGRESO', 'FALTA', NOW(), CONCAT(%s, ' 09:00:00'), 'Inasistencia con justificación'
                    )
                """
                cursor.execute(sql_insert_asistencia, (id_usuario, fecha))
                id_asistencia = cursor.lastrowid

            # 2. Insertar o actualizar fila en la tabla JUSTIFICACIONES (idAsistencias es UNIQUE)
            sql_justificacion = """
                INSERT INTO JUSTIFICACIONES (
                    idAsistencias, idUsuario, motivo, descripcion, estado, ruta_sustento, fecha_registro
                )
                VALUES (%s, %s, %s, %s, 'PENDIENTE', %s, NOW())
                ON DUPLICATE KEY UPDATE
                    motivo = VALUES(motivo),
                    descripcion = VALUES(descripcion),
                    ruta_sustento = VALUES(ruta_sustento),
                    estado = 'PENDIENTE',
                    fecha_registro = NOW()
            """
            cursor.execute(sql_justificacion, (id_asistencia, id_usuario, motivo, descripcion, ruta_sustento))
            self.connection.commit()

            id_justificacion = cursor.lastrowid
            if not id_justificacion:
                cursor.execute(
                    "SELECT idJustificacion FROM JUSTIFICACIONES WHERE idAsistencias = %s LIMIT 1",
                    (id_asistencia,)
                )
                row_j = cursor.fetchone()
                id_justificacion = row_j["idJustificacion"] if isinstance(row_j, dict) else row_j[0]

            return {
                "idJustificacion": id_justificacion,
                "idAsistencias": id_asistencia,
                "idUsuario": id_usuario,
                "estado": "PENDIENTE"
            }
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
        cursor = self.connection.cursor()
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
    def revisar_justificacion(self, id_usuario=None, id_revisor=1, estado="APROBADA", comentario="", id_asistencias=None, **kwargs):
        id_user = id_usuario if id_usuario is not None else kwargs.get("id_usuario_colaborador")
        id_asist = id_asistencias if id_asistencias is not None else kwargs.get("idAsistencias")
        est = estado if estado is not None else kwargs.get("estado_nuevo", "APROBADA")
        com = comentario if comentario is not None else kwargs.get("comentario_admin", "")
        rev = id_revisor if id_revisor is not None else kwargs.get("id_revisor", 1)

        estado_enum = "APROBADA" if str(est).upper() in ["APROBADA", "APROBADO"] else "RECHAZADA"

        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()
        try:
            # 1. Ubicar la justificación a actualizar por idAsistencias o idUsuario
            sql_get = """
                SELECT j.idJustificacion, j.idAsistencias
                FROM JUSTIFICACIONES j
                WHERE (%s IS NOT NULL AND j.idAsistencias = %s)
                   OR (%s IS NOT NULL AND j.idUsuario = %s)
                ORDER BY j.idJustificacion DESC LIMIT 1
            """
            cursor.execute(sql_get, (id_asist, id_asist, id_user, id_user))
            row = cursor.fetchone()

            if not row:
                return False

            id_justificacion = row["idJustificacion"] if isinstance(row, dict) else row[0]
            id_asistencia = row["idAsistencias"] if isinstance(row, dict) else row[1]

            # 2. Actualizar estado de la JUSTIFICACIÓN
            sql_update_j = """
                UPDATE JUSTIFICACIONES
                SET estado = %s, comentario_revision = %s, idRevisor = %s, fecha_revision = NOW()
                WHERE idJustificacion = %s
            """
            cursor.execute(sql_update_j, (estado_enum, com, rev, id_justificacion))

            # 3. Si fue APROBADA, actualizar el estado de la ASISTENCIA a 'A_TIEMPO'
            if estado_enum == "APROBADA":
                cursor.execute("""
                    UPDATE ASISTENCIAS
                    SET estado = 'A_TIEMPO', observacion = CONCAT('Justificación Aprobada: ', COALESCE(%s, ''))
                    WHERE idAsistencias = %s
                """, (com, id_asistencia))

            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    # ── 10. CONSULTA RESUMEN DE ASISTENCIAS DEL DÍA (10:30 AM) ───────────────
    def get_resumen_diario(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    COUNT(u.idUsuario) AS total,
                    COALESCE(SUM(CASE WHEN a.estado IN ('A_TIEMPO', 'TARDANZA') THEN 1 ELSE 0 END), 0) AS presentes,
                    COALESCE(SUM(CASE WHEN a.estado = 'A_TIEMPO' THEN 1 ELSE 0 END), 0) AS aTiempo,
                    COALESCE(SUM(CASE WHEN a.estado = 'TARDANZA' THEN 1 ELSE 0 END), 0) AS tardanzas,
                    COALESCE(SUM(CASE WHEN a.estado = 'FALTA' OR a.idAsistencias IS NULL THEN 1 ELSE 0 END), 0) AS faltas
                FROM USUARIOS u
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE()
                    AND a.tipo = 'INGRESO'
                WHERE u.estado = 'ACTIVO' AND u.rol NOT IN ('ADMINISTRADOR', 'SUPERVISOR');
            """
            cursor.execute(sql)
            return cursor.fetchone()
        finally:
            cursor.close()

    # ── 11. TOKENS FCM DE ADMINISTRADORES Y SUPERVISORES ─────────────────────
    def get_tokens_administradores_supervisores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT DISTINCT 
                    ud.fcm_token,
                    ud.idUsuario,
                    u.rol,
                    u.nombres,
                    u.apePaterno
                FROM USUARIO_DISPOSITIVO ud
                INNER JOIN USUARIOS u ON ud.idUsuario = u.idUsuario
                WHERE u.rol IN ('ADMINISTRADOR', 'SUPERVISOR')
                  AND ud.activo = 1
                  AND ud.fcm_token IS NOT NULL 
                  AND ud.fcm_token != ''
                  AND u.estado = 'ACTIVO';
            """
            cursor.execute(sql)
            return cursor.fetchall() or []
        finally:
            cursor.close()
