from repositories.asistencia_repository import AsistenciaRepository

class AsistenciaService:
    def __init__(self):
        self.repository = AsistenciaRepository()

    def obtener_resumen(self):
        datos = self.repository.get_resumen()
        total = datos.get('total', 0)
        presentes = datos.get('presentes', 0)
        porcentaje = round((presentes / total * 100)) if total > 0 else 0

        return {
            "success": True,
            "message": "Resumen obtenido correctamente",
            "data": {
                "porcentaje": porcentaje,
                "presentes": presentes,
                "total": total,
                "aTiempo": datos.get('aTiempo', 0),
                "tardanzas": datos.get('tardanzas', 0)
            }
        }

    def obtener_recientes(self, limite):
        datos = self.repository.get_recientes(limite)
        return {
            "success": True,
            "message": "Asistencias recientes obtenidas",
            "data": datos
        }

    def obtener_colaboradores(self):
        datos = self.repository.get_colaboradores()
        return {
            "success": True,
            "message": "Colaboradores obtenidos correctamente",
            "data": datos
        }

    def obtener_detalle(self, id_usuario):
        datos = self.repository.get_detalle_usuario(id_usuario)
        if not datos:
            return {
                "success": False,
                "message": "No se encontró asistencia de hoy para este usuario",
                "data": None
            }
            
        return {
            "success": True,
            "message": "Detalle obtenido correctamente",
            "data": datos
        }

    def obtener_historial(self, id_usuario):
        datos = self.repository.get_historial(id_usuario)
        return {
            "success": True,
            "message": "Historial obtenido correctamente",
            "data": datos
        }

    def obtener_evidencias(self, id_asistencia):
        datos = self.repository.get_evidencias(id_asistencia)
        return {
            "success": True,
            "message": "Evidencias obtenidas correctamente",
            "data": datos
        }