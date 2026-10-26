from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.asistencia_service import AsistenciaService
from utils.response import error_response, success_response

asistencia_bp = Blueprint("asistencias", __name__)


@asistencia_bp.route("/api/asistencias/resumen", methods=["GET"])
@jwt_required()
def obtener_resumen():
    service = AsistenciaService()
    data, message, http_code = service.obtener_resumen()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/recientes", methods=["GET"])
@jwt_required()
def obtener_recientes():
    limite = request.args.get("limite", default=10, type=int)

    service = AsistenciaService()
    data, message, http_code = service.obtener_recientes(limite=limite)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/colaboradores", methods=["GET"])
@jwt_required()
def obtener_colaboradores():
    service = AsistenciaService()
    data, message, http_code = service.obtener_colaboradores()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/historial/<int:idUsuario>", methods=["GET"])
@jwt_required()
def obtener_historial(idUsuario):
    service = AsistenciaService()
    data, message, http_code = service.obtener_historial(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

@asistencia_bp.route("/api/asistencias/marcar", methods=["POST"])
@jwt_required()
def marcar_asistencia():
    data = request.get_json()
    if not data:
        return error_response("Cuerpo de la petición vacío", 400)

    service = AsistenciaService()
    resultado, message, http_code = service.registrar_asistencia(data)

    if resultado is None:
        return error_response(message, http_code)

    return success_response(resultado, message, http_code)


@asistencia_bp.route("/api/asistencias/justificar", methods=["POST"])
@jwt_required()
def registrar_justificacion():
    data = request.get_json()
    if not data:
        return error_response("Cuerpo de la petición vacío", 400)

    service = AsistenciaService()
    resultado, message, http_code = service.registrar_justificacion(data)

    if resultado is None:
        return error_response(message, http_code)

    return success_response(resultado, message, http_code)


@asistencia_bp.route("/api/asistencias/justificacion/<int:idUsuario>", methods=["GET"])
@jwt_required()
def obtener_justificacion(idUsuario):
    service = AsistenciaService()
    data, message, http_code = service.obtener_justificacion(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)
