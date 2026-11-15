from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.usuario_service import UsuarioService
from utils.response import success_response, error_response

usuario_bp = Blueprint("usuarios", __name__)


# ── 1. PERFIL DE USUARIO ─────────────────────────────────────────────────────
@usuario_bp.route("/api/perfil", methods=["GET"])
@jwt_required()
def obtener_perfil():
    idUsuario = get_jwt_identity()

    service = UsuarioService()
    data, message, http_code = service.obtener_perfil(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 2. ACTUALIZAR TOKEN FCM (DISPOSITIVO) ────────────────────────────────────
@usuario_bp.route("/api/perfil/fcm-token", methods=["PUT", "POST"])
@usuario_bp.route("/api/usuario/fcm-token", methods=["PUT", "POST"])
@jwt_required()
def actualizar_fcm_token():
    idUsuario = get_jwt_identity()
    datos = request.get_json(silent=True)

    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    fcm_token = str(datos.get("fcm_token", "")).strip()
    id_dispositivo = datos.get("id_dispositivo") or datos.get("nombre_dispositivo")

    if not fcm_token:
        return error_response("El campo 'fcm_token' es obligatorio", 400)

    service = UsuarioService()
    data, message, http_code = service.actualizar_fcm_token(idUsuario, fcm_token, id_dispositivo)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 3. HISTORIAL DE NOTIFICACIONES RECIBIDAS ─────────────────────────────────
@usuario_bp.route("/api/notificaciones", methods=["GET"])
@usuario_bp.route("/api/perfil/notificaciones", methods=["GET"])
@jwt_required()
def listar_notificaciones():
    idUsuario = get_jwt_identity()
    limite = request.args.get("limite", default=20, type=int)

    service = UsuarioService()
    data, message, http_code = service.listar_notificaciones(idUsuario=idUsuario, limite=limite)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)
