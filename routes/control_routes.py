from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.control_service import ControlService
from utils.response import success_response, error_response

control_bp = Blueprint("control", __name__)
service = ControlService()

# ── 1. LISTAR PROMOTORES Y SU ESTADO ─────────────────────────────────────────
@control_bp.route("/api/control/promotores", methods=["GET"])
@jwt_required()
def listar_promotores():
    data, message, http_code = service.listar_promotores()
    return success_response(data, message, http_code)


# ── 2. ASIGNAR PROMOTOR A UN PUNTO DE VENTA ──────────────────────────────────
@control_bp.route("/api/control/asignar-punto", methods=["POST"])
@jwt_required()
def asignar_punto():
    datos = request.get_json(silent=True) or {}
    idUsuario = datos.get("idUsuario")
    idPuntosVenta = datos.get("idPuntosVenta")

    data, message, http_code = service.asignar_punto(idUsuario, idPuntosVenta)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 3. VER PUNTOS DE VENTA ASIGNADOS A UN PROMOTOR ───────────────────────────
@control_bp.route("/api/control/promotores/<int:id>/puntos", methods=["GET"])
@jwt_required()
def puntos_promotor(id):
    data, message, http_code = service.puntos_por_promotor(id)
    return success_response(data, message, http_code)


# ── 4. SUPERVISIÓN DE ASISTENCIAS EN PUNTOS ──────────────────────────────────
@control_bp.route("/api/control/asistencias-puntos", methods=["GET"])
@jwt_required()
def asistencias_puntos():
    fecha = request.args.get("fecha")
    data, message, http_code = service.asistencias_supervision(fecha=fecha)
    return success_response(data, message, http_code)


# ── 5. ALERTAS DE QUIEBRE / STOCK BAJO ───────────────────────────────────────
@control_bp.route("/api/control/alertas-stock", methods=["GET"])
@jwt_required()
def alertas_stock():
    estado = request.args.get("estado", "PENDIENTE")
    data, message, http_code = service.alertas_stock(estado=estado)
    return success_response(data, message, http_code)


# ── 6. ATENDER ALERTA DE STOCK ───────────────────────────────────────────────
@control_bp.route("/api/control/alertas-stock/<int:id>/atender", methods=["PATCH"])
@jwt_required()
def atender_alerta(id):
    datos = request.get_json(silent=True) or {}
    comentario = datos.get("comentario")
    data, message, http_code = service.atender_alerta(id, comentario=comentario)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 7. DASHBOARD KPIS (JEFA) ─────────────────────────────────────────────────
@control_bp.route("/api/control/dashboard-kpis", methods=["GET"])
@jwt_required()
def dashboard_kpis():
    data, message, http_code = service.dashboard_kpis()
    return success_response(data, message, http_code)


# ── 8. DESASIGNAR PROMOTOR DE UN PUNTO ───────────────────────────────────────
@control_bp.route("/api/control/desasignar-punto/<int:id>", methods=["DELETE"])
@jwt_required()
def desasignar_punto(id):
    data, message, http_code = service.desasignar_punto(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 9. CATEGORÍAS DE LOCALES (CHIPS FILTRO APP) ──────────────────────────────
@control_bp.route("/api/categorias-locales", methods=["GET"])
def categorias_locales():
    data, message, http_code = service.categorias_locales()
    return success_response(data, message, http_code)


# ── 10. PRODUCTOS DESTACADOS PICCOLI (CÓCTELES) ──────────────────────────────
@control_bp.route("/api/productos/destacados", methods=["GET"])
def productos_destacados():
    data, message, http_code = service.productos_destacados()
    return success_response(data, message, http_code)


# ── 11. DISTRITOS ACTIVOS CON PUNTOS DE VENTA ────────────────────────────────
@control_bp.route("/api/geografia/distritos-activos", methods=["GET"])
def distritos_activos():
    data, message, http_code = service.distritos_activos()
    return success_response(data, message, http_code)
