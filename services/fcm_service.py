import os
import glob
import json
import time
import threading
import urllib.request
import urllib.parse
import urllib.error

# Intentar importar requests si está instalado; de lo contrario se usa urllib (nativo)
try:
    import requests
except ImportError:
    requests = None

# PyJWT (instalado junto a Flask-JWT-Extended y cryptography)
try:
    import jwt
except ImportError:
    jwt = None

# google-auth si está disponible
try:
    from google.oauth2 import service_account
    import google.auth.transport.requests
except ImportError:
    service_account = None

# Firebase Admin SDK (credentials.Certificate)
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None

from config import BASE_DIR
from database import get_connection

SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]

class FCMService:
    _app_inicializada = False
    _credentials = None
    _access_token = None
    _token_expiry = 0
    _project_id = None

    NOMBRE_ARCHIVO_CREDENCIAL = "piccolifield-firebase-adminsdk-fbsvc-8b6481d9e4.json"

    @classmethod
    def _obtener_ruta_credenciales(cls):
        """
        Retorna la ruta absoluta al archivo de credenciales de Firebase Admin SDK.
        Construye la ruta a partir de la ubicación de fcm_service.py.
        """
        ruta_directa = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "firebase",
                "piccolifield-firebase-adminsdk-fbsvc-8b6481d9e4.json",
            )
        )
        print(f"[FCM] Buscando archivo de credenciales en: {ruta_directa}")

        if os.path.isfile(ruta_directa):
            print(f"[FCM] Archivo de credenciales encontrado correctamente: {ruta_directa}")
            return ruta_directa

        print(f"[FCM] ADVERTENCIA: El archivo no existe en la ruta: {ruta_directa}")

        # Fallback a variable de entorno si estuviera definida
        env_path = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if env_path and os.path.isfile(env_path):
            print(f"[FCM] Utilizando credenciales desde variable de entorno: {env_path}")
            return env_path

        # Fallback a cualquier otro .json en la carpeta firebase/
        firebase_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "firebase"))
        for f in glob.glob(os.path.join(firebase_dir, "*.json")):
            if os.path.basename(f).lower() == "google-services.json":
                continue
            print(f"[FCM] Utilizando archivo JSON alternativo encontrado en: {f}")
            return f

        return None

    @classmethod
    def _inicializar_firebase_admin(cls):
        """
        Inicializa firebase_admin utilizando credentials.Certificate con el archivo JSON.
        """
        if firebase_admin is None or credentials is None:
            return False, "Librería firebase-admin no instalada en el entorno"

        if cls._app_inicializada or (firebase_admin._apps and len(firebase_admin._apps) > 0):
            cls._app_inicializada = True
            return True, "firebase_admin ya inicializado"

        ruta_cred = cls._obtener_ruta_credenciales()
        if not ruta_cred or not os.path.isfile(ruta_cred):
            return False, f"Archivo de credenciales no encontrado en: {ruta_cred}"

        try:
            cred = credentials.Certificate(ruta_cred)
            firebase_admin.initialize_app(cred)
            cls._app_inicializada = True
            print(f"[FCM] firebase_admin inicializado exitosamente con Certificate('{os.path.basename(ruta_cred)}')")
            return True, "Inicializado con éxito"
        except Exception as e:
            print(f"[FCM] Error al inicializar firebase_admin.credentials.Certificate: {e}")
            return False, str(e)

    @classmethod
    def _http_post_json(cls, url, headers, payload, timeout=8):
        """
        Envía un POST JSON compatible tanto con requests (si está disponible)
        como con urllib.request (biblioteca estándar sin dependencias externas).
        """
        if requests is not None:
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
                return resp.status_code, resp.text
            except Exception as e:
                return 0, f"Error requests: {str(e)}"
        else:
            # Fallback nativo 100% estándar
            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=json_bytes, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return response.status, response.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8")
            except Exception as e:
                return 0, f"Error urllib: {str(e)}"

    @classmethod
    def _obtener_credenciales_archivo(cls):
        cred_path = cls._obtener_ruta_credenciales()
        if not cred_path or not os.path.isfile(cred_path):
            return None, None

        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            project_id = key_data.get("project_id", "piccolifield")
            return cred_path, key_data
        except Exception as e:
            print(f"[FCM] Error al leer archivo de credenciales {cred_path}: {e}")
            return None, None

    @classmethod
    def _obtener_access_token(cls):
        """
        Obtiene o renueva el OAuth2 Access Token para Google FCM HTTP v1.
        Soporta:
        1. PyJWT + urllib (estándar, sin necesidad de google-auth o requests).
        2. google.oauth2.service_account (si está instalado).
        """
        if cls._access_token and time.time() < (cls._token_expiry - 300):
            return cls._access_token, cls._project_id

        cred_path, key_data = cls._obtener_credenciales_archivo()
        if not key_data:
            return None, None

        cls._project_id = key_data.get("project_id", "piccolifield")

        # Opción 1: Generación nativa con PyJWT (disponible gracias a Flask-JWT-Extended y cryptography)
        if jwt is not None and "private_key" in key_data:
            try:
                now = int(time.time())
                payload = {
                    "iss": key_data["client_email"],
                    "scope": "https://www.googleapis.com/auth/firebase.messaging",
                    "aud": key_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                    "exp": now + 3600,
                    "iat": now
                }
                assertion = jwt.encode(payload, key_data["private_key"], algorithm="RS256")
                token_url = key_data.get("token_uri", "https://oauth2.googleapis.com/token")

                post_body = urllib.parse.urlencode({
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion
                }).encode("utf-8")

                req = urllib.request.Request(
                    token_url,
                    data=post_body,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=8) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    cls._access_token = resp_data.get("access_token")
                    expires_in = int(resp_data.get("expires_in", 3600))
                    cls._token_expiry = time.time() + expires_in
                    return cls._access_token, cls._project_id
            except Exception as e:
                print(f"[FCM] Intento de firma nativa falló ({e}), probando google-auth si existe...")

        # Opción 2: google-auth si está instalado
        if service_account is not None and cred_path:
            try:
                creds = service_account.Credentials.from_service_account_file(
                    cred_path, scopes=SCOPES
                )
                req = google.auth.transport.requests.Request()
                creds.refresh(req)
                cls._access_token = creds.token
                cls._token_expiry = time.time() + 3600
                return cls._access_token, cls._project_id
            except Exception as e:
                print(f"[FCM] Error al renovar token con google-auth: {e}")

        return None, cls._project_id

    @classmethod
    def enviar_a_token(cls, fcm_token, titulo, mensaje, data=None):
        """
        Envía un mensaje push directo a un token FCM.
        Prioriza el uso de Firebase Admin SDK con credentials.Certificate y messaging.send().
        Si firebase-admin no está disponible o falla, utiliza la API HTTP v1 con OAuth2.
        """
        if not fcm_token:
            return False, "Token vacío"

        # Todos los valores del diccionario data deben ser strings
        data_strings = {str(k): str(v) for k, v in (data or {}).items()}

        # ── 1. Intento con Firebase Admin SDK (credentials.Certificate) ──
        if firebase_admin is not None and messaging is not None:
            ok_init, det_init = cls._inicializar_firebase_admin()
            if ok_init:
                try:
                    fcm_msg = messaging.Message(
                        notification=messaging.Notification(
                            title=titulo,
                            body=mensaje,
                        ),
                        data=data_strings,
                        token=fcm_token,
                        android=messaging.AndroidConfig(
                            priority="high",
                            notification=messaging.AndroidNotification(
                                sound="default",
                                channel_id="piccoli_notificaciones",
                                click_action="OPEN_ACTIVITY"
                            )
                        )
                    )
                    resp_id = messaging.send(fcm_msg)
                    return True, f"Enviado con éxito (FCM Admin SDK: {resp_id})"
                except Exception as e:
                    print(f"[FCM Admin SDK] messaging.send falló ({e}). Intentando fallback HTTP v1...")

        # ── 2. Fallback: Google FCM HTTP v1 directo ──────────────────────
        access_token, project_id = cls._obtener_access_token()
        if not access_token or not project_id:
            return False, "No se pudieron obtener credenciales de Firebase"

        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8"
        }

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

        status_code, resp_text = cls._http_post_json(url, headers, payload, timeout=8)
        if status_code == 200:
            return True, "Enviado con éxito"
        else:
            return False, f"FCM Error {status_code}: {resp_text}"

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
