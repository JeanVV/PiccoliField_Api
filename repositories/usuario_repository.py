class UsuarioRepository:
    def __init__(self, connection):
        self.connection = connection

    def buscar_por_correo(self, correo):
        cursor = self.connection.cursor()

        try:
            sql = """
                SELECT
                    id,
                    correo,
                    password_hash,
                    usuario,
                    rol,
                    estado
                FROM usuarios
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
                    id,
                    correo,
                    usuario,
                    rol,
                    estado
                FROM usuarios
                WHERE id = %s
                LIMIT 1
            """

            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
        finally:
            cursor.close()
