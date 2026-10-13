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

    # ── GET /api/usuarios ────────────────────────────────────────────────────
    def listar_usuarios(self, rol=None, estado=None):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuarios = repository.listar_todos(rol=rol, estado=estado)
            return usuarios, "Usuarios obtenidos correctamente", 200
        finally:
            connection.close()

    # ── GET /api/usuarios/<id> ───────────────────────────────────────────────
    def obtener_usuario(self, idUsuario):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_id(idUsuario)

            if usuario is None:
                return None, "Usuario no encontrado", 404

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
            return data, "Usuario obtenido correctamente", 200
        finally:
            connection.close()

    # ── PATCH /api/usuarios/<id>/estado ─────────────────────────────────────
    def cambiar_estado(self, idUsuario, estado):
        estados_validos = ("ACTIVO", "INACTIVO")
        if estado not in estados_validos:
            return None, f"Estado inválido. Use: {', '.join(estados_validos)}", 400

        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_id(idUsuario)

            if usuario is None:
                return None, "Usuario no encontrado", 404

            if usuario["estado"] == estado:
                return None, f"El usuario ya se encuentra {estado}", 400

            repository.cambiar_estado(idUsuario, estado)
            return {"idUsuario": idUsuario, "estado": estado}, "Estado actualizado correctamente", 200
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

    # ── GET /api/perfil/foto ─────────────────────────────────────────────────
    def obtener_foto_perfil(self, idUsuario):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.obtener_foto_por_usuario(idUsuario)

            if usuario is None:
                return None, None, "Usuario no encontrado", 404

            if usuario["estado"] != "ACTIVO":
                return None, None, "El usuario se encuentra inactivo", 403

            nombre_foto = usuario.get("foto_perfil") or "default.png"
            nombre_seguro = os.path.basename(nombre_foto)

            ruta_base = os.path.realpath(Config.PROFILE_PHOTO_DIR)
            ruta_archivo = os.path.realpath(os.path.join(ruta_base, nombre_seguro))

            if os.path.commonpath([ruta_base, ruta_archivo]) != ruta_base:
                return None, None, "Ruta de foto no válida", 400

            if not os.path.isfile(ruta_archivo):
                return None, None, "Archivo de foto no encontrado", 404

            mimetype, _ = mimetypes.guess_type(ruta_archivo)

            if mimetype is None or not mimetype.startswith("image/"):
                return None, None, "El archivo almacenado no es una imagen válida", 415

            return ruta_archivo, mimetype, "Foto de perfil obtenida correctamente", 200
        finally:
            connection.close()
