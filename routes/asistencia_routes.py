from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.asistencia_service import AsistenciaService
from utils.response import error_response, success_response

asistencia_bp = Blueprint("asistencias", __name__)


# ── 1. Resumen de Asistencias del Día ────────────────────────────────────────
@asistencia_bp.route("/api/asistencias/resumen", methods=["GET"])
@jwt_required()
def obtener_resumen():
    service = AsistenciaService()
    data, message, http_code = service.obtener_resumen()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 2. Asistencias Recientes ─────────────────────────────────────────────────
@asistencia_bp.route("/api/asistencias/recientes", methods=["GET"])
@jwt_required()
def obtener_recientes():
    limite = request.args.get("limite", default=10, type=int)

    service = AsistenciaService()
    data, message, http_code = service.obtener_recientes(limite=limite)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 3. Lista de Colaboradores con Asistencia ─────────────────────────────────
@asistencia_bp.route("/api/asistencias/colaboradores", methods=["GET"])
@jwt_required()
def obtener_colaboradores():
    service = AsistenciaService()
    data, message, http_code = service.obtener_colaboradores()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 4. Historial de Turnos de un Colaborador ─────────────────────────────────
@asistencia_bp.route("/api/asistencias/historial/<int:idUsuario>", methods=["GET"])
@jwt_required()
def obtener_historial(idUsuario):
    service = AsistenciaService()
    data, message, http_code = service.obtener_historial(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 5. Marcar Asistencia (Ingreso / Salida) ──────────────────────────────────
@asistencia_bp.route("/api/asistencias/marcar", methods=["POST"])
@jwt_required()
def marcar_asistencia():
    payload = request.get_json() or {}
    service = AsistenciaService()
    data, message, http_code = service.registrar_asistencia(payload)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 6. Enviar Justificación de Inasistencia / Tardanza ───────────────────────
@asistencia_bp.route("/api/asistencias/justificar", methods=["POST"])
@jwt_required()
def registrar_justificacion():
    payload = request.get_json() or {}
    service = AsistenciaService()
    data, message, http_code = service.registrar_justificacion(payload)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


# ── 7. Obtener Última Justificación de un Usuario ────────────────────────────
@asistencia_bp.route("/api/asistencias/justificacion/<int:idUsuario>", methods=["GET"])
@jwt_required()
def obtener_justificacion_usuario(idUsuario):
    service = AsistenciaService()
    data, message, http_code = service.obtener_justificacion_usuario(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

# ── 7. Obtener Última asistencia de un Usuario ────────────────────────────
@asistencia_bp.route('/api/asistencias/ultima', methods=['GET'])

def obtener_ultima_asistencia():
    try:
        # Obtener el idUsuario (desde token JWT autenticado o parámetro query)
        # id_usuario = current_user.get('idUsuario')
        id_usuario = request.args.get('idUsuario', type=int)
        
        if not id_usuario:
            return jsonify({
                "status": False,
                "message": "Falta el idUsuario en la petición",
                "data": None
            }), 400

        ultima = asistencia_service.obtener_ultima_asistencia(id_usuario)

        if ultima:
            return jsonify({
                "status": True,
                "message": "Última asistencia obtenida correctamente",
                "data": ultima
            }), 200
        else:
            return jsonify({
                "status": True,
                "message": "No hay marcas de asistencia registradas",
                "data": None
            }), 200

    except Exception as e:
        return jsonify({
            "status": False,
            "message": f"Error en el servidor: {str(e)}",
            "data": None
        }), 500


# ── 7. Revisar justificación de un Usuario ────────────────────────────
@asistencia_bp.route('/api/asistencias/justificacion/revisar', methods=['POST'])

def revisar_justificacion():
    try:
        data = request.get_json() or {}
        
        # Parámetros que envía Android Studio (RevisionJustificacionRequest)
        id_usuario = data.get('idUsuario')
        estado_nuevo = data.get('estadoNuevo') # "APROBADA" o "RECHAZADA"
        comentario_admin = data.get('comentarioAdmin', '')
        
        # ID del Administrador que está revisando (obtenido del token o body)
        id_revisor = data.get('idRevisor', 1) 

        if not id_usuario or not estado_nuevo:
            return jsonify({
                "status": False,
                "message": "Faltan datos obligatorios (idUsuario, estadoNuevo)",
                "data": None
            }), 400

        exito = asistencia_service.revisar_justificacion(
            id_usuario_colaborador=id_usuario,
            estado_nuevo=estado_nuevo,
            comentario_admin=comentario_admin,
            id_revisor=id_revisor
        )

        if exito:
            return jsonify({
                "status": True,
                "message": f"Justificación {estado_nuevo.lower()} exitosamente",
                "data": None
            }), 200
        else:
            return jsonify({
                "status": False,
                "message": "No se encontró una justificación pendiente para este usuario",
                "data": None
            }), 404

    except ValueError as ve:
        return jsonify({
            "status": False,
            "message": str(ve),
            "data": None
        }), 400
    except Exception as e:
        return jsonify({
            "status": False,
            "message": f"Error en el servidor: {str(e)}",
            "data": None
        }), 500