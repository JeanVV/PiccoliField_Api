from flask import Blueprint, request

from services.auth_service import AuthService
from utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True)

    if not body:
        return error_response("El cuerpo de la solicitud es requerido", 400)

    correo = body.get("correo", "").strip()
    password = body.get("password", "").strip()

    if not correo or not password:
        return error_response("Correo y contraseña son requeridos", 400)

    service = AuthService()
    data, message, http_code = service.login(correo, password)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)
