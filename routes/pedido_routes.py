from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.pedido_service import PedidoService
from utils.response import success_response, error_response

pedido_bp = Blueprint("pedidos", __name__)
service = PedidoService()


# ── 1. LISTAR PEDIDOS ──────────────────────────────────────────────────────────
@pedido_bp.route("/api/pedidos", methods=["GET"])
@jwt_required()
def listar_pedidos():
    idUsuario = get_jwt_identity()
    idPuntosVenta = request.args.get("idPuntosVenta", type=int)
    estado = request.args.get("estado")
    tipo_pdv = request.args.get("tipo") or request.args.get("tipo_pdv")

    data, message, http_code = service.listar_pedidos(
        idUsuario=idUsuario,
        idPuntosVenta=idPuntosVenta,
        estado=estado,
        tipo_pdv=tipo_pdv
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 2. OBTENER DETALLE DE UN PEDIDO ──────────────────────────────────────────
@pedido_bp.route("/api/pedidos/<int:id>", methods=["GET"])
@jwt_required()
def obtener_pedido(id):
    idUsuario = get_jwt_identity()
    data, message, http_code = service.obtener_pedido(idUsuario=idUsuario, idPedido=id)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 3. REGISTRAR NUEVO PEDIDO (IDEMPOTENTE CON X-Operation-Id) ─────────────────
@pedido_bp.route("/api/pedidos", methods=["POST"])
@jwt_required()
def crear_pedido():
    idUsuario = get_jwt_identity()
    payload = request.get_json(silent=True)

    if payload is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    operation_id = request.headers.get("X-Operation-Id") or request.headers.get("x-operation-id")

    data, message, http_code = service.crear_pedido(
        idUsuario=idUsuario,
        payload=payload,
        operation_id=operation_id
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 4. CAMBIAR ESTADO DE PEDIDO (DESPACHO) ───────────────────────────────────
@pedido_bp.route("/api/pedidos/<int:id>/estado", methods=["PUT", "PATCH"])
@jwt_required()
def actualizar_estado(id):
    idUsuario = get_jwt_identity()
    payload = request.get_json(silent=True)

    if payload is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    nuevo_estado = payload.get("estado")
    data, message, http_code = service.actualizar_estado(
        idUsuario=idUsuario,
        idPedido=id,
        nuevo_estado=nuevo_estado
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

