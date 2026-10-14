from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from services.asistencia_service import AsistenciaService
from utils.response import error_response, success_response

asistencia_bp = Blueprint("asistencias", __name__)


@asistencia_bp.route("/api/asistencias/resumen", methods=["GET"])
@jwt_required()
def obtener_resumen():
    service = AsistenciaService()
    data, message, http_code = service.obtener_resumen()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/recientes", methods=["GET"])
@jwt_required()
def obtener_recientes():
    limite = request.args.get("limite", default=10, type=int)

    service = AsistenciaService()
    data, message, http_code = service.obtener_recientes(limite=limite)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/colaboradores", methods=["GET"])
@jwt_required()
def obtener_colaboradores():
    service = AsistenciaService()
    data, message, http_code = service.obtener_colaboradores()

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/detalle/<int:idUsuario>", methods=["GET"])
@jwt_required()
def obtener_detalle(idUsuario):
    service = AsistenciaService()
    data, message, http_code = service.obtener_detalle(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/historial/<int:idUsuario>", methods=["GET"])
@jwt_required()
def obtener_historial(idUsuario):
    service = AsistenciaService()
    data, message, http_code = service.obtener_historial(idUsuario)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)


@asistencia_bp.route("/api/asistencias/evidencias/<int:idAsistencia>", methods=["GET"])
@jwt_required()
def obtener_evidencias(idAsistencia):
    service = AsistenciaService()
    data, message, http_code = service.obtener_evidencias(idAsistencia)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

from flask import Blueprint, request, jsonify

# O en tu app.py directamente
@app.route('/api/asistencia/incidencia', methods=['POST'])
def registrar_incidencia():
    try:
        data = request.get_json()
        
        # Extraer parámetros enviados desde Android
        id_usuario = data.get('idUsuario')
        motivo = data.get('motivo')
        descripcion = data.get('descripcion')
        
        # Validación básica de campos requeridos
        if not id_usuario or not motivo:
            return jsonify({
                "status": "error",
                "message": "Faltan datos obligatorios (idUsuario o motivo)"
            }), 400

        # Lógica de negocio / Inserción a BD (Simulado o SQL real)
        # db.ejecutar("INSERT INTO incidencias ...")

        return jsonify({
            "status": "success",
            "message": "Incidencia registrada correctamente"
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500