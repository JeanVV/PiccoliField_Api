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
