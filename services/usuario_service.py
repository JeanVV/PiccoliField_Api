import base64
import hashlib
import mimetypes
import os
import shutil
import time

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
    def actualizar_fcm_token(self, idUsuario, fcm_token, id_dispositivo=None):
        if not fcm_token:
            return None, "El campo 'fcm_token' es requerido", 400

        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            repository.actualizar_fcm_token(idUsuario, fcm_token, id_dispositivo)
            return {
                "idUsuario": int(idUsuario),
                "fcm_token": fcm_token
            }, "Token FCM actualizado correctamente", 200
        except Exception as e:
            print(f"Error al actualizar FCM token: {e}")
            return None, f"Error interno: {str(e)}", 500
        finally:
            connection.close()

    # ── GET /api/notificaciones ──────────────────────────────────────────────
    MAPA_TIPOS_APP = {
        "ALERTA_STOCK": ("ALERTA", "⚠️ Alerta de Stock Bajo"),
        "INCIDENCIA_NUEVA": ("INCIDENCIA", "🚨 Nueva Incidencia"),
        "INCIDENCIA_RESUELTA": ("INCIDENCIA", "✅ Incidencia Resuelta"),
        "META_ALCANZADA": ("META", "🎉 ¡Meta Alcanzada!"),
        "REASIGNACION_LOCAL": ("REASIGNACION", "📍 Reasignación de Local"),
    }

    def listar_notificaciones(self, idUsuario, limite=20):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            filas = repository.listar_notificaciones(idUsuario, limite) or []
            notificaciones = []
            for f in filas:
                t_orig = f.get("tipo", "GENERAL")
                tipo_app, titulo_default = self.MAPA_TIPOS_APP.get(t_orig, ("GENERAL", "ℹ️ Notificación"))

                # Extraer ID numérico de referencia (ej: INC-35 -> "35", ALERTA-10 -> "10")
                ref = str(f.get("referencia") or "")
                content_id = ""
                if "-" in ref:
                    partes = ref.split("-", 1)
                    content_id = partes[1]
                elif ref.isdigit():
                    content_id = ref
                else:
                    content_id = str(f.get("idNotificacion"))

                notificaciones.append({
                    "idNotificacion": f["idNotificacion"],
                    "tipo": tipo_app,
                    "tipo_original": t_orig,
                    "id": content_id,
                    "titulo": titulo_default,
                    "mensaje": f.get("mensaje", ""),
                    "referencia": ref,
                    "fecha": f.get("fecha", "")
                })

            return {
                "total": len(notificaciones),
                "notificaciones": notificaciones
            }, "Historial de notificaciones obtenido exitosamente", 200
        except Exception as e:
            print(f"Error en listar_notificaciones: {e}")
            return None, f"Error interno: {str(e)}", 500
        finally:
            connection.close()

    # ── ACTUALIZAR FOTO DE PERFIL / USUARIO (CAMINO 1: ARCHIVO FÍSICO) ─────
    def actualizar_foto_usuario(self, id_usuario, raw_foto=None, archivo_foto=None):
        if not raw_foto and not archivo_foto:
            return None, "No se proporcionó ninguna imagen", 400

        # 1. Asegurar carpeta uploads/perfiles/
        os.makedirs(Config.PROFILE_PHOTO_DIR, exist_ok=True)

        # 2. Generar nombre de archivo único con timestamp
        ts = int(time.time())
        nombre_archivo = f"user_{id_usuario}_{ts}.jpg"
        rel_path = f"uploads/perfiles/{nombre_archivo}"
        abs_path = os.path.join(BASE_DIR, rel_path)

        guardado_exitoso = False

        # 3. Caso Multipart/form-data
        if archivo_foto:
            try:
                archivo_foto.save(abs_path)
                guardado_exitoso = True
            except Exception as e:
                print(f"[WARN] No se pudo guardar archivo multipart: {e}")

        # 4. Caso Base64 (data:image/... o base64 puro)
        if not guardado_exitoso and raw_foto:
            raw_str = raw_foto.strip()
            # Si ya es una ruta relativa existente en el servidor
            if not raw_str.startswith("data:image") and "base64," not in raw_str and len(raw_str) < 255 and raw_str.startswith("uploads/"):
                rel_path = raw_str
                guardado_exitoso = True
            else:
                try:
                    if "base64," in raw_str:
                        _, encoded_data = raw_str.split("base64,", 1)
                    else:
                        encoded_data = raw_str

                    image_data = base64.b64decode(encoded_data)
                    with open(abs_path, "wb") as f:
                        f.write(image_data)
                    guardado_exitoso = True
                except Exception as e:
                    return None, f"Error al decodificar la imagen Base64: {str(e)}", 400

        if not guardado_exitoso or not os.path.isfile(abs_path):
            return None, "No se pudo procesar ni guardar físicamente la imagen", 400

        # 5. También guardar/actualizar user_<id>.jpg como fallback fijo
        try:
            ruta_estatica = os.path.join(Config.PROFILE_PHOTO_DIR, f"user_{id_usuario}.jpg")
            if abs_path != ruta_estatica:
                shutil.copyfile(abs_path, ruta_estatica)
        except Exception:
            pass

        # 6. Guardar en MySQL EXCLUSIVAMENTE la ruta relativa limpia (Camino 1)
        ruta_bd = rel_path.replace("\\", "/")

        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            nuevo_valor = repository.actualizar_foto(id_usuario, ruta_bd)
            return {
                "idUsuario": int(id_usuario),
                "url_foto": nuevo_valor
            }, "Foto guardada físicamente en el servidor", 200
        except Exception as e:
            print(f"Error al actualizar foto de usuario {id_usuario}: {e}")
            return None, f"Error interno al guardar la foto: {str(e)}", 500
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

            # 1. Archivo en la ruta guardada en BD
            if foto and not foto.startswith("data:image"):
                clean_foto = foto.replace("\\", "/").strip("/")
                ruta_bd = os.path.join(BASE_DIR, clean_foto)
                if os.path.isfile(ruta_bd):
                    mimetype, _ = mimetypes.guess_type(ruta_bd)
                    return ruta_bd, mimetype or "image/jpeg", "Foto encontrada", 200

            # 2. Archivo físico estándar user_<id>.jpg
            rel_path = f"uploads/perfiles/user_{id_usuario}.jpg"
            abs_path = os.path.join(BASE_DIR, rel_path)
            if os.path.isfile(abs_path):
                mimetype, _ = mimetypes.guess_type(abs_path)
                return abs_path, mimetype or "image/jpeg", "Foto encontrada", 200

            # 3. Fallback a default.png
            default_foto = os.path.join(Config.PROFILE_PHOTO_DIR, "default.png")
            if os.path.isfile(default_foto):
                return default_foto, "image/png", "Foto por defecto", 200

            return None, None, "No se encontró foto de perfil", 404
        finally:
            connection.close()
