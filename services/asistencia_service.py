from repositories.asistencia_repository import AsistenciaRepository
from datetime import datetime

class AsistenciaService:
    def __init__(self):
        self.repository = AsistenciaRepository()
    
    def obtener_resumen_hoy(self):
        """Calcula el resumen de asistencias de hoy"""
        hoy = datetime.now().date()
        
        total = self.repository.contar_asistencias_hoy(hoy)
        a_tiempo = self.repository.contar_por_estado(hoy, 'A_TIEMPO')
        tardanzas = self.repository.contar_por_estado(hoy, 'TARDANZA')
        faltas = self.repository.contar_por_estado(hoy, 'FALTA')
        
        presentes = a_tiempo + tardanzas
        porcentaje = (presentes * 100 // total) if total > 0 else 0
        
        return {
            'porcentaje': porcentaje,
            'presentes': presentes,
            'total': total,
            'aTiempo': a_tiempo,
            'tardanzas': tardanzas
        }
    
    def obtener_ultimas_asistencias(self, limite=10):
        """Obtiene las últimas asistencias registradas"""
        return self.repository.obtener_ultimas(limite)
    
    def obtener_colaboradores_con_asistencia(self):
        """Obtiene todos los usuarios con su último registro de asistencia"""
        return self.repository.obtener_colaboradores_con_ultimo_registro()