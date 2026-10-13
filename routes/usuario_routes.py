from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.usuario_service import UsuarioService
from utils.response import success_response, error_response

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/api/perfil", methods=["GET"])
@jwt_required()
def obtener_perfil():
    idUsuario = get_jwt_identity()

    service = UsuarioService()
    data, message, http_code = service.obtener_perfil(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@usuario_bp.route("/api/perfil/foto", methods=["GET"])
@jwt_required()
def obtener_foto_perfil():
    idUsuario = get_jwt_identity()

    service = UsuarioService()
    ruta_archivo, mimetype, message, http_code = service.obtener_foto_perfil(idUsuario)

    if ruta_archivo is None:
        return error_response(message, http_code)

    return send_file(ruta_archivo, mimetype=mimetype, as_attachment=False, conditional=True)


@usuario_bp.route("/api/perfil/fcm-token", methods=["PUT"])
@jwt_required()
def actualizar_fcm_token():
    idUsuario = get_jwt_identity()
    datos = request.get_json(silent=True)

    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    fcm_token = str(datos.get("fcm_token", "")).strip()
    id_dispositivo = str(datos.get("id_dispositivo", "")).strip()

    if not fcm_token or not id_dispositivo:
        return error_response("fcm_token e id_dispositivo son obligatorios", 400)

    service = UsuarioService()
    data, message, http_code = service.actualizar_fcm_token(idUsuario, fcm_token, id_dispositivo)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@usuario_bp.route("/api/usuarios", methods=["GET"])
@jwt_required()
def listar_usuarios():
    rol = request.args.get("rol")
    estado = request.args.get("estado")

    service = UsuarioService()
    data, message, http_code = service.listar_usuarios(rol=rol, estado=estado)

    return success_response(data, message, http_code)


@usuario_bp.route("/api/usuarios/<int:idUsuario>/estado", methods=["PATCH"])
@jwt_required()
def cambiar_estado_usuario(idUsuario):
    datos = request.get_json(silent=True)

    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    estado = str(datos.get("estado", "")).strip().upper()

    if not estado:
        return error_response("El campo estado es obligatorio", 400)

    service = UsuarioService()
    data, message, http_code = service.cambiar_estado(idUsuario, estado)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)
