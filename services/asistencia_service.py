from datetime import datetime
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
        except Exception as e:
            return None, f"Error al obtener resumen: {str(e)}", 500
        finally:
            connection.close()

    # ── GET /api/asistencias/recientes ───────────────────────────────────────
    def obtener_recientes(self, limite=10):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            asistencias = repository.get_recientes(limite)
            return asistencias, "Asistencias recientes obtenidas", 200
        except Exception as e:
            return None, f"Error al obtener recientes: {str(e)}", 500
        finally:
            connection.close()

    # ── GET /api/asistencias/colaboradores ───────────────────────────────────
    def obtener_colaboradores(self):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            colaboradores = repository.get_colaboradores()
            return colaboradores, "Colaboradores obtenidos correctamente", 200
        except Exception as e:
            return None, f"Error al obtener colaboradores: {str(e)}", 500
        finally:
            connection.close()

    # ── GET /api/asistencias/historial/<idUsuario> ────────────────────────────
    def obtener_historial(self, idUsuario):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            historial = repository.get_historial(idUsuario)
            return historial, "Historial obtenido correctamente", 200
        except Exception as e:
            return None, f"Error al obtener historial: {str(e)}", 500
        finally:
            connection.close()

    # ── POST /api/asistencias/marcar ─────────────────────────────────────────
    def registrar_asistencia(self, payload):
        connection = get_connection()
        try:
            id_usuario = payload.get("idUsuario")
            tipo = payload.get("tipo", "INGRESO")
            latitud = payload.get("latitud", 0.0)
            longitud = payload.get("longitud", 0.0)
            fecha_hora_disp = payload.get("fechaHoraDispositivo") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not id_usuario:
                return None, "El idUsuario es requerido", 400

            repository = AsistenciaRepository(connection)
            resultado = repository.marcar_asistencia(
                id_usuario=id_usuario,
                tipo=tipo,
                latitud=latitud,
                longitud=longitud,
                fecha_hora_disp=fecha_hora_disp
            )

            return resultado, "Asistencia registrada correctamente", 201
        except Exception as e:
            return None, f"Error al marcar asistencia: {str(e)}", 500
        finally:
            connection.close()

    # ── POST /api/asistencias/justificar ──────────────────────────────────────
    def registrar_justificacion(self, payload):
        connection = get_connection()
        try:
            id_usuario = payload.get("idUsuario")
            motivo = payload.get("motivo")
            descripcion = payload.get("descripcion") or payload.get("detalle")
            fecha = payload.get("fecha") or datetime.now().strftime("%Y-%m-%d")

            if not id_usuario or not motivo or not descripcion:
                return None, "idUsuario, motivo y descripción son requeridos", 400

            repository = AsistenciaRepository(connection)
            resultado = repository.registrar_justificacion(
                id_usuario=id_usuario,
                motivo=motivo,
                descripcion=descripcion,
                fecha=fecha
            )

            return resultado, "Justificación registrada exitosamente", 201
        except Exception as e:
            return None, f"Error al registrar justificación: {str(e)}", 500
        finally:
            connection.close()

    # ── GET /api/asistencias/justificacion/<idUsuario> ────────────────────────
    def obtener_justificacion_usuario(self, idUsuario):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            justificacion = repository.get_justificacion_usuario(idUsuario)
            if not justificacion:
                return {}, "No hay justificaciones para este usuario", 200
            return justificacion, "Justificación obtenida correctamente", 200
        except Exception as e:
            return None, f"Error al consultar justificación: {str(e)}", 500
        finally:
            connection.close()