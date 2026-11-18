import os
import time
import base64
import threading
from datetime import datetime
from database import get_connection
from repositories.asistencia_repository import AsistenciaRepository, get_now_peru
from services.fcm_service import FCMService

_idempotency_cache = {}
_idempotency_lock = threading.Lock()
IDEMPOTENCY_TTL_SECONDS = 600  # 10 minutos de ventana de idempotencia


def guardar_foto_sustento(base64_str, id_usuario):
    if not base64_str or len(str(base64_str)) < 100:
        return base64_str  # Si ya es una URL o ruta corta, la devuelve tal cual

    try:
        raw_b64 = str(base64_str)
        # Limpiar prefijo data:image si existiera
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]

        image_data = base64.b64decode(raw_b64)
        folder = os.path.join("uploads", "justificaciones")
        os.makedirs(folder, exist_ok=True)

        filename = f"sustento_{id_usuario}_{int(datetime.now().timestamp())}.jpg"
        filepath = os.path.join(folder, filename)

        with open(filepath, "wb") as f:
            f.write(image_data)

        # Copia de compatibilidad en static/uploads/justificaciones
        try:
            static_folder = os.path.join("static", "uploads", "justificaciones")
            os.makedirs(static_folder, exist_ok=True)
            with open(os.path.join(static_folder, filename), "wb") as sf:
                sf.write(image_data)
        except Exception:
            pass

        # Retorna la ruta relativa corta para guardar en varchar(255)
        return f"uploads/justificaciones/{filename}"
    except Exception as e:
        print(f"[ERROR AL GUARDAR FOTO SUSTENTO]: {str(e)}")
        return None


