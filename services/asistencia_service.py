from database import get_connection
from repositories.asistencia_repository import AsistenciaRepository


class AsistenciaService:

    # ── GET /api/asistencias/resumen ─────────────────────────────────────────
    def obtener_resumen(self):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            row = repository.get_resumen()

            total = row.get("total", 0) if row else 0
            presentes = int(row.get("presentes", 0)) if row and row.get("presentes") else 0
            a_tiempo = int(row.get("aTiempo", 0)) if row and row.get("aTiempo") else 0
            tardanzas = int(row.get("tardanzas", 0)) if row and row.get("tardanzas") else 0

            porcentaje = round((presentes / total) * 100) if total > 0 else 0

            data = {
                "porcentaje": porcentaje,
                "presentes": presentes,
                "total": total,
                "aTiempo": a_tiempo,
                "tardanzas": tardanzas,
            }

            return data, "Resumen obtenido correctamente", 200
        finally:
            connection.close()

    # ── GET /api/asistencias/recientes ───────────────────────────────────────
    def obtener_recientes(self, limite=10):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            asistencias = repository.get_recientes(limite)
            return asistencias, "Asistencias recientes obtenidas", 200
        finally:
            connection.close()

    # ── GET /api/asistencias/colaboradores ───────────────────────────────────
    def obtener_colaboradores(self):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            colaboradores = repository.get_colaboradores()
            return colaboradores, "Colaboradores obtenidos correctamente", 200
        finally:
            connection.close()

    # ── GET /api/asistencias/detalle/<idUsuario> ──────────────────────────────
    def obtener_detalle(self, idUsuario):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            asistencia = repository.get_detalle_usuario(idUsuario)

            if asistencia is None:
                return None, "No se encontró asistencia de hoy para este usuario", 404

            return asistencia, "Detalle obtenido correctamente", 200
        finally:
            connection.close()

    # ── GET /api/asistencias/historial/<idUsuario> ────────────────────────────
    def obtener_historial(self, idUsuario):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            historial = repository.get_historial(idUsuario)
            return historial, "Historial obtenido correctamente", 200
        finally:
            connection.close()

    # ── GET /api/asistencias/evidencias/<idAsistencia> ───────────────────────
    def obtener_evidencias(self, idAsistencia):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            evidencias = repository.get_evidencias(idAsistencia)
            return evidencias, "Evidencias obtenidas correctamente", 200
        finally:
            connection.close()  

    def marcarAsistenciaPersonal(self, idUsuario, Tipo): 
        connection = get_connection()
        try: 
            repository = AsistenciaRepository(connection)  
            if repository.verificarHorarioTurnoPersonal(idUsuario) == True:
                return None, "Usuario no tiene horario de turno", 404
            
            repository.marcarAsistenciaPersonal(idUsuario, Tipo) 
            asistencia = repository.asistenciaPersonal(idUsuario, Tipo)
            return asistencia, "Asistencia marcada correctamente", 202
        finally: 
            connection.close()
