import os
import base64
from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from config import BASE_DIR
from database import get_connection
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


# ── 5. GUARDAR / ACTUALIZAR FOTO DEL PUNTO DE VENTA (BASE64 O MULTIPART) ───────
@punto_venta_bp.route("/api/puntos-venta/<int:id_pdv>/foto", methods=["PUT", "POST"])
@punto_venta_bp.route("/api/supervision/puntos-venta/<int:id_pdv>/foto", methods=["PUT", "POST"])
@jwt_required()
def actualizar_foto_pdv(id_pdv):
    prospectos_dir = os.path.join(BASE_DIR, "uploads", "prospectos")
    os.makedirs(prospectos_dir, exist_ok=True)
    rel_path = f"uploads/prospectos/pdv_{id_pdv}.jpg"
    abs_path = os.path.join(BASE_DIR, rel_path)

    # 1. Caso Multipart/form-data
    if request.files:
        foto_file = request.files.get("foto") or request.files.get("imagen") or request.files.get("foto_fachada")
        if foto_file:
            foto_file.save(abs_path)
    else:
        # 2. Caso JSON Base64
        data = request.get_json(silent=True) or {}
        raw = (data.get("url_foto") or data.get("foto_fachada") or data.get("foto") or "").strip()
        if raw.startswith("data:image") or len(raw) > 100:
            b64_content = raw.split(",", 1)[1] if "," in raw else raw
            try:
                img_bytes = base64.b64decode(b64_content)
                with open(abs_path, "wb") as f:
                    f.write(img_bytes)
            except Exception as e:
                return error_response(f"Error al decodificar imagen Base64: {str(e)}", 400)

    if not os.path.isfile(abs_path):
        return error_response("No se envió ninguna imagen válida en la petición", 400)

    # Actualizar en BD (garantizando columna url_foto si no existiese)
    conn = get_connection()
    cur = conn.cursor()
    try:
        try:
            cur.execute(
                "UPDATE PUNTOS_VENTA SET url_foto = %s WHERE idPuntosVenta = %s",
                (rel_path, id_pdv)
            )
            conn.commit()
        except Exception as e:
            if "Unknown column 'url_foto'" in str(e):
                conn.rollback()
                cur.execute("ALTER TABLE PUNTOS_VENTA ADD COLUMN url_foto VARCHAR(255) NULL;")
                conn.commit()
                cur.execute(
                    "UPDATE PUNTOS_VENTA SET url_foto = %s WHERE idPuntosVenta = %s",
                    (rel_path, id_pdv)
                )
                conn.commit()
            else:
                raise e
    except Exception as e:
        conn.rollback()
        return error_response(f"Error al actualizar BD: {str(e)}", 500)
    finally:
        cur.close()
        conn.close()

    return success_response(
        {"idPuntosVenta": id_pdv, "url_foto": rel_path},
        "Foto del punto de venta guardada exitosamente",
        200
    )


# ── 6. OBTENER / SERVIR FOTO DEL PUNTO DE VENTA DIRECTAMENTE ───────────────────
@punto_venta_bp.route("/api/puntos-venta/<int:id_pdv>/foto", methods=["GET"])
@punto_venta_bp.route("/api/supervision/puntos-venta/<int:id_pdv>/foto", methods=["GET"])
@jwt_required(optional=True)
def obtener_foto_pdv(id_pdv):
    rel_path = f"uploads/prospectos/pdv_{id_pdv}.jpg"
    abs_path = os.path.join(BASE_DIR, rel_path)

    if not os.path.isfile(abs_path):
        try:
            conn = get_connection()
            cur = conn.cursor()
            try:
                # Buscar en PUNTOS_VENTA
                try:
                    cur.execute("SELECT url_foto, codigo FROM PUNTOS_VENTA WHERE idPuntosVenta = %s LIMIT 1", (id_pdv,))
                    row = cur.fetchone()
                    if row and row.get("url_foto"):
                        db_abs = os.path.join(BASE_DIR, row["url_foto"].replace("\\", "/").strip("/"))
                        if os.path.isfile(db_abs):
                            abs_path = db_abs
                    elif row and row.get("codigo", "").startswith("DIST-"):
                        # Si es convertido de prospecto (ej. DIST-0017), buscar foto de prospecto
                        try:
                            id_prosp = int(row["codigo"].replace("DIST-", ""))
                            prosp_path = os.path.join(BASE_DIR, f"uploads/prospectos/prospecto_{id_prosp}.jpg")
                            if os.path.isfile(prosp_path):
                                abs_path = prosp_path
                        except Exception:
                            pass
                except Exception:
                    pass
            finally:
                cur.close()
                conn.close()
        except Exception:
            pass

    if not os.path.isfile(abs_path):
        return error_response(f"No existe foto registrada para el punto de venta {id_pdv}", 404)

    return send_file(abs_path)
