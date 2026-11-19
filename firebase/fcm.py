import os
import json
import datetime
import requests
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account

try:
    import firebase_admin
    from firebase_admin import credentials as fb_credentials, messaging
except ImportError:
    firebase_admin = None
    fb_credentials = None
    messaging = None


def _obtener_ruta_credenciales():
    SERVICE_ACCOUNT_FILE = 'piccolifield-firebase-adminsdk-fbsvc-8b6481d9e4.json'
    service_account_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SERVICE_ACCOUNT_FILE)
    if not os.path.isfile(service_account_path):
        service_account_path = os.path.join(os.getcwd(), "firebase", SERVICE_ACCOUNT_FILE)
    if os.path.isfile(service_account_path):
        return service_account_path
    return None


def _inicializar_firebase():
    if firebase_admin is None or fb_credentials is None:
        return False
    if not firebase_admin._apps:
        cred_path = _obtener_ruta_credenciales()
        if cred_path and os.path.isfile(cred_path):
            cred = fb_credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            return True
        else:
            try:
                firebase_admin.initialize_app()
                return True
            except Exception:
                return False
    return True


def _enviar_http_v1(token, titulo, mensaje, data_payload):
    service_account_path = _obtener_ruta_credenciales()
    if not service_account_path or not os.path.isfile(service_account_path):
        raise FileNotFoundError(f"Archivo de credenciales de Firebase no encontrado.")

    SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
    credentials = service_account.Credentials.from_service_account_file(service_account_path, scopes=SCOPES)
    credentials.refresh(Request())
    access_token = credentials.token

    FCM_URL = 'https://fcm.googleapis.com/v1/projects/piccolifield/messages:send'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json; UTF-8',
    }
    message = {
        'message': {
            'token': str(token),
            'notification': {
                'title': str(titulo),
                'body': str(mensaje),
            },
            'data': data_payload
        }
    }
    response = requests.post(FCM_URL, headers=headers, data=json.dumps(message), timeout=10)
    print(f"[FCM HTTP v1 Status] {response.status_code}: {response.text}")
    return response.status_code == 200


def notificar(token=None, titulo=None, mensaje=None, data=None, **kwargs):
    """
    Envía una notificación push FCM con soporte para data payload.
    Acepta parámetros posicionales y nombrados (token/device_token, titulo/title, mensaje/body, data).
    """
    # Compatibilidad con argumentos nombrados tradicionales
    token = token or kwargs.get("device_token") or kwargs.get("token")
    titulo = titulo or kwargs.get("title") or kwargs.get("titulo") or "Notificación"
    mensaje = mensaje or kwargs.get("body") or kwargs.get("mensaje") or ""
    data_payload = data if data is not None else kwargs.get("data")

    if not token:
        print("[FCM ERROR] Token de dispositivo vacío.")
        return False

    try:
        data_dict = data_payload or {}
        if isinstance(data_dict, dict):
            # Asegurar que todas las llaves y valores sean strings
            data_dict = {str(k): str(v) for k, v in data_dict.items()}
            data_dict["title"] = str(titulo)
            data_dict["body"] = str(mensaje)
        else:
            data_dict = {
                "title": str(titulo),
                "body": str(mensaje)
            }

        # 1. Intento primario con Firebase Admin SDK (messaging.send)
        if firebase_admin is not None and messaging is not None:
            try:
                _inicializar_firebase()
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=str(titulo),
                        body=str(mensaje)
                    ),
                    data=data_dict,
                    token=str(token)
                )
                response = messaging.send(message)
                print(f"[FCM ÉXITO] Notificación enviada a token {token}: {response}")
                return True
            except Exception as e_adm:
                print(f"[FCM Admin SDK] Falló ({e_adm}), intentando HTTP v1 fallback...")

        # 2. Fallback con Google Auth HTTP v1 (OAuth2)
        try:
            exito = _enviar_http_v1(token, titulo, mensaje, data_dict)
            if exito:
                print(f"[FCM ÉXITO] Notificación HTTP v1 enviada a token {token}")
                return True
        except Exception as e_v1:
            print(f"[FCM HTTP v1 ERROR] Falló envío: {e_v1}")

        return False

    except Exception as e:
        print(f"[FCM ERROR] Error al enviar token {token}: {str(e)}")
        return False
