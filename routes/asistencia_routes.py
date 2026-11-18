from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from services.asistencia_service import AsistenciaService
from utils.response import error_response, success_response

asistencia_bp = Blueprint("asistencias", __name__)
asistencia_service = AsistenciaService()


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
@asistencia_bp.route("/justificar", methods=["POST"])
@jwt_required(optional=True)
def registrar_justificacion():
    data = request.get_json() or {}
    id_usuario = data.get("idUsuario")
    motivo = data.get("motivo")
    descripcion = data.get("descripcion") or data.get("detalle")
    fecha = data.get("fecha")
    ruta_sustento = data.get("ruta_sustento") or data.get("fotoSustento")

    resultado, message, http_code = asistencia_service.registrar_justificacion(
        payload_or_id_usuario=id_usuario,
        motivo=motivo,
        descripcion=descripcion,
        fecha=fecha,
        ruta_sustento=ruta_sustento
    )

    if resultado is None:
        return error_response(message, http_code)

    return success_response(resultado, message, http_code)


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
@asistencia_bp.route("/api/asistencias/ultima", methods=["GET"])
def obtener_ultima_asistencia():
    try:
        # Obtener el idUsuario (desde token JWT autenticado o parámetro query)
        # id_usuario = current_user.get('idUsuario')
        id_usuario = request.args.get("idUsuario", type=int)

        if not id_usuario:
            return (
                jsonify(
                    {
                        "status": False,
                        "message": "Falta el idUsuario en la petición",
                        "data": None,
                    }
                ),
                400,
            )

        ultima = asistencia_service.obtener_ultima_asistencia(id_usuario)

        if ultima:
            return (
                jsonify(
                    {
                        "status": True,
                        "message": "Última asistencia obtenida correctamente",
                        "data": ultima,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": True,
                        "message": "No hay marcas de asistencia registradas",
                        "data": None,
                    }
                ),
                200,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": False,
                    "message": f"Error en el servidor: {str(e)}",
                    "data": None,
                }
            ),
            500,
        )


# ── 7. Revisar justificación de un Usuario ────────────────────────────
@asistencia_bp.route("/api/asistencias/justificacion/revisar", methods=["POST"])
@asistencia_bp.route("/justificacion/revisar", methods=["POST"])
def revisar_justificacion():
    try:
        data = request.get_json() or {}

        # Parámetros (compatibles con Postman y Android Studio)
        id_usuario = data.get("idUsuario")
        id_asistencias = data.get("idAsistencias") or data.get("id_asistencias")
        id_revisor = data.get("idRevisor", 1)
        estado = data.get("estado") or data.get("estadoNuevo")  # "APROBADA" o "RECHAZADA"
        comentario = data.get("comentarioRevision") or data.get("comentarioAdmin") or ""

        if (not id_usuario and not id_asistencias) or not estado:
            return (
                jsonify(
                    {
                        "status": False,
                        "message": "Faltan datos obligatorios (idUsuario o idAsistencias, estado)",
                        "data": None,
                    }
                ),
                400,
            )

        exito = asistencia_service.revisar_justificacion(
            id_usuario=id_usuario,
            id_revisor=id_revisor,
            estado=estado,
            comentario=comentario,
            id_asistencias=id_asistencias,
        )

        if exito:
            return (
                jsonify(
                    {
                        "status": True,
                        "message": "Revisión registrada correctamente",
                        "data": None,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": False,
                        "message": "No se encontró la justificación a revisar",
                        "data": None,
                    }
                ),
                400,
            )

    except ValueError as ve:
        return jsonify({"status": False, "message": str(ve), "data": None}), 400
    except Exception as e:
        return (
            jsonify(
                {
                    "status": False,
                    "message": f"Error en el servidor: {str(e)}",
                    "data": None,
                }
            ),
            500,
        )


# ── 8. Notificación Push de Resumen Diario de Asistencias (10:30 AM / Manual) ────
@asistencia_bp.route("/api/asistencias/notificar-resumen", methods=["GET", "POST"])
def notificar_resumen():
    """
    Dispara manualmente el envío de la Notificación Push del Resumen Diario de Asistencias
    a todos los Administradores y Supervisores registrados en USUARIO_DISPOSITIVO.
    Habilitado para pruebas manuales en Postman (GET o POST).
    """
    data, message, http_code = asistencia_service.enviar_notificacion_resumen_diario()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

