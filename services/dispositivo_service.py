from database import get_connection
from repositories.dispositivo_repository import DispositivoRepository
from repositories.usuario_repository import UsuarioRepository


class DispositivoService:

    def actualizar(self, idUsuario, datos):
        fcm_token = str(datos.get("fcm_token", "")).strip()
        plataforma = str(
            datos.get("plataforma", "ANDROID")
        ).strip().upper()
        nombre_dispositivo = str(
            datos.get("nombre_dispositivo", "")
        ).strip()

        if not fcm_token:
            return None, "El token FCM es obligatorio", 400

        if plataforma not in ("ANDROID", "IOS"):
            return None, "La plataforma no es válida", 400

        connection = get_connection()

        try:
            usuario_repository = UsuarioRepository(connection)
            usuario = usuario_repository.buscar_por_id(idUsuario)

            if usuario is None:
                return None, "Usuario no encontrado", 404

            if usuario["estado"] != "ACTIVO":
                return None, "El usuario se encuentra inactivo", 403

            repository = DispositivoRepository(connection)

            repository.actualizar_dispositivo(
                idUsuario,
                fcm_token,
                plataforma,
                nombre_dispositivo or None
            )

            connection.commit()

            data = {
                "idUsuario": int(idUsuario),
                "fcm_token": fcm_token,
                "plataforma": plataforma,
                "nombre_dispositivo": (
                    nombre_dispositivo or None
                )
            }

            return (
                data,
                "Dispositivo actualizado correctamente",
                200
            )

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
