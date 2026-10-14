from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.pedido_service import PedidoService
from utils.response import success_response, error_response

pedido_bp = Blueprint("pedidos", __name__)
service = PedidoService()

# ── 1. LISTAR PEDIDOS ────────────────────────────────────────────────────────
@pedido_bp.route("/api/pedidos", methods=["GET"])
@jwt_required()
def listar_pedidos():
    idPuntosVenta = request.args.get("idPuntosVenta")
    data, message, http_code = service.listar_pedidos(idPuntosVenta=idPuntosVenta)
    return success_response(data, message, http_code)


# ── 2. CREAR PEDIDO (TRANSACCIONAL) ──────────────────────────────────────────
@pedido_bp.route("/api/pedidos", methods=["POST"])
@jwt_required()
def crear_pedido():
    datos = request.get_json(silent=True)
    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    data, message, http_code = service.crear_pedido(datos)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 3. DETALLE DE UN PEDIDO ──────────────────────────────────────────────────
@pedido_bp.route("/api/pedidos/<int:id>", methods=["GET"])
@jwt_required()
def obtener_pedido(id):
    data, message, http_code = service.obtener_detalle(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 4. MODIFICAR PEDIDO ──────────────────────────────────────────────────────
@pedido_bp.route("/api/pedidos/<int:id>", methods=["PUT"])
@jwt_required()
def actualizar_pedido(id):
    datos = request.get_json(silent=True)
    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    data, message, http_code = service.actualizar_pedido(id, datos)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 5. CANCELAR PEDIDO ───────────────────────────────────────────────────────
@pedido_bp.route("/api/pedidos/<int:id>/cancelar", methods=["PATCH"])
@jwt_required()
def cancelar_pedido(id):
    data, message, http_code = service.cancelar_pedido(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 6. ELIMINAR PEDIDO ───────────────────────────────────────────────────────
@pedido_bp.route("/api/pedidos/<int:id>", methods=["DELETE"])
@jwt_required()
def eliminar_pedido(id):
    data, message, http_code = service.cancelar_pedido(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, "Pedido eliminado correctamente", 200)


# ── 7. PEDIDOS PENDIENTES DE UN PUNTO ────────────────────────────────────────
@pedido_bp.route("/api/puntos-venta/<int:id>/pedidos-pendientes", methods=["GET"])
@jwt_required()
def pedidos_pendientes_punto(id):
    data, message, http_code = service.listar_pedidos(idPuntosVenta=id)
    # Filtrar solo pendientes
    pendientes = [p for p in (data or []) if p.get("estado_despacho") == "PENDIENTE"]
    return success_response(pendientes, "Pedidos pendientes obtenidos correctamente", 200)


# ── 8. REPARTIDORES DISPONIBLES ──────────────────────────────────────────────
@pedido_bp.route("/api/repartidores/disponibles", methods=["GET"])
@jwt_required()
def repartidores_disponibles():
    data, message, http_code = service.listar_repartidores()
    return success_response(data, message, http_code)


# ── 9. LISTAR ÓRDENES DE DESPACHO ────────────────────────────────────────────
@pedido_bp.route("/api/despachos", methods=["GET"])
@jwt_required()
def listar_despachos():
    data, message, http_code = service.listar_pedidos()
    return success_response(data, "Despachos obtenidos correctamente", 200)


# ── 10. CREAR ORDEN DE DESPACHO ──────────────────────────────────────────────
@pedido_bp.route("/api/despachos", methods=["POST"])
@jwt_required()
def crear_despacho():
    datos = request.get_json(silent=True)
    if not datos:
        return error_response("Debe enviar los datos en formato JSON", 400)
    return success_response({
        "idDespacho": 101,
        "idPedido": datos.get("idPedido"),
        "idRepartidor": datos.get("idRepartidor"),
        "estado": "PROGRAMADO"
    }, "Orden de despacho creada exitosamente", 201)


# ── 11. ASIGNAR REPARTIDOR A DESPACHO ────────────────────────────────────────
@pedido_bp.route("/api/despachos/<int:id>/asignar-repartidor", methods=["POST"])
@jwt_required()
def asignar_repartidor(id):
    datos = request.get_json(silent=True) or {}
    return success_response({
        "idDespacho": id,
        "idRepartidor": datos.get("idRepartidor"),
        "estado": "ASIGNADO"
    }, "Repartidor asignado correctamente al despacho", 200)


# ── 12. MIS DESPACHOS (REPARTIDOR) ───────────────────────────────────────────
@pedido_bp.route("/api/repartidor/mis-despachos", methods=["GET"])
@jwt_required()
def mis_despachos():
    data, message, http_code = service.listar_pedidos()
    return success_response(data, "Ruta y despachos asignados al repartidor", 200)


# ── 13. INICIAR RUTA DE DESPACHO ─────────────────────────────────────────────
@pedido_bp.route("/api/despachos/<int:id>/iniciar-ruta", methods=["PATCH"])
@jwt_required()
def iniciar_ruta(id):
    return success_response({
        "idDespacho": id,
        "estado": "EN_RUTA"
    }, "Ruta de despacho iniciada. Repartidor en camino", 200)


# ── 14. COMPLETAR ENTREGA (TRANSACCIONAL) ─────────────────────────────────────
@pedido_bp.route("/api/despachos/<int:id>/completar-entrega", methods=["PATCH"])
@jwt_required()
def completar_entrega(id):
    datos = request.get_json(silent=True) or {}
    data, message, http_code = service.completar_entrega(id, datos)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 15. TRANSMITIR UBICACIÓN DEL REPARTIDOR (GPS) ─────────────────────────────
@pedido_bp.route("/api/repartidor/ubicacion-actual", methods=["POST"])
@jwt_required()
def ubicacion_repartidor():
    datos = request.get_json(silent=True) or {}
    return success_response({
        "latitud": datos.get("latitud"),
        "longitud": datos.get("longitud"),
        "timestamp": "ok"
    }, "Ubicación GPS actualizada", 200)


# ── 16. ANULAR DESPACHO ──────────────────────────────────────────────────────
@pedido_bp.route("/api/despachos/<int:id>", methods=["DELETE"])
@jwt_required()
def anular_despacho(id):
    return success_response({
        "idDespacho": id,
        "estado": "ANULADO"
    }, "Orden de despacho anulada correctamente", 200)
