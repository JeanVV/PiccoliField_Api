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

    # ── GET /api/asistencias/historial/<idUsuario> ────────────────────────────
    def obtener_historial(self, idUsuario):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            historial = repository.get_historial(idUsuario)
            return historial, "Historial obtenido correctamente", 200
        finally:
            connection.close()

    # ── POST /api/asistencias/marcar ─────────────────────────────────────────
    def registrar_asistencia(self, data):
        id_usuario = data.get("idUsuario")
        tipo = data.get("tipo", "INGRESO").upper()
        latitud = data.get("latitud")
        longitud = data.get("longitud")
        fecha_dispositivo = data.get("fechaHoraDispositivo")

        if not id_usuario:
            return None, "El idUsuario es requerido", 400
        if tipo not in ["INGRESO", "SALIDA"]:
            return None, "El tipo debe ser INGRESO o SALIDA", 400

        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            resultado = repository.marcar_asistencia(
                id_usuario=id_usuario,
                tipo=tipo,
                fecha_hora_dispositivo=fecha_dispositivo,
                latitud=latitud,
                longitud=longitud
            )
            return resultado, f"Marcado de {tipo.lower()} registrado correctamente", 200
        except Exception as e:
            return None, f"Error al registrar asistencia: {str(e)}", 500
        finally:
            connection.close()

    # ── POST /api/asistencias/justificar ──────────────────────────────────────
    def registrar_justificacion(self, data):
        id_usuario = data.get("idUsuario")
        motivo = data.get("motivo")
        descripcion = data.get("descripcion")
        fecha = data.get("fecha")

        if not id_usuario:
            return None, "El idUsuario es requerido", 400
        if not motivo or not descripcion:
            return None, "El motivo y la descripción son requeridos", 400

        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            resultado = repository.registrar_justificacion(
                id_usuario=id_usuario,
                motivo=motivo,
                descripcion=descripcion,
                fecha=fecha
            )
            return resultado, "Justificación registrada correctamente", 200
        except Exception as e:
            return None, f"Error al guardar justificación: {str(e)}", 500
        finally:
            connection.close()

    # ── GET /api/asistencias/justificacion/<idUsuario> ────────────────────────
    def obtener_justificacion(self, idUsuario):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            justificacion = repository.get_justificacion_usuario(idUsuario)
            if not justificacion:
                # Retorna estructura limpia con 200 para que Android no rompa el parsing
                return {
                    "idUsuario": idUsuario,
                    "justificacion": None,
                    "motivoJustificacion": None,
                    "estadoJustificacion": "SIN_REGISTRO"
                }, "Sin justificación registrada", 200

            return justificacion, "Justificación obtenida correctamente", 200
        except Exception as e:
            return None, f"Error al consultar justificación: {str(e)}", 500
        finally:
            connection.close()