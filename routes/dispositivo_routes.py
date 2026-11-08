from flask import Blueprint, request
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from services.dispositivo_service import DispositivoService
from utils.response import success_response, error_response


dispositivo_bp = Blueprint("dispositivos", __name__)


@dispositivo_bp.route(
    "/api/dispositivo",
    methods=["PUT"]
)
@jwt_required()
def actualizar_dispositivo():
    datos = request.get_json(silent=True)

    if datos is None:
        return error_response(
            "Debe enviar los datos en formato JSON",
            400
        )

    service = DispositivoService()

    data, message, http_code = service.actualizar(
        get_jwt_identity(),
        datos
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(
        data,
        message,
        http_code
    )
