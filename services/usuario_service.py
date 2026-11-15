import base64
import hashlib
import mimetypes
import os

from config import Config, BASE_DIR
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
                "url_foto": usuario.get("url_foto"),
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

    # ── ACTUALIZAR FOTO DE PERFIL / USUARIO ─────────────────────────────────
    def actualizar_foto_usuario(self, id_usuario, raw_foto=None, archivo_foto=None):
        if not raw_foto and not archivo_foto:
            return None, "No se envió ninguna imagen (url_foto o archivo 'foto' vacío)", 400

        # Asegurar directorio físico de perfiles
        os.makedirs(Config.PROFILE_PHOTO_DIR, exist_ok=True)
        rel_path = f"uploads/perfiles/user_{id_usuario}.jpg"
        abs_path = os.path.join(BASE_DIR, rel_path)

        valor_bd = None

        # 1. Si viene como multipart/form-data
        if archivo_foto:
            try:
                archivo_foto.save(abs_path)
                valor_bd = rel_path
            except Exception as e:
                print(f"[WARN] No se pudo guardar archivo multipart: {e}")

        # 2. Si viene como Base64 (data:image/...) o URL
        if not valor_bd and raw_foto:
            valor_bd = raw_foto.strip()
            if valor_bd.startswith("data:image"):
                try:
                    header, b64data = valor_bd.split(",", 1)
                    img_bytes = base64.b64decode(b64data)
                    with open(abs_path, "wb") as f:
                        f.write(img_bytes)
                except Exception as e:
                    print(f"[WARN] No se pudo escribir archivo físico desde base64: {e}")

        if not valor_bd:
            return None, "No se pudo procesar la imagen enviada", 400

        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            nuevo_valor = repository.actualizar_foto(id_usuario, valor_bd)
            return {
                "idUsuario": int(id_usuario),
                "url_foto": nuevo_valor
            }, "Foto de perfil actualizada correctamente", 200
        except Exception as e:
            print(f"Error al actualizar foto de usuario {id_usuario}: {e}")
            return None, f"Error al actualizar la foto: {str(e)}", 500
        finally:
            connection.close()

    # ── OBTENER FOTO DE PERFIL ──────────────────────────────────────────────
    def obtener_foto_perfil(self, id_usuario):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_id(id_usuario)
            if not usuario:
                return None, None, "Usuario no encontrado", 404

            foto = usuario.get("url_foto")

            # 1. Archivo físico estándar user_<id>.jpg
            rel_path = f"uploads/perfiles/user_{id_usuario}.jpg"
            abs_path = os.path.join(BASE_DIR, rel_path)
            if os.path.isfile(abs_path):
                mimetype, _ = mimetypes.guess_type(abs_path)
                return abs_path, mimetype or "image/jpeg", "Foto encontrada", 200

            # 2. Archivo en la ruta especificada en BD
            if foto and not foto.startswith("data:image"):
                ruta_directa = os.path.join(BASE_DIR, foto)
                if os.path.isfile(ruta_directa):
                    mimetype, _ = mimetypes.guess_type(ruta_directa)
                    return ruta_directa, mimetype or "image/jpeg", "Foto encontrada", 200

            # 3. Fallback a default.png
            default_foto = os.path.join(Config.PROFILE_PHOTO_DIR, "default.png")
            if os.path.isfile(default_foto):
                return default_foto, "image/png", "Foto por defecto", 200

            return None, None, "No se encontró foto de perfil", 404
        finally:
            connection.close()
