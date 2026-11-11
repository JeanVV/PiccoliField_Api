from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.punto_venta_service import PuntoVentaService
from utils.response import success_response, error_response

punto_venta_bp = Blueprint("puntos_venta", __name__)
service = PuntoVentaService()


# ── 1. LISTAR PUNTOS DE VENTA / DISTRIBUCIÓN ──────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta", methods=["GET"])
@jwt_required(optional=True)
def listar_puntos():
    search = request.args.get("search")
    distrito = request.args.get("distrito")
    estado = request.args.get("estado", "ACTIVO")
    tipo = request.args.get("tipo")
    idUsuario_param = request.args.get("idUsuario", type=int)

    # Si se pide ?asignados=true y hay usuario autenticado
    asignados = request.args.get("asignados", "").lower() in ("true", "1")
    if asignados:
        idUsuario_actual = get_jwt_identity()
        if idUsuario_actual:
            idUsuario_param = int(idUsuario_actual)

    data, message, http_code = service.listar_puntos(
        search=search,
        distrito=distrito,
        estado=estado,
        tipo=tipo,
        idUsuario=idUsuario_param
    )
    return success_response(data, message, http_code)


# ── 2. OBTENER DETALLE DE UN PUNTO DE VENTA ───────────────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def obtener_punto(id):
    data, message, http_code = service.obtener_punto(idPuntosVenta=id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 3. ASIGNAR RESPONSABLE / PROMOTOR AL PUNTO DE VENTA (ADMINISTRADOR) ───────
@punto_venta_bp.route("/api/puntos-venta/<int:id>/responsable", methods=["PUT", "POST"])
@jwt_required()
def asignar_responsable(id):
    idUsuarioRegistra = get_jwt_identity()
    datos = request.get_json(silent=True)

    if not datos:
        return error_response("Debe enviar los datos en formato JSON", 400)

    idUsuarioNuevo = datos.get("idUsuario")
    if not idUsuarioNuevo:
        return error_response("El campo 'idUsuario' es obligatorio", 400)

    motivo = datos.get("motivo")
    data, message, http_code = service.asignar_responsable(
        idPuntosVenta=id,
        idUsuarioNuevo=idUsuarioNuevo,
        idUsuarioRegistra=idUsuarioRegistra,
        motivo=motivo
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 4. HISTORIAL DE ASIGNACIONES DEL PUNTO DE VENTA ───────────────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id>/historial", methods=["GET"])
@jwt_required()
def obtener_historial_asignaciones(id):
    data, message, http_code = service.obtener_historial_asignaciones(idPuntosVenta=id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)
