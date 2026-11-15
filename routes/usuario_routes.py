from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.usuario_service import UsuarioService
from utils.response import success_response, error_response

usuario_bp = Blueprint("usuarios", __name__)
service = UsuarioService()


# ── 1. OBTENER PERFIL DEL USUARIO AUTENTICADO ─────────────────────────────────
@usuario_bp.route("/api/perfil", methods=["GET"])
@jwt_required()
def obtener_perfil():
    idUsuario = get_jwt_identity()
    data, message, http_code = service.obtener_perfil(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 2. ACTUALIZAR TOKEN FCM Y DISPOSITIVO ─────────────────────────────────────
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

    data, message, http_code = service.actualizar_fcm_token(idUsuario, fcm_token, id_dispositivo)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 3. ACTUALIZAR FOTO DE UN USUARIO (PANEL WEB / ADMIN) ──────────────────────
@usuario_bp.route("/api/usuarios/<int:id_usuario>/foto", methods=["PUT", "POST"])
@jwt_required()
def actualizar_foto_usuario(id_usuario):
    try:
        data = request.get_json(silent=True) or {}
        url_foto = data.get("url_foto") or data.get("foto")
        archivo = request.files.get("foto")

        resultado, message, code = service.actualizar_foto_usuario(
            id_usuario=id_usuario,
            raw_foto=url_foto,
            archivo_foto=archivo
        )

        if resultado is None:
            return jsonify({"success": False, "status": False, "message": message}), code

        return jsonify({
            "success": True,
            "status": True,
            "message": message,
            "data": resultado
        }), code
    except Exception as e:
        return jsonify({"success": False, "status": False, "message": str(e)}), 400


# ── 4. ACTUALIZAR FOTO DE MI PROPIO PERFIL ────────────────────────────────────
@usuario_bp.route("/api/perfil/foto", methods=["PUT", "POST"])
@jwt_required()
def actualizar_foto_mi_perfil():
    try:
        identidad = get_jwt_identity()
        id_usuario = identidad.get("idUsuario") if isinstance(identidad, dict) else int(identidad)

        data = request.get_json(silent=True) or {}
        url_foto = data.get("url_foto") or data.get("foto")
        archivo = request.files.get("foto")

        resultado, message, code = service.actualizar_foto_usuario(
            id_usuario=id_usuario,
            raw_foto=url_foto,
            archivo_foto=archivo
        )

        if resultado is None:
            return jsonify({"success": False, "status": False, "message": message}), code

        return jsonify({
            "success": True,
            "status": True,
            "message": message,
            "data": resultado
        }), code
    except Exception as e:
        return jsonify({"success": False, "status": False, "message": str(e)}), 400


# ── 5. OBTENER FOTO DE MI PROPIO PERFIL (STREAM DE IMAGEN) ───────────────────
@usuario_bp.route("/api/perfil/foto", methods=["GET"])
@jwt_required()
def obtener_foto_mi_perfil():
    identidad = get_jwt_identity()
    id_usuario = identidad.get("idUsuario") if isinstance(identidad, dict) else int(identidad)

    ruta, mimetype, message, code = service.obtener_foto_perfil(id_usuario)
    if ruta is None:
        return error_response(message, code)
    return send_file(ruta, mimetype=mimetype, as_attachment=False, conditional=True)


# ── 6. OBTENER FOTO DE UN USUARIO (STREAM DE IMAGEN) ──────────────────────────
@usuario_bp.route("/api/usuarios/<int:id_usuario>/foto", methods=["GET"])
@jwt_required(optional=True)
def obtener_foto_usuario(id_usuario):
    ruta, mimetype, message, code = service.obtener_foto_perfil(id_usuario)
    if ruta is None:
        return error_response(message, code)
    return send_file(ruta, mimetype=mimetype, as_attachment=False, conditional=True)
