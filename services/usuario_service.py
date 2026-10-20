import hashlib
import mimetypes
import os

from config import Config
from database import get_connection
from repositories.usuario_repository import UsuarioRepository


class UsuarioService:

    # ── GET /api/perfil ─────────────────────────────────────────────────────
    def obtener_perfil(self, idUsuario):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_id(idUsuario)

            if usuario is None:
                return None, "Usuario no encontrado", 404
            if usuario["estado"] != "ACTIVO":
                return None, "El usuario se encuentra inactivo", 403

            data = {
                "idUsuario": usuario["idUsuario"],
                "nombres": usuario["nombres"],
                "apePaterno": usuario["apePaterno"],
                "apeMaterno": usuario["apeMaterno"],
                "correo": usuario["correo"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
                "sede": usuario["sede"],
                "distrito": usuario["distrito"]
            }

            return data, "Perfil obtenido correctamente", 200
        finally:
            connection.close()

    # ── PUT /api/perfil/fcm-token ────────────────────────────────────────────
    def actualizar_fcm_token(self, idUsuario, fcm_token, id_dispositivo):
        if not fcm_token or not id_dispositivo:
            return None, "fcm_token e id_dispositivo son requeridos", 400

        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            rows = repository.actualizar_fcm_token(idUsuario, fcm_token, id_dispositivo)

            if rows == 0:
                return None, "Usuario no encontrado", 404

            return {"idUsuario": idUsuario}, "Token FCM actualizado correctamente", 200
        finally:
            connection.close()
