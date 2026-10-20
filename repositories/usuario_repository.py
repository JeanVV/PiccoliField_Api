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

    def actualizar_fcm_token(self, idUsuario, fcm_token, id_dispositivo):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE USUARIOS
                SET fcm_token = %s, id_dispositivo = %s
                WHERE idUsuario = %s
            """
            cursor.execute(sql, (fcm_token, id_dispositivo, idUsuario))
            self.connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()
