from datetime import datetime

class AsistenciaRepository:
    def __init__(self, connection):
        self.connection = connection

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

    

    def get_recientes(self, limite):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    a.idAsistencias,
                    a.id_turno,
                    a.tipo,
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.url_foto,
                    s.sede,
                    a.estado,
                    DATE_FORMAT(a.fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_dispositivo,
                    DATE_FORMAT(a.fecha_hora_servidor, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_servidor,
                    a.minutos_tardanza
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

    def get_colaboradores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.url_foto,
                    s.sede,
                    COALESCE(a.estado, 'SIN_REGISTRO') AS estado,
                    DATE_FORMAT(a.fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_dispositivo
                FROM USUARIOS u
                INNER JOIN SEDES s ON u.idSede = s.idSede
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE() 
                    AND a.tipo = 'INGRESO'
                WHERE u.estado = 'ACTIVO' AND u.rol != 'ADMINISTRADOR'
                ORDER BY a.fecha_hora_servidor DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_historial(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    id_turno,
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

    def marcar_asistencia(self, id_usuario, tipo, fecha_hora_dispositivo=None, latitud=None, longitud=None):
            cursor = self.connection.cursor()
            try:
                if not fecha_hora_dispositivo:
                    fecha_hora_dispositivo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Cálculo de tardanza si es INGRESO (Horario estándar 09:00 AM, tolerancia 09:15 AM)
                estado = "A_TIEMPO"
                minutos_tardanza = 0
                if tipo == "INGRESO":
                    try:
                        dt = datetime.strptime(fecha_hora_dispositivo, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        dt = datetime.now()
                    hora_limite = dt.replace(hour=9, minute=15, second=0, microsecond=0)
                    hora_inicio = dt.replace(hour=9, minute=0, second=0, microsecond=0)
                    if dt > hora_limite:
                        estado = "TARDANZA"
                        minutos_tardanza = int((dt - hora_inicio).total_seconds() // 60)
                    else:
                        estado = "A_TIEMPO"
                        minutos_tardanza = 0
                # Detección dinámica de columnas existentes en ASISTENCIAS para evitar errores
                cursor.execute("DESCRIBE ASISTENCIAS")
                filas = cursor.fetchall()
                columnas = [f["Field"] if isinstance(f, dict) else f[0] for f in filas]
                campos = ["idUsuario", "tipo", "fecha_hora_servidor"]
                valores = [id_usuario, tipo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                placeholders = ["%s", "%s", "%s"]
                if "fecha_hora_dispositivo" in columnas:
                    campos.append("fecha_hora_dispositivo")
                    valores.append(fecha_hora_dispositivo)
                    placeholders.append("%s")
                if "estado" in columnas:
                    campos.append("estado")
                    valores.append(estado)
                    placeholders.append("%s")
                if "minutos_tardanza" in columnas:
                    campos.append("minutos_tardanza")
                    valores.append(minutos_tardanza)
                    placeholders.append("%s")
                if "id_turno" in columnas:
                    campos.append("id_turno")
                    valores.append(1)
                    placeholders.append("%s")
                if "latitud" in columnas and latitud is not None:
                    campos.append("latitud")
                    valores.append(latitud)
                    placeholders.append("%s")
                if "longitud" in columnas and longitud is not None:
                    campos.append("longitud")
                    valores.append(longitud)
                    placeholders.append("%s")
                sql = f"""
                    INSERT INTO ASISTENCIAS ({", ".join(campos)})
                    VALUES ({", ".join(placeholders)})
                """
                cursor.execute(sql, tuple(valores))
                self.connection.commit()
                nuevo_id = cursor.lastrowid
                return {
                    "idAsistencias": nuevo_id,
                    "idUsuario": id_usuario,
                    "tipo": tipo,
                    "estado": estado,
                    "minutosTardanza": minutos_tardanza,
                    "fechaHora": fecha_hora_dispositivo
                }
            except Exception as e:
                self.connection.rollback()
                raise e
            finally:
                cursor.close()

    def registrar_justificacion(self, id_usuario, motivo, descripcion, fecha=None):
            cursor = self.connection.cursor()
            try:
                # Crea la tabla automáticamente si aún no existe en la base de datos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS JUSTIFICACIONES (
                        idJustificacion INT AUTO_INCREMENT PRIMARY KEY,
                        idUsuario INT NOT NULL,
                        motivo VARCHAR(150) NOT NULL,
                        descripcion TEXT NOT NULL,
                        fecha DATE NOT NULL,
                        estado VARCHAR(50) DEFAULT 'ENVIADA',
                        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                if not fecha:
                    fecha = datetime.now().strftime("%Y-%m-%d")
                sql = """
                    INSERT INTO JUSTIFICACIONES (idUsuario, motivo, descripcion, fecha, estado, fecha_creacion)
                    VALUES (%s, %s, %s, %s, 'ENVIADA', NOW())
                """
                cursor.execute(sql, (id_usuario, motivo, descripcion, fecha))
                self.connection.commit()
                return {
                    "idJustificacion": cursor.lastrowid,
                    "idUsuario": id_usuario,
                    "motivo": motivo,
                    "descripcion": descripcion,
                    "fecha": str(fecha),
                    "estado": "ENVIADA"
                }
            except Exception as e:
                self.connection.rollback()
                raise e
            finally:
                cursor.close()

    def get_justificacion_usuario(self, id_usuario):
            cursor = self.connection.cursor()
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS JUSTIFICACIONES (
                        idJustificacion INT AUTO_INCREMENT PRIMARY KEY,
                        idUsuario INT NOT NULL,
                        motivo VARCHAR(150) NOT NULL,
                        descripcion TEXT NOT NULL,
                        fecha DATE NOT NULL,
                        estado VARCHAR(50) DEFAULT 'ENVIADA',
                        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                sql = """
                    SELECT 
                        idJustificacion,
                        idUsuario,
                        motivo AS motivoJustificacion,
                        descripcion AS justificacion,
                        DATE_FORMAT(fecha, '%Y-%m-%d') AS fechaJustificacion,
                        estado AS estadoJustificacion
                    FROM JUSTIFICACIONES
                    WHERE idUsuario = %s
                    ORDER BY idJustificacion DESC
                    LIMIT 1
                """
                cursor.execute(sql, (id_usuario,))
                return cursor.fetchone()
            finally:
                cursor.close()

                
