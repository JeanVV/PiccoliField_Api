class DispositivoRepository:

    def __init__(self, connection):
        self.connection = connection

    def actualizar_dispositivo(
        self,
        idUsuario,
        fcm_token,
        plataforma,
        nombre_dispositivo
    ):
        cursor = self.connection.cursor()

        try:
            sql = """
                INSERT INTO USUARIO_DISPOSITIVO (
                    idUsuario,
                    fcm_token,
                    plataforma,
                    nombre_dispositivo,
                    activo
                )
                VALUES (%s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    idUsuario = VALUES(idUsuario),
                    plataforma = VALUES(plataforma),
                    nombre_dispositivo = VALUES(nombre_dispositivo),
                    activo = 1,
                    fecha_actualizacion = CURRENT_TIMESTAMP
            """

            cursor.execute(sql, (
                idUsuario,
                fcm_token,
                plataforma,
                nombre_dispositivo
            ))

            return cursor.rowcount
        finally:
            cursor.close()
