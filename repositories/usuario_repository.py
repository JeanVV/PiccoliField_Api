class UsuarioRepository:
    def __init__(self, connection):
        self.connection = connection

    def buscar_por_correo(self, correo):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                    idUsuario,
                    nombres,
                    apePaterno,
                    apeMaterno,
                    correo,
                    password_hash,
                    url_foto,
                    rol,
                    estado,
                    idDistrito,
                    idSede
                FROM USUARIOS
                WHERE correo = %s
                LIMIT 1
            """
            cursor.execute(sql, (correo,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def buscar_por_id(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.correo,
                    u.url_foto,
                    u.rol,
                    u.estado,
                    s.sede,
                    d.distrito
                FROM USUARIOS u
                INNER JOIN SEDES s ON u.idSede = s.idSede
                INNER JOIN DISTRITO d ON u.idDistrito = d.idDistrito
                WHERE u.idUsuario = %s
                LIMIT 1
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def actualizar_fcm_token(self, idUsuario, fcm_token, id_dispositivo=None):
        cursor = self.connection.cursor()
        try:
            # 1. Actualizar token principal en la tabla USUARIOS
            sql_usuario = """
                UPDATE USUARIOS
                SET fcm_token = %s
                WHERE idUsuario = %s
            """
            cursor.execute(sql_usuario, (fcm_token, idUsuario))
            filas_afectadas = cursor.rowcount

            # 2. Registrar o actualizar en la tabla USUARIO_DISPOSITIVO
            sql_disp = """
                INSERT INTO USUARIO_DISPOSITIVO (
                    idUsuario,
                    fcm_token,
                    plataforma,
                    nombre_dispositivo,
                    activo
                )
                VALUES (%s, %s, 'ANDROID', %s, 1)
                ON DUPLICATE KEY UPDATE
                    idUsuario = VALUES(idUsuario),
                    activo = 1,
                    nombre_dispositivo = COALESCE(VALUES(nombre_dispositivo), nombre_dispositivo),
                    fecha_actualizacion = CURRENT_TIMESTAMP
            """
            cursor.execute(sql_disp, (idUsuario, fcm_token, id_dispositivo or "Dispositivo Android"))
            self.connection.commit()
            return filas_afectadas
        finally:
            cursor.close()

    def listar_notificaciones(self, idUsuario, limite=20):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idNotificacion,
                    tipo,
                    referencia,
                    mensaje,
                    DATE_FORMAT(fecha, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha
                FROM NOTIFICACIONES_LOG
                WHERE idUsuario = %s
                ORDER BY fecha DESC, idNotificacion DESC
                LIMIT %s
            """
            cursor.execute(sql, (idUsuario, limite))
            return cursor.fetchall() or []
        finally:
            cursor.close()

    def actualizar_foto(self, id_usuario, url_foto):
        cursor = self.connection.cursor()
        try:
            try:
                cursor.execute(
                    "UPDATE USUARIOS SET url_foto = %s WHERE idUsuario = %s",
                    (url_foto, id_usuario)
                )
                self.connection.commit()
                return url_foto
            except Exception:
                self.connection.rollback()
                ruta_corta = f"uploads/perfiles/user_{id_usuario}.jpg"
                cursor.execute(
                    "UPDATE USUARIOS SET url_foto = %s WHERE idUsuario = %s",
                    (ruta_corta, id_usuario)
                )
                self.connection.commit()
                return ruta_corta
        finally:
            cursor.close()
