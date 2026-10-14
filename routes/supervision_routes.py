from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.supervision_service import SupervisionService
from utils.response import success_response, error_response

supervision_bp = Blueprint("supervision", __name__)

@supervision_bp.route("/api/supervision/vendedores", methods=["GET"])
@jwt_required()
def listar_vendedores():
    service = SupervisionService()
    data, message, http_code = service.listar_mejores_vendedores()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

@supervision_bp.route("/api/supervision/resumen", methods=["GET"])
@jwt_required()
def resumen_dashboard():
    service = SupervisionService()
    data, message, http_code = service.obtener_resumen_dashboard()
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)

@supervision_bp.route("/api/supervision/vendedores/<int:idUsuario>", methods=["GET"])
@jwt_required()
def detalle_vendedor(idUsuario):
    # Nota: <int:idUsuario> permite atrapar el número que mandes en la URL
    service = SupervisionService()
    data, message, http_code = service.obtener_detalle_vendedor(idUsuario)
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)

@supervision_bp.route("/api/supervision/alertas/<int:idAlerta>", methods=["GET"])
@jwt_required()
def detalle_alerta(idAlerta):
    service = SupervisionService()
    data, message, http_code = service.obtener_detalle_alerta(idAlerta)
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)