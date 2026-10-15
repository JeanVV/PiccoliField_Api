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

@supervision_bp.route("/api/supervision/puntos-venta", methods=["GET"])
@jwt_required()
def listar_puntos_venta():
    service = SupervisionService()
    data, message, http_code = service.listar_puntos_venta()
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)

@supervision_bp.route("/api/supervision/alertas", methods=["GET"])
@jwt_required()
def listar_alertas():
    service = SupervisionService()
    data, message, http_code = service.listar_alertas()
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)

@supervision_bp.route("/api/prospectos/listar", methods=["GET"])
@jwt_required()
def listar_prospectos():
    service = SupervisionService()
    data, message, http_code = service.listar_prospectos()
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)



@supervision_bp.route("/api/prospectos/<int:id>/contactar", methods=["PUT"])
@jwt_required()
def actualizar_punto_venta(idPr):
    service = SupervisionService()
    data, message, http_code = service.actualizar_prospecto(idPr)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)















@supervision_bp.route("/api/supervision/nuevo-endpoint", methods=["GET"])
@jwt_required()
def nuevo_endpoint():
    service = SupervisionService()
    data, message, http_code = service.obtener_nuevo_recurso()
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)

@supervision_bp.route("/api/supervision/alertas", methods=["POST"])
@jwt_required()
def crear_alerta():
    body = request.get_json()  # Captura el body JSON enviado desde Postman
    service = SupervisionService()
    data, message, http_code = service.registrar_alerta(body)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)
    #{ "idPuntosVenta": 1, "idProductos": 2, "tipo": "ALTA" }

@supervision_bp.route("/api/supervision/puntos-venta/<int:idPdv>", methods=["PUT"])
@jwt_required()
def actualizar_punto_venta(idPdv):
    body = request.get_json()
    service = SupervisionService()
    data, message, http_code = service.actualizar_punto_venta(idPdv, body)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)
    #{ "nombre": "Plaza Vea Chiclayo", "direccion": "Av. Bolognesi 123", "estado": "ACTIVO" }

@supervision_bp.route("/api/supervision/alertas/<int:idAlerta>/estado", methods=["PATCH"])
@jwt_required()
def actualizar_estado_alerta(idAlerta):
    body = request.get_json()
    service = SupervisionService()
    data, message, http_code = service.cambiar_estado_alerta(idAlerta, body)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)
    #{ "estado": "RESUELTO" }

@supervision_bp.route("/api/supervision/alertas/<int:idAlerta>", methods=["DELETE"])    
@jwt_required()
def borrar_alerta(idAlerta):
    service = SupervisionService()
    data, message, http_code = service.eliminar_alerta(idAlerta)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code) 