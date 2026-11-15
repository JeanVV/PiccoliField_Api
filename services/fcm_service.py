import os
import glob
import json
import time
import threading
import requests
from google.oauth2 import service_account
import google.auth.transport.requests

from config import BASE_DIR
from database import get_connection

SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

class FCMService:
    _credentials = None
    _access_token = None
    _token_expiry = 0
    _project_id = None

    @classmethod
    def _obtener_credenciales(cls):
        if cls._credentials is not None and cls._project_id is not None:
            return cls._credentials, cls._project_id

        firebase_dir = os.path.join(BASE_DIR, "firebase")
        json_files = glob.glob(os.path.join(firebase_dir, "*.json"))
        if not json_files:
            return None, None

        cred_path = json_files[0]
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._project_id = data.get("project_id", "piccolifield")

            cls._credentials = service_account.Credentials.from_service_account_file(
                cred_path, scopes=SCOPES
            )
            return cls._credentials, cls._project_id
        except Exception as e:
            print(f"[FCM] Error al cargar credenciales de servicio: {e}")
            return None, None

    @classmethod
    def _obtener_access_token(cls):
        creds, project_id = cls._obtener_credenciales()
        if not creds:
            return None, None

        # Si el token sigue vigente (con 5 min de margen)
        if cls._access_token and time.time() < (cls._token_expiry - 300):
            return cls._access_token, project_id

        try:
            req = google.auth.transport.requests.Request()
            creds.refresh(req)
            cls._access_token = creds.token
            cls._token_expiry = time.time() + 3600
            return cls._access_token, project_id
        except Exception as e:
            print(f"[FCM] Error al renovar token OAuth2: {e}")
            return None, project_id

    @classmethod
    def enviar_a_token(cls, fcm_token, titulo, mensaje, data=None):
        """
        Envía un mensaje push directo a un token FCM usando la API HTTP v1 de Firebase.
        """
        if not fcm_token:
            return False, "Token vacío"

        access_token, project_id = cls._obtener_access_token()
        if not access_token or not project_id:
            return False, "No se pudieron obtener credenciales de Firebase"

        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8"
        }

        # Todos los valores del diccionario data deben ser strings
        data_strings = {str(k): str(v) for k, v in (data or {}).items()}

        payload = {
            "message": {
                "token": fcm_token,
                "notification": {
                    "title": titulo,
                    "body": mensaje
                },
                "data": data_strings,
                "android": {
                    "priority": "HIGH",
                    "notification": {
                        "sound": "default",
                        "channel_id": "piccoli_notificaciones",
                        "click_action": "OPEN_ACTIVITY"
                    }
                }
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                return True, "Enviado con éxito"
            else:
                return False, f"FCM Error {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, f"Excepción de conexión FCM: {str(e)}"

    @classmethod
    def obtener_tokens_usuario(cls, idUsuario):
        """
        Busca todos los tokens FCM activos para el idUsuario en USUARIO_DISPOSITIVO y USUARIOS.
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            sql = """
                SELECT DISTINCT fcm_token FROM (
                    SELECT fcm_token FROM USUARIO_DISPOSITIVO 
                    WHERE idUsuario = %s AND activo = 1 AND fcm_token IS NOT NULL AND fcm_token != ''
                    UNION
                    SELECT fcm_token FROM USUARIOS 
                    WHERE idUsuario = %s AND fcm_token IS NOT NULL AND fcm_token != ''
                ) t
            """
            cursor.execute(sql, (idUsuario, idUsuario))
            rows = cursor.fetchall() or []
            return [r["fcm_token"] for r in rows if r.get("fcm_token")]
        except Exception as e:
            print(f"[FCM] Error al obtener tokens de usuario {idUsuario}: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def obtener_promotores_activos(cls):
        """
        Retorna la lista de idUsuario de todos los usuarios con rol PROMOTOR activos.
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT idUsuario FROM USUARIOS 
                WHERE rol = 'PROMOTOR' AND estado = 'ACTIVO'
            """)
            rows = cursor.fetchall() or []
            return [r["idUsuario"] for r in rows if r.get("idUsuario")]
        except Exception as e:
            print(f"[FCM] Error al obtener promotores activos: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def _guardar_log(cls, idUsuario, tipo, referencia, mensaje, resultado):
        """
        Inserta registro en la tabla NOTIFICACIONES_LOG
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            sql = """
                INSERT INTO NOTIFICACIONES_LOG (tipo, referencia, mensaje, fcm_result, fecha, idUsuario)
                VALUES (%s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(sql, (tipo, referencia, mensaje[:250], str(resultado)[:250], idUsuario))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[FCM] Error al registrar log de notificación: {e}")

    @classmethod
    def notificar_usuario(cls, idUsuario, titulo, mensaje, data=None, tipo="GENERAL", referencia=None):
        """
        Envía notificación a un usuario a todos sus dispositivos registrados de forma síncrona o interna.
        """
        tokens = cls.obtener_tokens_usuario(idUsuario)
        if not tokens:
            cls._guardar_log(idUsuario, tipo, referencia, mensaje, "Sin tokens registrados")
            return False

        enviado_al_menos_uno = False
        detalles = []
        for t in tokens:
            ok, det = cls.enviar_a_token(t, titulo, mensaje, data)
            detalles.append(det)
            if ok:
                enviado_al_menos_uno = True

        cls._guardar_log(idUsuario, tipo, referencia, mensaje, "; ".join(detalles))
        return enviado_al_menos_uno

    @classmethod
    def _ejecutar_en_segundo_plano(cls, target, *args, **kwargs):
        """
        Ejecuta el envío en un hilo daemon para no bloquear la respuesta HTTP del endpoint.
        """
        t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        t.start()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Alerta de Stock: se envía a TODOS los promotores activos
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def notificar_alerta_stock(cls, idPuntosVenta, idProductos, stock_actual, stock_minimo, idAlerta=None):
        def _job():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                # Obtener nombre del local
                cursor.execute("SELECT puntoVenta FROM PUNTOS_VENTA WHERE idPuntosVenta = %s LIMIT 1", (idPuntosVenta,))
                pdv = cursor.fetchone()

                # Obtener nombre del producto
                cursor.execute("SELECT producto FROM PRODUCTOS WHERE idProductos = %s LIMIT 1", (idProductos,))
                prod = cursor.fetchone()
                conn.close()

                nombre_pdv = pdv.get("puntoVenta", "Local") if pdv else "Local"
                nombre_producto = prod.get("producto", "Producto") if prod else "Producto"

                titulo = "⚠️ Alerta de Stock Bajo"
                mensaje = f"'{nombre_producto}' en nivel crítico ({stock_actual} uds., mín: {stock_minimo}) en {nombre_pdv}."

                # Payload con "tipo" e "id" para redirección en la app móvil
                data = {
                    "tipo": "ALERTA",
                    "id": str(idAlerta if idAlerta else idPuntosVenta),
                    "idAlerta": str(idAlerta or ""),
                    "idPuntosVenta": str(idPuntosVenta),
                    "idProductos": str(idProductos),
                    "stock_actual": str(stock_actual),
                    "stock_minimo": str(stock_minimo)
                }

                promotores = cls.obtener_promotores_activos()
                for idPromotor in promotores:
                    cls.notificar_usuario(
                        idUsuario=idPromotor,
                        titulo=titulo,
                        mensaje=mensaje,
                        data=data,
                        tipo="ALERTA_STOCK",
                        referencia=f"ALERTA-{idAlerta}" if idAlerta else f"PDV-{idPuntosVenta}"
                    )
            except Exception as e:
                print(f"[FCM] Error en job notificar_alerta_stock: {e}")

        cls._ejecutar_en_segundo_plano(_job)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Nueva Incidencia: se envía a TODOS los promotores activos
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def notificar_nueva_incidencia(cls, idPuntosVenta, tipo_incidencia, severidad, descripcion, idIncidencias=None, idUsuarioReporta=None):
        def _job():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT puntoVenta FROM PUNTOS_VENTA WHERE idPuntosVenta = %s LIMIT 1", (idPuntosVenta,))
                pdv = cursor.fetchone()
                conn.close()

                nombre_pdv = pdv.get("puntoVenta", "Local") if pdv else "Local"

                titulo = f"🚨 Nueva Incidencia: {nombre_pdv}"
                desc_corta = (descripcion or "")[:90]
                mensaje = f"[{severidad}] {tipo_incidencia}: {desc_corta}"

                # Payload con "tipo" e "id" para redirección en la app móvil
                data = {
                    "tipo": "INCIDENCIA",
                    "id": str(idIncidencias or ""),
                    "idIncidencias": str(idIncidencias or ""),
                    "idPuntosVenta": str(idPuntosVenta),
                    "severidad": str(severidad or "MEDIA"),
                    "tipo_incidencia": str(tipo_incidencia)
                }

                promotores = cls.obtener_promotores_activos()
                for idPromotor in promotores:
                    cls.notificar_usuario(
                        idUsuario=idPromotor,
                        titulo=titulo,
                        mensaje=mensaje,
                        data=data,
                        tipo="INCIDENCIA_NUEVA",
                        referencia=f"INC-{idIncidencias}" if idIncidencias else f"PDV-{idPuntosVenta}"
                    )
            except Exception as e:
                print(f"[FCM] Error en job notificar_nueva_incidencia: {e}")

        cls._ejecutar_en_segundo_plano(_job)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Incidencia Resuelta: se envía al impulsador que la reportó
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def notificar_incidencia_resuelta(cls, idIncidencias, nuevo_estado="RESUELTO", comentario_atencion=None):
        def _job():
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT i.idUsuario, i.tipo, pv.puntoVenta
                    FROM INCIDENCIAS i
                    LEFT JOIN PUNTOS_VENTA pv ON i.idPuntosVenta = pv.idPuntosVenta
                    WHERE i.idIncidencias = %s
                    LIMIT 1
                """, (idIncidencias,))
                inc = cursor.fetchone()
                conn.close()

                if not inc or not inc.get("idUsuario"):
                    return

                idImpulsador = inc["idUsuario"]
                tipo_inc = inc.get("tipo", "Incidencia")
                nombre_pdv = inc.get("puntoVenta", "su local")

                estado_texto = "resuelta" if nuevo_estado.upper() == "RESUELTO" else "atendida"
                titulo = f"✅ Incidencia {estado_texto.capitalize()}"
                if comentario_atencion and comentario_atencion.strip():
                    mensaje = f"Tu reporte de '{tipo_inc}' fue {estado_texto}: \"{comentario_atencion.strip()}\""
                else:
                    mensaje = f"Tu reporte de '{tipo_inc}' en {nombre_pdv} ha sido marcado como {estado_texto}."

                data = {
                    "tipo": "INCIDENCIA",
                    "id": str(idIncidencias),
                    "idIncidencias": str(idIncidencias),
                    "estado": str(nuevo_estado)
                }

                cls.notificar_usuario(
                    idUsuario=idImpulsador,
                    titulo=titulo,
                    mensaje=mensaje,
                    data=data,
                    tipo="INCIDENCIA_RESUELTA",
                    referencia=f"INC-{idIncidencias}"
                )
            except Exception as e:
                print(f"[FCM] Error en job notificar_incidencia_resuelta: {e}")

        cls._ejecutar_en_segundo_plano(_job)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Meta Alcanzada: se envía al impulsador al alcanzar o superar su meta
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def notificar_meta_alcanzada(cls, idUsuario, meta_ventas, total_vendido, pct=100.0):
        def _job():
            try:
                titulo = "🎉 ¡Felicitaciones! Alcanzaste tu meta"
                mensaje = f"¡Excelente trabajo! Has alcanzado el {pct}% de tu meta mensual con S/ {float(total_vendido):.2f} en ventas."

                data = {
                    "tipo": "META",
                    "id": str(idUsuario),
                    "idUsuario": str(idUsuario),
                    "meta_ventas": str(meta_ventas),
                    "total_vendido": str(total_vendido),
                    "porcentaje": str(pct)
                }

                cls.notificar_usuario(
                    idUsuario=idUsuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    data=data,
                    tipo="META_ALCANZADA",
                    referencia=f"META-{idUsuario}"
                )
            except Exception as e:
                print(f"[FCM] Error en job notificar_meta_alcanzada: {e}")

        cls._ejecutar_en_segundo_plano(_job)

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Reasignación de Local: se envía al impulsador cuando es reasignado
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def notificar_reasignacion_local(cls, idUsuario, idPuntosVenta, nombre_pdv=None, motivo=None):
        def _job():
            try:
                # Si no vino el nombre del PDV, consultarlo
                if not nombre_pdv:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT puntoVenta FROM PUNTOS_VENTA WHERE idPuntosVenta = %s LIMIT 1", (idPuntosVenta,))
                    pdv_row = cursor.fetchone()
                    conn.close()
                    pdv_nombre = pdv_row.get("puntoVenta", "Nuevo Local") if pdv_row else "Nuevo Local"
                else:
                    pdv_nombre = nombre_pdv

                titulo = "📍 Reasignación de Local"
                motivo_texto = f" Motivo: {motivo}." if motivo else ""
                mensaje = f"Has sido reasignado al punto de venta '{pdv_nombre}'.{motivo_texto}"

                data = {
                    "tipo": "REASIGNACION",
                    "id": str(idPuntosVenta),
                    "idPuntosVenta": str(idPuntosVenta),
                    "nombre_pdv": str(pdv_nombre)
                }

                cls.notificar_usuario(
                    idUsuario=idUsuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    data=data,
                    tipo="REASIGNACION_LOCAL",
                    referencia=f"PDV-{idPuntosVenta}"
                )
            except Exception as e:
                print(f"[FCM] Error en job notificar_reasignacion_local: {e}")

        cls._ejecutar_en_segundo_plano(_job)
