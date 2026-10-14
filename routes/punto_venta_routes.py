from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.punto_venta_service import PuntoVentaService
from utils.response import success_response, error_response

punto_venta_bp = Blueprint("puntos_venta", __name__)
service = PuntoVentaService()

# ── 1. LISTAR PUNTOS DE DISTRIBUCIÓN ──────────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta", methods=["GET"])
def listar_puntos():
    search = request.args.get("search")
    distrito = request.args.get("distrito")
    estado = request.args.get("estado", "ACTIVO")

    data, message, http_code = service.listar_puntos(search=search, distrito=distrito, estado=estado)
    return success_response(data, message, http_code)


# ── 2. PUNTOS MÁS CERCANOS (GPS) ──────────────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/cercanos", methods=["GET"])
def puntos_cercanos():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    radio_km = request.args.get("radio_km", 10)

    if not lat or not lng:
        return error_response("Los parámetros lat y lng son obligatorios", 400)

    data, message, http_code = service.buscar_cercanos(lat=lat, lng=lng, radio_km=radio_km)
    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 3. DETALLE DEL PUNTO DE DISTRIBUCIÓN ──────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>", methods=["GET"])
def obtener_punto(id):
    data, message, http_code = service.obtener_detalle(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 4. PRODUCTOS DISPONIBLES EN EL PUNTO ──────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>/productos", methods=["GET"])
def obtener_productos(id):
    data, message, http_code = service.obtener_productos(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 5. REGISTRAR PUNTO DE DISTRIBUCIÓN ────────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta", methods=["POST"])
@jwt_required()
def crear_punto():
    datos = request.get_json(silent=True)
    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    data, message, http_code = service.crear_punto(datos)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 6. ACTUALIZAR PUNTO DE DISTRIBUCIÓN ───────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>", methods=["PUT"])
@jwt_required()
def actualizar_punto(id):
    datos = request.get_json(silent=True)
    if datos is None:
        return error_response("Debe enviar los datos en formato JSON", 400)

    data, message, http_code = service.actualizar_punto(id, datos)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 7. CAMBIAR ESTADO DEL PUNTO ───────────────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>/estado", methods=["PATCH"])
@jwt_required()
def cambiar_estado(id):
    datos = request.get_json(silent=True)
    if datos is None or "estado" not in datos:
        return error_response("Debe enviar el campo 'estado' en el JSON", 400)

    data, message, http_code = service.cambiar_estado(id, str(datos["estado"]).upper())
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 8. ELIMINAR / DESACTIVAR PUNTO ───────────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>", methods=["DELETE"])
@jwt_required()
def eliminar_punto(id):
    data, message, http_code = service.cambiar_estado(id, "INACTIVO")
    if data is None:
        return error_response(message, http_code)
    return success_response(data, "Punto de distribución dado de baja correctamente", 200)


# ── 9. MAPA DE CALOR (HEATMAP PEDIDOS) ────────────────────────────────────────
@punto_venta_bp.route("/api/mapa-calor/pedidos", methods=["GET"])
def mapa_calor_pedidos():
    data, message, http_code = service.mapa_calor()
    return success_response(data, message, http_code)


# ── 10. MAPA DE CALOR ZONAS ───────────────────────────────────────────────────
@punto_venta_bp.route("/api/mapa-calor/zonas", methods=["GET"])
def mapa_calor_zonas():
    distrito = request.args.get("distrito")
    data, message, http_code = service.listar_puntos(distrito=distrito, estado="ACTIVO")
    return success_response(data, message, http_code)


# ── 11. HISTORIAL DE PEDIDOS ANTERIORES DEL PUNTO ─────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>/historial-pedidos", methods=["GET"])
@jwt_required()
def historial_pedidos(id):
    data, message, http_code = service.historial_pedidos(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 12. RESUMEN DE DEMANDA DEL PUNTO ──────────────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>/resumen-demanda", methods=["GET"])
@jwt_required()
def resumen_demanda(id):
    data, message, http_code = service.resumen_demanda(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)
