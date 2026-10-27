from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.supervision_service import SupervisionService
from utils.response import success_response, error_response

supervision_bp = Blueprint("supervision", __name__)

# ── 1. DASHBOARD Y RESUMEN ──────────────────────────────────────────────────
@supervision_bp.route("/api/supervision/resumen", methods=["GET"])
@jwt_required()
def resumen_dashboard():
    service = SupervisionService()
    data, message, http_code = service.obtener_resumen_dashboard()
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 2. IMPULSADORES / VENDEDORES ─────────────────────────────────────────────
@supervision_bp.route("/api/supervision/vendedores", methods=["GET"])
@jwt_required()
def listar_vendedores():
    service = SupervisionService()
    data, message, http_code = service.listar_mejores_vendedores()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@supervision_bp.route("/api/supervision/vendedores/<int:idUsuario>", methods=["GET"])
@jwt_required()
def detalle_vendedor(idUsuario):
    service = SupervisionService()
    data, message, http_code = service.obtener_detalle_vendedor(idUsuario)
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


@supervision_bp.route("/api/supervision/impulsadores", methods=["GET"])
@jwt_required()
def listar_impulsadores():
    service = SupervisionService()
    data, message, http_code = service.listar_impulsadores()

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


@supervision_bp.route("/api/supervision/impulsadores/<int:idUsuario>/foto", methods=["GET"])
@jwt_required(optional=True)
def obtener_foto_impulsador(idUsuario):
    service = SupervisionService()
    file_path, message, http_code = service.obtener_ruta_foto_impulsador(idUsuario)

    if not file_path:
        return error_response(message, http_code)
    return send_file(file_path)


# ── 3. PRODUCTOS (FOTO Y DETALLE) ───────────────────────────────────────────
@supervision_bp.route("/api/supervision/productos/<int:idProductos>/foto", methods=["GET"])
@jwt_required(optional=True)
def obtener_foto_producto(idProductos):
    service = SupervisionService()
    file_path, message, http_code = service.obtener_ruta_foto_producto(idProductos)

    if not file_path:
        return error_response(message, http_code)
    return send_file(file_path)


# ── 4. PUNTOS DE VENTA (TIPO VENTA) ─────────────────────────────────────────
@supervision_bp.route("/api/supervision/puntos-venta", methods=["GET"])
@jwt_required()
def listar_puntos_venta():
    service = SupervisionService()
    data, message, http_code = service.listar_puntos_venta()
    
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


@supervision_bp.route("/api/supervision/puntos-venta/<int:idPuntosVenta>", methods=["GET"])
@jwt_required()
def detalle_punto_venta(idPuntosVenta):
    service = SupervisionService()
    data, message, http_code = service.obtener_detalle_punto_venta(idPuntosVenta)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


@supervision_bp.route("/api/supervision/puntos-venta/<int:idPuntosVenta>/historial", methods=["GET"])
@jwt_required()
def historial_impulsadores_pdv(idPuntosVenta):
    service = SupervisionService()
    data, message, http_code = service.obtener_historial_impulsadores(idPuntosVenta)

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 5. REASIGNACIÓN DE IMPULSADOR A PUNTO DE VENTA ──────────────────────────
@supervision_bp.route("/api/supervision/reasignar-impulsador", methods=["POST"])
@jwt_required()
def reasignar_impulsador():
    idUsuarioRegistra = get_jwt_identity()
    datos = request.get_json(silent=True) or {}

    idUsuario = datos.get("idUsuario")
    idPuntosVenta = datos.get("idPuntosVenta")
    motivo = datos.get("motivo")

    if not idUsuario or not idPuntosVenta:
        return error_response("idUsuario e idPuntosVenta son obligatorios", 400)

    try:
        idUsuario = int(idUsuario)
        idPuntosVenta = int(idPuntosVenta)
        idUsuarioRegistra = int(idUsuarioRegistra)
    except (ValueError, TypeError):
        return error_response("idUsuario e idPuntosVenta deben ser números enteros", 400)

    service = SupervisionService()
    data, message, http_code = service.reasignar_impulsador(
        idPuntosVenta=idPuntosVenta,
        idUsuario=idUsuario,
        idUsuarioRegistra=idUsuarioRegistra,
        motivo=motivo
    )

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


@supervision_bp.route("/api/supervision/puntos-venta/<int:idPuntosVenta>/reasignar", methods=["POST", "PUT"])
@jwt_required()
def reasignar_impulsador_pdv(idPuntosVenta):
    idUsuarioRegistra = get_jwt_identity()
    datos = request.get_json(silent=True) or {}

    idUsuario = datos.get("idUsuario")
    motivo = datos.get("motivo")

    if not idUsuario:
        return error_response("idUsuario es obligatorio", 400)

    try:
        idUsuario = int(idUsuario)
        idPuntosVenta = int(idPuntosVenta)
        idUsuarioRegistra = int(idUsuarioRegistra)
    except (ValueError, TypeError):
        return error_response("idUsuario e idPuntosVenta deben ser números enteros", 400)

    service = SupervisionService()
    data, message, http_code = service.reasignar_impulsador(
        idPuntosVenta=idPuntosVenta,
        idUsuario=idUsuario,
        idUsuarioRegistra=idUsuarioRegistra,
        motivo=motivo
    )

    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 6. ALERTAS DE STOCK ──────────────────────────────────────────────────────
@supervision_bp.route("/api/supervision/alertas", methods=["GET"])
@jwt_required()
def listar_alertas():
    service = SupervisionService()
    data, message, http_code = service.listar_alertas()
    
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