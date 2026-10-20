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
