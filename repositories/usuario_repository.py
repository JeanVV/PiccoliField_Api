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
                    foto_perfil,
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
                    u.foto_perfil,
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

    def listar_todos(self, rol=None, estado=None):
        cursor = self.connection.cursor()
        try:
            conditions = []
            params = []

            if rol:
                conditions.append("u.rol = %s")
                params.append(rol)
            if estado:
                conditions.append("u.estado = %s")
                params.append(estado)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            sql = f"""
                SELECT
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.correo,
                    u.rol,
                    u.estado,
                    s.sede
                FROM USUARIOS u
                INNER JOIN SEDES s ON u.idSede = s.idSede
                {where}
                ORDER BY u.apePaterno, u.nombres
            """
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
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

    def cambiar_estado(self, idUsuario, estado):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE USUARIOS
                SET estado = %s
                WHERE idUsuario = %s
            """
            cursor.execute(sql, (estado, idUsuario))
            self.connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()

    def actualizar_foto_perfil(self, idUsuario, nombre_archivo):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE USUARIOS
                SET foto_perfil = %s
                WHERE idUsuario = %s
            """
            cursor.execute(sql, (nombre_archivo, idUsuario))
            self.connection.commit()
            return cursor.rowcount
        finally:
            cursor.close()

    def obtener_foto_por_usuario(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT idUsuario, foto_perfil, estado
                FROM USUARIOS
                WHERE idUsuario = %s
                LIMIT 1
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
        finally:
            cursor.close()