class AsistenciaService:

    # ── GET /api/asistencias/resumen ─────────────────────────────────────────
    def obtener_resumen(self):
        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            row = repository.get_resumen()

            total = int(row.get("total", 0)) if row and row.get("total") else 0
            presentes = int(row.get("presentes", 0)) if row and row.get("presentes") else 0
            a_tiempo = int(row.get("aTiempo", 0)) if row and row.get("aTiempo") else 0
            tardanzas = int(row.get("tardanzas", 0)) if row and row.get("tardanzas") else 0
            faltas = int(row.get("faltas", 0)) if row and row.get("faltas") else 0
            sin_marcar = int(row.get("sinMarcar", 0)) if row and row.get("sinMarcar") else 0

            porcentaje = row.get("porcentaje", round((presentes / total) * 100) if total > 0 else 0)

            data = {
                "porcentaje": porcentaje,
                "presentes": presentes,
                "total": total,
                "aTiempo": a_tiempo,
                "tardanzas": tardanzas,
                "faltas": faltas,
                "sinMarcar": sin_marcar,
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
    def marcar_asistencia(self, payload_or_id_usuario, tipo=None, latitud=None, longitud=None, direccion=None, sede=None, fecha_hora_disp=None, operation_id=None, **kwargs):
        op_id = operation_id or kwargs.get("operation_id")
        if isinstance(payload_or_id_usuario, dict):
            payload = payload_or_id_usuario
            id_usuario = payload.get("idUsuario")
            tipo = payload.get("tipo")
            latitud = payload.get("latitud")
            longitud = payload.get("longitud")
            direccion = payload.get("direccion") or payload.get("ubicacion")
            sede = payload.get("sede") or payload.get("nombreSede")
            fecha_hora_disp = payload.get("fechaHoraDispositivo") or payload.get("fecha_hora_disp")
            if not op_id:
                op_id = payload.get("operationId") or payload.get("x_operation_id") or payload.get("X-Operation-Id")
        else:
            id_usuario = payload_or_id_usuario

        # 1. Validar Idempotencia con X-Operation-Id
        if op_id:
            cache_key = f"{id_usuario}_{op_id}"
            with _idempotency_lock:
                now_ts = time.time()
                expired = [k for k, v in _idempotency_cache.items() if now_ts - v.get("timestamp", 0) > IDEMPOTENCY_TTL_SECONDS]
                for k in expired:
                    del _idempotency_cache[k]

                if cache_key in _idempotency_cache:
                    cached = _idempotency_cache[cache_key]
                    print(f"[IDEMPOTENCIA] Retornando respuesta almacenada para X-Operation-Id: {op_id}")
                    return cached["data"], cached["message"], cached["code"]

        if not id_usuario or not tipo:
            return None, "idUsuario y tipo son requeridos", 400

        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            resultado = repository.marcar_asistencia(
                id_usuario=id_usuario,
                tipo=tipo,
                latitud=latitud,
                longitud=longitud,
                direccion=direccion,
                sede=sede,
                fecha_hora_disp=fecha_hora_disp
            )
            msg = resultado.get("mensaje") or resultado.get("message") or "Asistencia registrada correctamente"
            codigo_http = 200 if resultado.get("yaRegistrado") else 201

            # Guardar respuesta en caché de idempotencia si se envió X-Operation-Id
            if op_id and resultado is not None:
                with _idempotency_lock:
                    _idempotency_cache[f"{id_usuario}_{op_id}"] = {
                        "data": resultado,
                        "message": msg,
                        "code": codigo_http,
                        "timestamp": time.time()
                    }

            return resultado, msg, codigo_http
        except Exception as e:
            return None, f"Error al marcar asistencia: {str(e)}", 500
        finally:
            connection.close()

    registrar_asistencia = marcar_asistencia

    # ── POST /api/asistencias/justificar ──────────────────────────────────────
    def registrar_justificacion(self, payload_or_id_usuario, motivo=None, descripcion=None, fecha=None, ruta_sustento=None, operation_id=None, **kwargs):
        op_id = operation_id or kwargs.get("operation_id")
        if isinstance(payload_or_id_usuario, dict):
            payload = payload_or_id_usuario
            id_usuario = payload.get("idUsuario")
            motivo = payload.get("motivo")
            descripcion = payload.get("descripcion") or payload.get("detalle")
            fecha = payload.get("fecha") or get_now_peru().strftime("%Y-%m-%d")
            ruta_sustento = payload.get("fotoSustentoBase64") or payload.get("ruta_sustento") or payload.get("fotoSustento")
            if not op_id:
                op_id = payload.get("operationId") or payload.get("x_operation_id") or payload.get("X-Operation-Id")
        else:
            id_usuario = payload_or_id_usuario
            fecha = fecha or get_now_peru().strftime("%Y-%m-%d")

        # 1. Validar Idempotencia con X-Operation-Id si se envió
        if op_id:
            cache_key = f"just_{id_usuario}_{op_id}"
            with _idempotency_lock:
                now_ts = time.time()
                if cache_key in _idempotency_cache and (now_ts - _idempotency_cache[cache_key].get("timestamp", 0) <= IDEMPOTENCY_TTL_SECONDS):
                    cached = _idempotency_cache[cache_key]
                    print(f"[IDEMPOTENCIA JUSTIFICACION] Retornando respuesta almacenada para X-Operation-Id: {op_id}")
                    return cached["data"], cached["message"], cached["code"]

        if not id_usuario or not motivo or not descripcion:
            return None, "idUsuario, motivo y descripción son requeridos", 400

        # Guardar imagen en base64 en archivo y guardar sólo la ruta corta
        if ruta_sustento:
            ruta_sustento = guardar_foto_sustento(ruta_sustento, id_usuario)

        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            resultado = repository.registrar_justificacion(
                id_usuario=id_usuario,
                motivo=motivo,
                descripcion=descripcion,
                fecha=fecha,
                ruta_sustento=ruta_sustento
            )

            # Guardar en caché de idempotencia si se proporcionó operation_id
            if op_id and resultado is not None:
                with _idempotency_lock:
                    _idempotency_cache[f"just_{id_usuario}_{op_id}"] = {
                        "data": resultado,
                        "message": "Justificación registrada exitosamente",
                        "code": 201,
                        "timestamp": time.time()
                    }

            # Notificar en tiempo real a Administradores y Supervisores vía Push FCM (hilo daemon)
            self._notificar_justificacion_en_segundo_plano(id_usuario, motivo)

            return resultado, "Justificación registrada exitosamente", 201
        except Exception as e:
            return None, f"Error al registrar justificación: {str(e)}", 500
        finally:
            connection.close()

    @classmethod
    def _notificar_justificacion_en_segundo_plano(cls, id_usuario, motivo):
        """
        Envía en segundo plano (daemon thread) la Notificación Push de nueva justificación
        a todos los Administradores y Supervisores registrados.
        """
        def _job():
            try:
                conn = get_connection()
                try:
                    repo = AsistenciaRepository(conn)
                    # 1. Obtener nombre completo del colaborador (nombres + apePaterno)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT nombres, apePaterno FROM USUARIOS WHERE idUsuario = %s LIMIT 1",
                        (id_usuario,)
                    )
                    user_row = cursor.fetchone()
                    cursor.close()

                    if user_row:
                        nombres = (user_row.get("nombres") or "").strip()
                        apePaterno = (user_row.get("apePaterno") or "").strip()
                        nombre_colaborador = f"{nombres} {apePaterno}".strip() or "Un colaborador"
                    else:
                        nombre_colaborador = "Un colaborador"

                    # 2. Obtener tokens FCM de USUARIO_DISPOSITIVO para Administradores y Supervisores
                    dispositivos = repo.get_tokens_administradores_supervisores()
                finally:
                    conn.close()

                if not dispositivos:
                    print("[FCM Justificación] No se encontraron dispositivos activos para Administradores o Supervisores.")
                    return

                # 3. Construir mensaje Push FCM y Data Payload
                titulo = "📩 Nueva Justificación Recibida"
                body = f"{nombre_colaborador} envió un justificativo de {motivo} para su revisión."
                data_payload = {
                    "tipo": "JUSTIFICACION_RECIBIDA",
                    "title": titulo,
                    "body": body,
                    "idUsuario": str(id_usuario)
                }

                # 4. Enviar notificación FCM a cada token único
                tokens_procesados = set()
                for d in dispositivos:
                    token = d.get("fcm_token")
                    id_destinatario = d.get("idUsuario")
                    if not token or token in tokens_procesados:
                        continue
                    tokens_procesados.add(token)

                    ok, det = FCMService.enviar_a_token(
                        fcm_token=token,
                        titulo=titulo,
                        mensaje=body,
                        data=data_payload
                    )

                    # Registrar en NOTIFICACIONES_LOG
                    FCMService._guardar_log(
                        idUsuario=id_destinatario,
                        tipo="JUSTIFICACION_RECIBIDA",
                        referencia=f"JUST-{id_usuario}",
                        mensaje=body,
                        resultado=det
                    )
            except Exception as e:
                print(f"[FCM Justificación] Error en job de notificación en segundo plano: {e}")

        t = threading.Thread(target=_job, daemon=True)
        t.start()

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

    def revisar_justificacion(self, id_usuario=None, id_revisor=1, estado="APROBADA", comentario="", id_asistencias=None, **kwargs):
        id_user = id_usuario if id_usuario is not None else kwargs.get("id_usuario_colaborador")
        id_asist = id_asistencias if id_asistencias is not None else kwargs.get("idAsistencias")
        est = estado if estado is not None else kwargs.get("estado_nuevo", "APROBADA")
        com = comentario if comentario is not None else kwargs.get("comentario_admin", "")
        rev = id_revisor if id_revisor is not None else kwargs.get("id_revisor", 1)

        if not id_user and not id_asist:
            raise ValueError("El idUsuario o idAsistencias es obligatorio.")
        if not est:
            raise ValueError("El estado ('APROBADA'/'RECHAZADA') es obligatorio.")

        connection = get_connection()
        try:
            repository = AsistenciaRepository(connection)
            return repository.revisar_justificacion(
                id_usuario=id_user,
                id_revisor=rev,
                estado=est,
                comentario=com,
                id_asistencias=id_asist
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
