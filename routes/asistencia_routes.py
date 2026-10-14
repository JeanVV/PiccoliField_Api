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


@asistencia_bp.route("/api/asistencias/detalle/<int:idUsuario>", methods=["GET"])
@jwt_required()
def obtener_detalle(idUsuario):
    service = AsistenciaService()
    data, message, http_code = service.obtener_detalle(idUsuario)

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


@asistencia_bp.route("/api/asistencias/evidencias/<int:idAsistencia>", methods=["GET"])
@jwt_required()
def obtener_evidencias(idAsistencia):
    service = AsistenciaService()
    data, message, http_code = service.obtener_evidencias(idAsistencia)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/asistenciaPersonal", methods=["POST"])
@jwt_required()
def marcar_asistenciaPersonal():
    data = request.get_json()
    idUsuario = data.get("idUsuario")
    tipo = data.get("tipo")
    service = AsistenciaService()
    data, message, http_code = service.marcarAsistenciaPersonal(idUsuario, tipo)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)

