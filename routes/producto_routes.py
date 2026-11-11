from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.producto_service import ProductoService
from utils.response import success_response, error_response

producto_bp = Blueprint("productos", __name__)
service = ProductoService()


# ── 1. LISTAR CATÁLOGO DE PRODUCTOS (AUTENTICADO) ─────────────────────────────
@producto_bp.route("/api/productos", methods=["GET"])
@jwt_required(optional=True)
def listar_productos():
    search = request.args.get("search")
    categoria = request.args.get("categoria")

    data, message, http_code = service.listar_productos(search=search, categoria=categoria)
    return success_response(data, message, http_code)


# ── 2. BUSCAR PRODUCTO POR CÓDIGO EAN O SKU ──────────────────────────────────
@producto_bp.route("/api/productos/ean/<string:codigo>", methods=["GET"])
@jwt_required(optional=True)
def buscar_por_ean(codigo):
    data, message, http_code = service.buscar_por_ean(codigo)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)


# ── 3. OBTENER DETALLE DE UN PRODUCTO POR ID ─────────────────────────────────
@producto_bp.route("/api/productos/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def obtener_producto(id):
    data, message, http_code = service.obtener_por_id(id)
    if data is None:
        return error_response(message, http_code)
    return success_response(data, message, http_code)

