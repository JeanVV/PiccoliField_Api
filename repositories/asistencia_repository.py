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
                    u.foto_perfil,
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
                    u.foto_perfil,
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

    def get_detalle_usuario(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.foto_perfil,
                    s.sede,
                    a.estado,
                    DATE_FORMAT(a.fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_dispositivo,
                    DATE_FORMAT(a.fecha_hora_servidor, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_servidor,
                    a.minutos_tardanza,
                    a.id_turno
                FROM USUARIOS u
                INNER JOIN SEDES s ON u.idSede = s.idSede
                INNER JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE()
                WHERE u.idUsuario = %s
                ORDER BY a.fecha_hora_servidor DESC
                LIMIT 1
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
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

    def get_evidencias(self, idAsistencia):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idEvidencias,
                    ruta_archivo,
                    hash_sha,
                    tipo,
                    DATE_FORMAT(fecha_captura, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_captura,
                    idStock,
                    INCIDENCIASidIncidencias AS idIncidencia
                FROM EVIDENCIAS
                WHERE idAsistencias = %s
            """
            cursor.execute(sql, (idAsistencia,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def marcarAsistenciaPersonal(self, idUsuario, tipo):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO ASISTENCIAS 
                    (id_turno, tipo, fecha_hora_dispositivo, fecha_hora_servidor, idUsuario)
                VALUES 
                    (%s, %s, NOW(), NOW(), %s)
            """
            cursor.execute(sql, (idUsuario, tipo, idUsuario))
            self.connection.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
    
    def verificarHorarioTurnoPersonal(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    t.horaEntrada,
                    t.horaSalida
                FROM USUARIOS u
                INNER JOIN TURNOS t ON u.idTurno = t.idTurno
                WHERE u.idUsuario = %s
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
        finally:
            cursor.close() 

    def asistenciaPersonal(self, idUsuario, tipo):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    a.fecha_hora_servidor as fecha,
                    a.fecha_hora_dispositivo as hora,
                    a.minutos_tardanza,
                    a.tipo,
                    a.idUsuario
                FROM USUARIOS u
                INNER JOIN TURNOS t ON u.idTurno = t.idTurno
                inner Join ASISTENCIAS a ON u.idUsuario = a.idUsuario
                WHERE u.idUsuario = %s
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
        finally:
            cursor.close() 
    
