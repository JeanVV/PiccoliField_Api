from flask import Blueprint, jsonify, request
from services.asistencia_service import AsistenciaService

asistencia_bp = Blueprint('asistencia_bp', __name__)
asistencia_service = AsistenciaService()

@asistencia_bp.route('/resumen', methods=['GET'])
def obtener_resumen():
    resultado = asistencia_service.obtener_resumen()
    return jsonify(resultado), 200

@asistencia_bp.route('/recientes', methods=['GET'])
def obtener_recientes():
    limite = request.args.get('limite', default=10, type=int)
    resultado = asistencia_service.obtener_recientes(limite)
    return jsonify(resultado), 200

@asistencia_bp.route('/colaboradores', methods=['GET'])
def obtener_colaboradores():
    resultado = asistencia_service.obtener_colaboradores()
    return jsonify(resultado), 200

@asistencia_bp.route('/detalle/<int:idUsuario>', methods=['GET'])
def obtener_detalle(idUsuario):
    resultado = asistencia_service.obtener_detalle(idUsuario)
    if resultado.get("data"):
        return jsonify(resultado), 200
    return jsonify(resultado), 404

@asistencia_bp.route('/historial/<int:idUsuario>', methods=['GET'])
def obtener_historial(idUsuario):
    resultado = asistencia_service.obtener_historial(idUsuario)
    return jsonify(resultado), 200

@asistencia_bp.route('/evidencias/<int:idAsistencia>', methods=['GET'])
def obtener_evidencias(idAsistencia):
    resultado = asistencia_service.obtener_evidencias(idAsistencia)
    return jsonify(resultado), 200