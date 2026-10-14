from flask import Blueprint, jsonify
from services.asistencia_service import AsistenciaService

asistencia_bp = Blueprint('asistencia', __name__, url_prefix='/api/asistencias')
asistencia_service = AsistenciaService()

@asistencia_bp.route('/resumen', methods=['GET'])
def obtener_resumen_asistencias():
    """
    Obtiene el resumen de asistencias del día actual
    GET /api/asistencias/resumen
    """
    try:
        resumen = asistencia_service.obtener_resumen_hoy()
        return jsonify({
            'success': True,
            'data': resumen
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@asistencia_bp.route('/recientes', methods=['GET'])
def obtener_asistencias_recientes():
    """
    Obtiene las últimas asistencias registradas
    GET /api/asistencias/recientes
    """
    try:
        recientes = asistencia_service.obtener_ultimas_asistencias(limite=10)
        return jsonify({
            'success': True,
            'data': recientes
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@asistencia_bp.route('/colaboradores', methods=['GET'])
def obtener_colaboradores_con_asistencia():
    """
    Obtiene todos los colaboradores con su último estado de asistencia
    GET /api/asistencias/colaboradores
    """
    try:
        colaboradores = asistencia_service.obtener_colaboradores_con_asistencia()
        return jsonify({
            'success': True,
            'data': colaboradores
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500