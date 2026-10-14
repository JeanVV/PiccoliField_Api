from flask import Blueprint, jsonify, request
from services.asistencia_service import AsistenciaService

asistencia_bp = Blueprint('asistencia', __name__, url_prefix='/api/asistencias')
asistencia_service = AsistenciaService()

@asistencia_bp.route('/resumen', methods=['GET'])
def obtener_resumen():
    try:
        resumen = asistencia_service.obtener_resumen_hoy()
        return jsonify({'success': True, 'data': resumen}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@asistencia_bp.route('/recientes', methods=['GET'])
def obtener_recientes():
    try:
        limite = request.args.get('limite', 10, type=int)
        recientes = asistencia_service.obtener_ultimas_asistencias(limite)
        return jsonify({'success': True, 'data': recientes}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@asistencia_bp.route('/colaboradores', methods=['GET'])
def obtener_colaboradores():
    try:
        colaboradores = asistencia_service.obtener_colaboradores_con_asistencia()
        return jsonify({'success': True, 'data': colaboradores}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@asistencia_bp.route('/detalle/<int:id_usuario>', methods=['GET'])
def obtener_detalle(id_usuario):
    try:
        detalle = asistencia_service.obtener_detalle_usuario(id_usuario)
        return jsonify({'success': True, 'data': detalle}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@asistencia_bp.route('/historial/<int:id_usuario>', methods=['GET'])
def obtener_historial(id_usuario):
    try:
        historial = asistencia_service.obtener_historial_turnos(id_usuario)
        return jsonify({'success': True, 'data': historial}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@asistencia_bp.route('/evidencias/<int:id_asistencia>', methods=['GET'])
def obtener_evidencias(id_asistencia):
    try:
        evidencias = asistencia_service.obtener_evidencias_asistencia(id_asistencia)
        return jsonify({'success': True, 'data': evidencias}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500