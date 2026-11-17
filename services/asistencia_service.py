from datetime import datetime
from database import get_connection
from repositories.asistencia_repository import AsistenciaRepository
from services.fcm_service import FCMService


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

    def obtener_ultima_asistencia(self, id_usuario):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            return repository.obtener_ultima_asistencia(id_usuario)
        finally:
            connection.close()

    def revisar_justificacion(self, id_usuario_colaborador, estado_nuevo, comentario_admin, id_revisor):
        if not id_usuario_colaborador:
            raise ValueError("El idUsuario del colaborador es obligatorio.")
        if not estado_nuevo:
            raise ValueError("El estadoNuevo ('APROBADA'/'RECHAZADA') es obligatorio.")

        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            return repository.revisar_justificacion(
                id_usuario_colaborador, 
                estado_nuevo, 
                comentario_admin, 
                id_revisor
            )
        finally:
            connection.close()

    # ── ENVÍO DE NOTIFICACIÓN PUSH DE RESUMEN DIARIO (10:30 AM) ─────────────
    def enviar_notificacion_resumen_diario(self):
        """
        Consulta las métricas de asistencia del día, obtiene los tokens FCM
        de Administradores y Supervisores, y envía la notificación push correspondiente.
        """
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)

            # 1. Consultar métricas del día con la SQL especificada
            row = repository.get_resumen_diario()
            total = int(row.get("total") or 0) if row else 0
            presentes = int(row.get("presentes") or 0) if row else 0
            aTiempo = int(row.get("aTiempo") or 0) if row else 0
            tardanzas = int(row.get("tardanzas") or 0) if row else 0
            faltas = int(row.get("faltas") or 0) if row else 0

            # 2. Obtener tokens FCM de USUARIO_DISPOSITIVO para Administradores y Supervisores
            dispositivos = repository.get_tokens_administradores_supervisores()

            # 3. Construir mensaje Push FCM y Data Payload
            titulo = "Resumen de Asistencias del Día"
            body = f"Hoy: {presentes}/{total} presentes ({aTiempo} a tiempo, {tardanzas} tardanzas, {faltas} faltas)."
            data_payload = {
                "tipo": "RESUMEN_ASISTENCIA",
                "title": titulo,
                "body": body,
                "total": str(total),
                "presentes": str(presentes),
                "aTiempo": str(aTiempo),
                "tardanzas": str(tardanzas),
                "faltas": str(faltas),
            }

            if not dispositivos:
                print("[RESUMEN_DIARIO] No se encontraron dispositivos activos para Administradores o Supervisores.")
                return {
                    "metricas": {
                        "total": total,
                        "presentes": presentes,
                        "aTiempo": aTiempo,
                        "tardanzas": tardanzas,
                        "faltas": faltas,
                    },
                    "tokens_encontrados": 0,
                    "notificaciones_enviadas": 0,
                    "fallidas": 0,
                    "mensaje": body,
                }, "No se encontraron tokens activos para Administradores o Supervisores", 200

            # 4. Enviar notificación FCM a cada token único
            tokens_procesados = set()
            enviados = 0
            fallidos = 0
            detalles_envio = []

            for d in dispositivos:
                token = d.get("fcm_token")
                id_usuario = d.get("idUsuario")
                if not token or token in tokens_procesados:
                    continue
                tokens_procesados.add(token)

                ok, det = FCMService.enviar_a_token(
                    fcm_token=token,
                    titulo=titulo,
                    mensaje=body,
                    data=data_payload,
                )

                if ok:
                    enviados += 1
                else:
                    fallidos += 1

                detalles_envio.append({
                    "idUsuario": id_usuario,
                    "rol": d.get("rol"),
                    "token": f"{token[:12]}...",
                    "status": "ENVIADO" if ok else "FALLIDO",
                    "detalle": det,
                })

                # Registrar en NOTIFICACIONES_LOG
                FCMService._guardar_log(
                    idUsuario=id_usuario,
                    tipo="RESUMEN_ASISTENCIA",
                    referencia="RESUMEN-DIARIO",
                    mensaje=body,
                    resultado=det,
                )

            resultado = {
                "metricas": {
                    "total": total,
                    "presentes": presentes,
                    "aTiempo": aTiempo,
                    "tardanzas": tardanzas,
                    "faltas": faltas,
                },
                "tokens_encontrados": len(tokens_procesados),
                "notificaciones_enviadas": enviados,
                "fallidas": fallidos,
                "mensaje_enviado": {
                    "title": titulo,
                    "body": body,
                    "data": data_payload,
                },
                "detalles": detalles_envio,
            }

            return resultado, "Notificación de resumen diario enviada correctamente", 200
        except Exception as e:
            print(f"[RESUMEN_DIARIO] Error al enviar notificación de resumen diario: {e}")
            return None, f"Error al enviar notificación de resumen diario: {str(e)}", 500
        finally:
            connection.close()


def enviar_notificacion_resumen_diario():
    """
    Función helper a nivel de módulo para invocación directa desde el scheduler o cron.
    """
    service = AsistenciaService()
    return service.enviar_notificacion_resumen_diario()
