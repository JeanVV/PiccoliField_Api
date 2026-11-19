import os
import time
import base64
import shutil
import threading
from datetime import datetime
from config import BASE_DIR, Config
from database import get_connection
from repositories.asistencia_repository import AsistenciaRepository, get_now_peru, calcular_estado_asistencia
from services.fcm_service import FCMService

_idempotency_cache = {}
_idempotency_lock = threading.Lock()
IDEMPOTENCY_TTL_SECONDS = 600  # 10 minutos de ventana de idempotencia


def guardar_foto_sustento(base64_str, id_usuario):
    if not base64_str:
        return None

    raw_str = str(base64_str).strip()
    if len(raw_str) < 100 and (raw_str.startswith("uploads/") or raw_str.startswith("http")):
        return raw_str  # Si ya es una ruta corta existente

    try:
        if "base64," in raw_str:
            encoded_data = raw_str.split("base64,", 1)[1]
        elif "," in raw_str:
            encoded_data = raw_str.split(",", 1)[1]
        else:
            encoded_data = raw_str

        image_data = base64.b64decode(encoded_data)
        folder = os.path.join(BASE_DIR, "uploads", "justificaciones")
        os.makedirs(folder, exist_ok=True)

        ts = int(time.time())
        nombre_archivo = f"justif_{id_usuario}_{ts}.jpg"
        filepath = os.path.join(folder, nombre_archivo)

        with open(filepath, "wb") as f:
            f.write(image_data)

        # Copia de compatibilidad en sustento_{id_usuario}_{ts}.jpg y justif_{id_usuario}.jpg
        try:
            ruta_fija = os.path.join(folder, f"justif_{id_usuario}.jpg")
            if filepath != ruta_fija:
                shutil.copyfile(filepath, ruta_fija)
        except Exception:
            pass

        # Retorna la ruta corta para guardar en varchar(255)
        return f"uploads/justificaciones/{nombre_archivo}"
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
            fecha_hora_disp = (
                payload.get("fechaHoraDispositivo")
                or payload.get("fecha_hora_disp")
                or payload.get("hora_dispositivo")
                or payload.get("horaDispositivo")
                or payload.get("fechaHora")
                or payload.get("hora")
            )
            if not op_id:
                op_id = payload.get("operationId") or payload.get("x_operation_id") or payload.get("X-Operation-Id")
        else:
            id_usuario = payload_or_id_usuario
            fecha_hora_disp = (
                fecha_hora_disp
                or kwargs.get("fecha_hora_disp")
                or kwargs.get("fechaHoraDispositivo")
                or kwargs.get("hora_dispositivo")
                or kwargs.get("horaDispositivo")
                or kwargs.get("fechaHora")
                or kwargs.get("hora")
            )

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

            # ── 3. ENVÍO DE NOTIFICACIÓN PUSH A ADMINISTRADORES ─────────────────
            # Encapsulado estrictamente en try-except para que ningún fallo de Firebase
            # afecte el guardado exitoso de la justificación en MySQL.
            try:
                self._notificar_justificacion_administradores()
            except Exception as e_fcm:
                print(f"[FCM JUSTIFICACION ERROR]: Error al procesar notificación Push: {e_fcm}")

            return resultado, "Justificación registrada exitosamente", 201
        except Exception as e:
            return None, f"Error al registrar justificación: {str(e)}", 500
        finally:
            connection.close()

    @classmethod
    def _notificar_justificacion_administradores(cls):
        """
        Envía notificación push FCM a los administradores cuando se registra una justificación.
        1. Consulta SQL en USUARIO_DISPOSITIVO con JOIN a USUARIOS:
           SELECT ud.fcm_token 
           FROM USUARIO_DISPOSITIVO ud
           JOIN USUARIOS u ON ud.idUsuario = u.idUsuario
           WHERE u.rol IN ('ADMINISTRADOR', 'ADMIN', 'SUPERVISOR') 
             AND ud.activo = 1 
             AND ud.fcm_token IS NOT NULL 
             AND ud.fcm_token != ''
        2. Por cada fcm_token obtenido, envía notificación push:
           - Título: "Nueva Justificación Registrada"
           - Cuerpo: "El colaborador ha presentado una justificación de inasistencia."
           - Data: {"tipo": "JUSTIFICACION", "pantalla": "JUSTIFICACION"}
        3. Totalmente protegido en try-except para salvaguardar el guardado en MySQL.
        """
        try:
            conn = get_connection()
            tokens = []
            try:
                try:
                    cursor = conn.cursor(dictionary=True)
                except TypeError:
                    cursor = conn.cursor()

                # 1. Consulta SQL para obtener tokens FCM activos de todos los administradores
                sql = """
                    SELECT ud.fcm_token 
                    FROM USUARIO_DISPOSITIVO ud
                    JOIN USUARIOS u ON ud.idUsuario = u.idUsuario
                    WHERE u.rol IN ('ADMINISTRADOR', 'ADMIN', 'SUPERVISOR') 
                      AND ud.activo = 1 
                      AND ud.fcm_token IS NOT NULL 
                      AND ud.fcm_token != ''
                """
                cursor.execute(sql)
                rows = cursor.fetchall() or []
                for r in rows:
                    tok = r.get("fcm_token") if isinstance(r, dict) else r[0]
                    if tok and str(tok).strip() and str(tok).strip() not in tokens:
                        tokens.append(str(tok).strip())

                # Fallback complementario desde USUARIOS.fcm_token
                try:
                    cursor.execute("""
                        SELECT fcm_token FROM USUARIOS 
                        WHERE rol IN ('ADMINISTRADOR', 'ADMIN', 'SUPERVISOR') 
                          AND fcm_token IS NOT NULL 
                          AND fcm_token != ''
                    """)
                    for r in cursor.fetchall() or []:
                        tok = r.get("fcm_token") if isinstance(r, dict) else r[0]
                        if tok and str(tok).strip() and str(tok).strip() not in tokens:
                            tokens.append(str(tok).strip())
                except Exception:
                    pass

                cursor.close()
            finally:
                conn.close()

            if not tokens:
                print("[FCM Justificación] No se encontraron tokens FCM activos de administradores/supervisores.")
                return

            titulo = "Nueva Justificación Registrada"
            cuerpo = "El colaborador ha presentado una justificación de inasistencia."
            data_payload = {
                "tipo": "JUSTIFICACION",
                "pantalla": "JUSTIFICACION"
            }

            # 2. Por cada fcm_token obtenido, enviar notificación push protegida en try-except
            for token in tokens:
                try:
                    ok, det = FCMService.enviar_a_token(
                        fcm_token=token,
                        titulo=titulo,
                        mensaje=cuerpo,
                        data=data_payload
                    )
                    if ok:
                        print(f"[FCM Justificación SUCCESS]: Enviado a {token[:20]}... ({det})")
                    else:
                        print(f"[FCM Justificación fallback]: {det}, intentando con firebase/fcm.py...")
                        try:
                            from firebase.fcm import notificar
                            notificar(device_token=token, title=titulo, body=cuerpo, data=data_payload)
                            print(f"[FCM Justificación SUCCESS]: Enviado con firebase/fcm a {token[:20]}...")
                        except Exception as e_direct:
                            print(f"[FCM Justificación ERROR]: Error al notificar token {token[:20]}...: {e_direct}")
                except Exception as e_send:
                    try:
                        from firebase.fcm import notificar
                        notificar(device_token=token, title=titulo, body=cuerpo, data=data_payload)
                        print(f"[FCM Justificación SUCCESS]: Enviado con firebase/fcm a {token[:20]}...")
                    except Exception as e_fb:
                        print(f"[FCM Justificación ERROR]: Error al enviar push a token {token[:20]}...: {e_fb}")

        except Exception as e_outer:
            print(f"[FCM Justificación ERROR]: Error general en envío push (MySQL seguro): {e_outer}")

    @classmethod
    def _notificar_justificacion_en_segundo_plano(cls, id_usuario=None, motivo=None):
        """Compatibilidad con versiones anteriores."""
        cls._notificar_justificacion_administradores()

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
