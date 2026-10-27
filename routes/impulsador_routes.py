from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.impulsador_service import ImpulsadorService
from utils.response import success_response, error_response

impulsador_bp = Blueprint("impulsador", __name__)


# ── 1. DASHBOARD DEL IMPULSADOR ───────────────────────────────────────────────
@impulsador_bp.route("/api/impulsador/dashboard", methods=["GET"])
@jwt_required()
def dashboard_impulsador():
    idUsuario = get_jwt_identity()
    service = ImpulsadorService()
    data, message, http_code = service.obtener_dashboard(idUsuario)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 2. HISTORIAL DE PUNTOS DE VENTA ASIGNADOS ─────────────────────────────────
@impulsador_bp.route("/api/impulsador/historial", methods=["GET"])
@jwt_required()
def historial_impulsador():
    idUsuario = get_jwt_identity()
    service = ImpulsadorService()
    data, message, http_code = service.obtener_historial(idUsuario)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 3. BÚSQUEDA DE PRODUCTO POR CÓDIGO DE BARRAS / SKU (PARA BOTTOMSHEET) ─────
@impulsador_bp.route("/api/impulsador/productos/buscar", methods=["GET"])
@jwt_required()
def buscar_producto():
    idUsuario = get_jwt_identity()
    codigo = request.args.get("codigo") or request.args.get("codigo_barras") or request.args.get("sku")
    idPuntosVenta = request.args.get("idPuntosVenta", type=int)

    if not codigo:
        return error_response("El parámetro 'codigo' es requerido", 400)

    service = ImpulsadorService()
    data, message, http_code = service.buscar_producto(
        idUsuario=idUsuario,
        codigo=codigo,
        idPuntosVenta=idPuntosVenta
    )

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


@impulsador_bp.route("/api/impulsador/productos/codigo/<string:codigo_barras>", methods=["GET"])
@jwt_required()
def buscar_producto_por_path(codigo_barras):
    idUsuario = get_jwt_identity()
    idPuntosVenta = request.args.get("idPuntosVenta", type=int)

    service = ImpulsadorService()
    data, message, http_code = service.buscar_producto(
        idUsuario=idUsuario,
        codigo=codigo_barras,
        idPuntosVenta=idPuntosVenta
    )

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 4. CATÁLOGO DE PRODUCTOS EN EL LOCAL ASIGNADO ─────────────────────────────
@impulsador_bp.route("/api/impulsador/productos", methods=["GET"])
@jwt_required()
def listar_productos():
    idUsuario = get_jwt_identity()
    search = request.args.get("search")
    idPuntosVenta = request.args.get("idPuntosVenta", type=int)

    service = ImpulsadorService()
    data, message, http_code = service.listar_productos_local(
        idUsuario=idUsuario,
        search=search,
        idPuntosVenta=idPuntosVenta
    )

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 5. REGISTRAR VENTA POR CÓDIGO DE BARRAS ───────────────────────────────────
@impulsador_bp.route("/api/impulsador/ventas/registrar", methods=["POST"])
@jwt_required()
def registrar_venta():
    idUsuario = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    service = ImpulsadorService()
    data, message, http_code = service.registrar_venta(idUsuario=idUsuario, payload=payload)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 6. REPORTAR INCIDENCIA CON O SIN FOTOGRAFÍA ────────────────────────────────
@impulsador_bp.route("/api/impulsador/incidencias", methods=["POST"])
@jwt_required()
def reportar_incidencia():
    idUsuario = get_jwt_identity()

    # Si viene como multipart/form-data
    if request.files:
        payload = request.form.to_dict()
        foto = request.files.get("foto") or request.files.get("imagen")
    else:
        payload = request.get_json(silent=True) or {}
        foto = None

    service = ImpulsadorService()
    data, message, http_code = service.reportar_incidencia(
        idUsuario=idUsuario,
        payload=payload,
        archivo_foto=foto
    )

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)
