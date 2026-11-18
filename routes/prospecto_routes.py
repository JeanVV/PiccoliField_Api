import os
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from config import BASE_DIR
from services.prospecto_service import ProspectoService
from utils.response import success_response, error_response

prospecto_bp = Blueprint("prospectos", __name__)
service = ProspectoService()

PROSPECTOS_DIR = os.path.join(BASE_DIR, "uploads", "prospectos")


# ── 1. LISTAR PROSPECTOS (CON FILTROS) ────────────────────────────────────────
@prospecto_bp.route("/api/prospectos", methods=["GET"])
@jwt_required()
def listar_prospectos():
    estado = request.args.get("estado")
    potencial = request.args.get("potencial")
    idDistrito = request.args.get("idDistrito", type=int)
    idUsuario = request.args.get("idUsuario", type=int)
    search = request.args.get("search")

    data, message, http_code = service.listar_prospectos(
        estado=estado,
        potencial=potencial,
        idDistrito=idDistrito,
        idUsuario=idUsuario,
        search=search
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 2. OBTENER DETALLE DE UN PROSPECTO ────────────────────────────────────────
@prospecto_bp.route("/api/prospectos/<int:id>", methods=["GET"])
@jwt_required()
def obtener_prospecto(id):
    data, message, http_code = service.obtener_prospecto(idProspectos=id)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 3. REGISTRAR NUEVO PROSPECTO ──────────────────────────────────────────────
@prospecto_bp.route("/api/prospectos", methods=["POST"])
@jwt_required()
def crear_prospecto():
    idUsuario = get_jwt_identity()

    # Si viene como multipart/form-data o JSON
    if request.is_json:
        payload = request.get_json(silent=True) or {}
    else:
        payload = request.form.to_dict()

    # Soporte para subir foto del local
    if "foto" in request.files or "imagen" in request.files:
        foto_file = request.files.get("foto") or request.files.get("imagen")
        if foto_file and foto_file.filename:
            os.makedirs(PROSPECTOS_DIR, exist_ok=True)
            import uuid
            ext = os.path.splitext(foto_file.filename)[1] or ".jpg"
            filename = f"prospect_{uuid.uuid4().hex[:10]}{ext}"
            abs_path = os.path.join(PROSPECTOS_DIR, filename)
            foto_file.save(abs_path)
            payload["url_foto"] = f"uploads/prospectos/{filename}"

    data, message, http_code = service.crear_prospecto(
        idUsuarioAutenticado=idUsuario,
        payload=payload
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 4. ACTUALIZAR DATOS DE UN PROSPECTO ───────────────────────────────────────
@prospecto_bp.route("/api/prospectos/<int:id>", methods=["PUT"])
@jwt_required()
def actualizar_prospecto(id):
    payload = request.get_json(silent=True) or {}
    data, message, http_code = service.actualizar_prospecto(idProspectos=id, payload=payload)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 5. CAMBIAR ESTADO DE PROSPECTO (SI ES CONVERTIDO -> CREA PUNTO DE VENTA) ─
@prospecto_bp.route("/api/prospectos/<int:id>/estado", methods=["PUT", "PATCH"])
@jwt_required()
def cambiar_estado(id):
    idUsuario = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    nuevo_estado = payload.get("estado")
    motivo_descarte = payload.get("motivo_descarte") or payload.get("motivo")

    data, message, http_code = service.cambiar_estado(
        idProspectos=id,
        nuevo_estado=nuevo_estado,
        motivo_descarte=motivo_descarte,
        idUsuarioRevisor=idUsuario
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 6. ASIGNAR PROMOTOR AL PROSPECTO ──────────────────────────────────────────
@prospecto_bp.route("/api/prospectos/<int:id>/asignar", methods=["PUT", "POST"])
@jwt_required()
def asignar_promotor(id):
    payload = request.get_json(silent=True) or {}
    idUsuario = payload.get("idUsuario")

    data, message, http_code = service.asignar_promotor(
        idProspectos=id,
        idUsuario=idUsuario
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 7. REGISTRAR SEGUIMIENTO (LLAMADA, VISITA, PROPUESTA, MENSAJE) ────────────
@prospecto_bp.route("/api/prospectos/<int:id>/seguimientos", methods=["POST"])
@jwt_required()
def crear_seguimiento(id):
    idUsuario = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    data, message, http_code = service.crear_seguimiento(
        idProspectos=id,
        idUsuario=idUsuario,
        payload=payload
    )

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 8. LISTAR SEGUIMIENTOS DE UN PROSPECTO ────────────────────────────────────
@prospecto_bp.route("/api/prospectos/<int:id>/seguimientos", methods=["GET"])
@jwt_required()
def listar_seguimientos(id):
    data, message, http_code = service.listar_seguimientos(idProspectos=id)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)
