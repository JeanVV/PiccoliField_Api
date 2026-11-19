import json
import os

def build_collection():
    collection = {
        "info": {
            "_postman_id": "piccolifield-full-api-v2-updated",
            "name": "PiccoliField API - Colección Completa (Actualizada)",
            "description": "Colección completa y exhaustiva con el 100% de rutas y endpoints de PiccoliField API.\nIncluye Autenticación, Perfil, Fotos físicas en uploads/, Notificaciones, Puntos de Venta, Pedidos, Catálogo, Operaciones de Impulsador, Asistencias, Justificaciones, Supervisión, Prospectos (con conversión automática a PDV), FCM y Archivos Multimedia.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{token}}",
                    "type": "string"
                }
            ]
        },
        "event": [],
        "variable": [
            {
                "key": "base_url",
                "value": "https://piccolifield-api-smkc.onrender.com/api",
                "type": "string",
                "description": "URL base en Render. Para pruebas en desarrollo local usar: http://localhost:5000/api"
            },
            {
                "key": "base_host",
                "value": "https://piccolifield-api-smkc.onrender.com",
                "type": "string",
                "description": "Host raíz sin prefijo /api (para uploads y rutas directas). Para local usar: http://localhost:5000"
            },
            {
                "key": "token",
                "value": "",
                "type": "string",
                "description": "Token JWT guardado automáticamente tras el Login"
            }
        ],
        "item": []
    }

    def req(name, method, url, desc="", body=None, formdata=None, headers=None, auth_inherit=True, tests=None):
        item = {
            "name": name,
            "request": {
                "method": method,
                "header": headers or [],
                "url": {
                    "raw": url,
                    "host": [url.split("/")[0]],
                    "path": [p for p in url.split("/")[1:] if p]
                },
                "description": desc
            },
            "response": []
        }
        if not auth_inherit:
            item["request"]["auth"] = {"type": "noauth"}

        if formdata is not None:
            item["request"]["body"] = {
                "mode": "formdata",
                "formdata": formdata
            }
        elif body is not None:
            if isinstance(body, dict) or isinstance(body, list):
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(body, indent=2, ensure_ascii=False),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
                if not any(h.get("key", "").lower() == "content-type" for h in (headers or [])):
                    item["request"]["header"].append({"key": "Content-Type", "value": "application/json", "type": "text"})
            elif isinstance(body, str):
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": body,
                    "options": {"raw": {"language": "json"}}
                }

        if tests:
            item["event"] = [
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": tests
                    }
                }
            ]
        return item

    # ─────────────────────────────────────────────────────────────────────────
    # 0. AUTENTICACIÓN, PERFIL Y NOTIFICACIONES
    # ─────────────────────────────────────────────────────────────────────────
    auth_folder = {
        "name": "0. Autenticación, Perfil y Notificaciones",
        "description": "Login, perfil de usuario, tokens FCM, fotos de perfil (físicas en uploads/perfiles/) y notificaciones push.",
        "item": [
            req(
                name="Login (Iniciar Sesión)",
                method="POST",
                url="{{base_url}}/auth/login",
                desc="Inicia sesión con correo y contraseña. Guarda automáticamente el token JWT en las variables {{token}}.",
                body={
                    "correo": "admin@piccolifield.com",
                    "password": "Password123!"
                },
                auth_inherit=False,
                tests=[
                    "var jsonData = pm.response.json();",
                    "if (jsonData.data && jsonData.data.token) {",
                    "    pm.collectionVariables.set('token', jsonData.data.token);",
                    "    pm.environment.set('token', jsonData.data.token);",
                    "    console.log('Token JWT guardado automáticamente en {{token}}');",
                    "}"
                ]
            ),
            req(
                name="Ver Mi Perfil",
                method="GET",
                url="{{base_url}}/perfil",
                desc="Obtiene los datos completos del colaborador autenticado (nombres, rol, sede, correo, teléfono, foto, estado)."
            ),
            req(
                name="Actualizar Mi Foto de Perfil (Base64)",
                method="PUT",
                url="{{base_url}}/perfil/foto",
                desc="Actualiza la foto de perfil del usuario en sesión. La API decodifica el Base64, guarda el archivo en uploads/perfiles/ y almacena la ruta corta en MySQL.",
                body={
                    "url_foto": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/..."
                }
            ),
            req(
                name="Actualizar Mi Foto de Perfil (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/perfil/foto",
                desc="Permite subir la foto de perfil directamente como archivo físico multipart (campo 'foto').",
                formdata=[
                    {"key": "foto", "type": "file", "src": "", "description": "Seleccionar archivo de imagen .jpg/.png"}
                ]
            ),
            req(
                name="Obtener Mi Foto de Perfil (Stream)",
                method="GET",
                url="{{base_url}}/perfil/foto",
                desc="Devuelve la imagen física de la foto de perfil en streaming binario (JPEG/PNG)."
            ),
            req(
                name="Actualizar Foto de un Usuario por ID (Admin Base64)",
                method="PUT",
                url="{{base_url}}/usuarios/8/foto",
                desc="Permite al administrador actualizar la foto de perfil de cualquier usuario mediante Base64 o ruta.",
                body={
                    "url_foto": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/..."
                }
            ),
            req(
                name="Actualizar Foto de un Usuario por ID (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/usuarios/8/foto",
                desc="Permite al administrador subir la imagen física del usuario mediante multipart/form-data (campo 'foto').",
                formdata=[
                    {"key": "foto", "type": "file", "src": "", "description": "Seleccionar imagen física"}
                ]
            ),
            req(
                name="Obtener Foto de un Usuario por ID (Stream)",
                method="GET",
                url="{{base_url}}/usuarios/8/foto",
                desc="Retorna el archivo de imagen de perfil del usuario especificado por su idUsuario."
            ),
            req(
                name="Actualizar FCM Token de Mi Perfil (PUT)",
                method="PUT",
                url="{{base_url}}/perfil/fcm-token",
                desc="Registra o actualiza el token de Firebase Cloud Messaging (FCM) del dispositivo móvil para recibir notificaciones push.",
                body={
                    "token": "fcm_token_generado_en_el_dispositivo_movil_firebase_123456",
                    "dispositivo_info": "Samsung Galaxy A54 (Android 14)"
                }
            ),
            req(
                name="Actualizar FCM Token de Mi Perfil (POST)",
                method="POST",
                url="{{base_url}}/perfil/fcm-token",
                desc="Ruta POST alternativa para registrar o refrescar el token FCM de notificaciones push.",
                body={
                    "token": "fcm_token_generado_en_el_dispositivo_movil_firebase_123456"
                }
            ),
            req(
                name="Actualizar FCM Token (Alias /api/usuario/fcm-token)",
                method="POST",
                url="{{base_url}}/usuario/fcm-token",
                desc="Ruta alias para registro de token FCM desde la aplicación móvil.",
                body={
                    "token": "fcm_token_generado_en_el_dispositivo_movil_firebase_123456",
                    "dispositivo_info": "Xiaomi Redmi Note 12"
                }
            ),
            req(
                name="Actualizar FCM Token (Alias PUT /api/usuario/fcm-token)",
                method="PUT",
                url="{{base_url}}/usuario/fcm-token",
                desc="Ruta alias con método PUT para actualizar el token FCM.",
                body={
                    "token": "fcm_token_generado_en_el_dispositivo_movil_firebase_123456"
                }
            ),
            req(
                name="Historial de Notificaciones Recibidas",
                method="GET",
                url="{{base_url}}/notificaciones?limite=20",
                desc="Lista el historial de notificaciones push enviadas y recibidas por el usuario logueado."
            ),
            req(
                name="Historial de Notificaciones (Alias /api/perfil/notificaciones)",
                method="GET",
                url="{{base_url}}/perfil/notificaciones",
                desc="Ruta alternativa para consultar el historial de notificaciones del perfil."
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 1. PUNTOS DE VENTA Y DISTRIBUCIÓN
    # ─────────────────────────────────────────────────────────────────────────
    pdv_folder = {
        "name": "1. Puntos de Venta y Distribución",
        "description": "Gestión de puntos de venta (tipo VENTA o DISTRIBUCIÓN), asignación de promotores/responsables, fotos de fachada e historial.",
        "item": [
            req(
                name="Listar Puntos de Venta (Con Filtros)",
                method="GET",
                url="{{base_url}}/puntos-venta?tipo=DISTRIBUCION&estado=ACTIVO",
                desc="Lista todos los puntos de venta. Soporta parámetros opcionales: ?tipo=DISTRIBUCION / VENTA y ?estado=ACTIVO / INACTIVO."
            ),
            req(
                name="Detalle de un Punto de Venta por ID",
                method="GET",
                url="{{base_url}}/puntos-venta/20",
                desc="Obtiene los datos detallados de un punto de venta (código, nombre, dirección, geocerca, promotor asignado, tipo y estado)."
            ),
            req(
                name="Asignar Responsable / Promotor a Punto de Venta (PUT)",
                method="PUT",
                url="{{base_url}}/puntos-venta/20/responsable",
                desc="Asigna un promotor o vendedor responsable al punto de venta y registra el cambio en HISTORIAL_ASIGNACIONES.",
                body={
                    "idUsuario": 8,
                    "motivo": "Asignación de zona comercial norte"
                }
            ),
            req(
                name="Asignar Responsable / Promotor a Punto de Venta (POST)",
                method="POST",
                url="{{base_url}}/puntos-venta/20/responsable",
                desc="Ruta POST alternativa para asignar responsable a un punto de venta.",
                body={
                    "idUsuario": 8,
                    "motivo": "Asignación comercial inicial"
                }
            ),
            req(
                name="Historial de Asignaciones del Punto de Venta",
                method="GET",
                url="{{base_url}}/puntos-venta/20/historial",
                desc="Lista el histórico de todos los promotores/vendedores que han sido asignados al punto de venta."
            ),
            req(
                name="Actualizar Foto de Punto de Venta (Base64)",
                method="PUT",
                url="{{base_url}}/puntos-venta/20/foto",
                desc="Guarda la fotografía de fachada del punto de venta en uploads/prospectos/pdv_20.jpg y actualiza url_foto en la BD.",
                body={
                    "foto_fachada": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Actualizar Foto de Punto de Venta (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/puntos-venta/20/foto",
                desc="Guarda la foto de fachada enviando un archivo físico en multipart (campo 'foto').",
                formdata=[
                    {"key": "foto", "type": "file", "src": "", "description": "Foto de fachada del local"}
                ]
            ),
            req(
                name="Actualizar Foto de PDV (Ruta Supervisión)",
                method="PUT",
                url="{{base_url}}/supervision/puntos-venta/20/foto",
                desc="Ruta de supervisión para actualizar la foto de fachada del punto de venta.",
                body={
                    "foto_fachada": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Actualizar Foto de PDV (Ruta Supervisión POST)",
                method="POST",
                url="{{base_url}}/supervision/puntos-venta/20/foto",
                desc="Ruta de supervisión POST alternativa para actualizar la foto de fachada.",
                body={
                    "foto_fachada": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Obtener Foto de Punto de Venta (Stream)",
                method="GET",
                url="{{base_url}}/puntos-venta/20/foto",
                desc="Retorna en streaming binario la imagen del punto de venta o del prospecto del que fue convertido."
            ),
            req(
                name="Obtener Foto de PDV (Ruta Supervisión Stream)",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/20/foto",
                desc="Retorna en streaming la foto del punto de venta desde el módulo de supervisión."
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. PEDIDOS Y DESPACHO
    # ─────────────────────────────────────────────────────────────────────────
    pedidos_folder = {
        "name": "2. Pedidos y Despacho",
        "description": "Registro de pedidos para puntos de distribución, listados y transiciones de estado (Despacho).",
        "item": [
            req(
                name="Listar Todos los Pedidos",
                method="GET",
                url="{{base_url}}/pedidos?estado=REGISTRADO&tipo=DISTRIBUCION",
                desc="Lista los pedidos. Administrador ve todos; Promotor ve los de sus PDVs asignados. Filtros: ?estado=REGISTRADO, EN_PREPARACION, ENTREGADO, CANCELADO y ?idPuntosVenta=20."
            ),
            req(
                name="Detalle de un Pedido por ID",
                method="GET",
                url="{{base_url}}/pedidos/1",
                desc="Devuelve la información detallada del pedido, datos del punto de venta y del producto solicitado."
            ),
            req(
                name="Registrar Pedido (Ruta Directa)",
                method="POST",
                url="{{base_url}}/pedidos",
                desc="Registra un nuevo pedido para un punto de distribución. Soporta idempotencia mediante header X-Operation-Id.",
                headers=[
                    {"key": "X-Operation-Id", "value": "op-pedido-uuid-12345", "type": "text"}
                ],
                body={
                    "idPuntosVenta": 20,
                    "idProductos": 1,
                    "cantSolicitada": 5
                }
            ),
            req(
                name="Registrar Pedido (Ruta Anidada /puntos-venta/:id/pedidos)",
                method="POST",
                url="{{base_url}}/puntos-venta/20/pedidos",
                desc="Registra un pedido vinculando el idPuntosVenta directamente en la ruta URL.",
                headers=[
                    {"key": "X-Operation-Id", "value": "op-pedido-anidado-67890", "type": "text"}
                ],
                body={
                    "idProductos": 1,
                    "cantSolicitada": 10
                }
            ),
            req(
                name="Listar Pedidos de un Punto de Venta Específico",
                method="GET",
                url="{{base_url}}/puntos-venta/20/pedidos",
                desc="Consulta únicamente el historial de pedidos pertenecientes al punto de venta indicado."
            ),
            req(
                name="Actualizar Estado del Pedido (Despacho)",
                method="PUT",
                url="{{base_url}}/pedidos/1/estado",
                desc="Actualiza el estado: REGISTRADO -> EN_PREPARACION -> ENTREGADO (o CANCELADO). Al pasar a ENTREGADO descuenta inventario.",
                body={
                    "estado": "EN_PREPARACION"
                }
            ),
            req(
                name="Actualizar Estado del Pedido (Método PATCH)",
                method="PATCH",
                url="{{base_url}}/pedidos/1/estado",
                desc="Actualización parcial del estado del pedido mediante método PATCH.",
                body={
                    "estado": "ENTREGADO"
                }
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. CATÁLOGO Y PRODUCTOS
    # ─────────────────────────────────────────────────────────────────────────
    productos_folder = {
        "name": "3. Catálogo y Productos",
        "description": "Consulta de catálogo de licores y bebidas artesanales, búsqueda por código de barras (EAN-13 / UPC).",
        "item": [
            req(
                name="Listar Productos del Catálogo",
                method="GET",
                url="{{base_url}}/productos?activo=1",
                desc="Devuelve todos los productos del catálogo comercial (ID, nombre, descripción, SKU, EAN, precio sugerido, foto)."
            ),
            req(
                name="Detalle de Producto por ID",
                method="GET",
                url="{{base_url}}/productos/1",
                desc="Información detallada de un producto específico del catálogo."
            ),
            req(
                name="Buscar Producto por Código de Barras EAN",
                method="GET",
                url="{{base_url}}/productos/ean/7751234567890",
                desc="Busca un producto por su código EAN-13 o código de barras estándar para visualización y venta rápida."
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. OPERACIONES DE IMPULSADOR
    # ─────────────────────────────────────────────────────────────────────────
    impulsador_folder = {
        "name": "4. Operaciones de Impulsador",
        "description": "Venta rápida por código de barras, reposición de stock (evidencias en uploads/evidencias/), reporte de incidencias y dashboard del promotor.",
        "item": [
            req(
                name="Dashboard del Impulsador",
                method="GET",
                url="{{base_url}}/impulsador/dashboard",
                desc="Resumen de asignación activa, ventas del día, meta diaria y puntos clave del local asignado."
            ),
            req(
                name="Historial de Asignaciones del Impulsador",
                method="GET",
                url="{{base_url}}/impulsador/historial",
                desc="Histórico de locales y puntos de venta donde ha trabajado el impulsador autenticado."
            ),
            req(
                name="Catálogo de Productos en el Local Asignado",
                method="GET",
                url="{{base_url}}/impulsador/productos",
                desc="Lista de productos y su disponibilidad de stock en el punto de venta donde labora el impulsador."
            ),
            req(
                name="Buscar Producto por Código de Barras (Query ?codigo=)",
                method="GET",
                url="{{base_url}}/impulsador/productos/buscar?codigo=7751234567890",
                desc="Busca el producto mediante lector de código de barras para venta o reposición rápida."
            ),
            req(
                name="Buscar Producto por Código de Barras (Path /codigo/:barras)",
                method="GET",
                url="{{base_url}}/impulsador/productos/codigo/7751234567890",
                desc="Ruta alternativa por path param para el lector de código de barras de la app Android."
            ),
            req(
                name="Registrar Venta por Código de Barras",
                method="POST",
                url="{{base_url}}/impulsador/ventas/registrar",
                desc="Registra la venta de botellas en el local asignado y descuenta automáticamente el stock en góndola/almacén.",
                body={
                    "codigo_barras": "7751234567890",
                    "cantidad": 2,
                    "idPuntosVenta": 1
                }
            ),
            req(
                name="Reponer Stock de Producto (Base64)",
                method="POST",
                url="{{base_url}}/impulsador/stock/reponer",
                desc="Actualiza las unidades en exhibición y almacén del producto. Guarda la foto física en uploads/evidencias/reposicion_...jpg y registra la ruta en MySQL.",
                body={
                    "idProductos": 1,
                    "cantExhibida": 15,
                    "cantAlmacen": 30,
                    "idPuntosVenta": 1,
                    "observacion": "Reposición matutina de anaqueles",
                    "foto": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Reponer Stock de Producto (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/impulsador/stock/reponer",
                desc="Permite subir la evidencia física de reposición como archivo multipart (campo 'foto').",
                formdata=[
                    {"key": "idProductos", "value": "1", "type": "text"},
                    {"key": "cantExhibida", "value": "15", "type": "text"},
                    {"key": "cantAlmacen", "value": "30", "type": "text"},
                    {"key": "idPuntosVenta", "value": "1", "type": "text"},
                    {"key": "observacion", "value": "Góndola reabastecida al 100%", "type": "text"},
                    {"key": "foto", "type": "file", "src": "", "description": "Foto de anaquel reabastecido"}
                ]
            ),
            req(
                name="Reponer Stock (Alias /productos/reponer)",
                method="POST",
                url="{{base_url}}/impulsador/productos/reponer",
                desc="Ruta alias para reposición de stock en góndola.",
                body={
                    "idProductos": 1,
                    "cantExhibida": 10,
                    "cantAlmacen": 20,
                    "idPuntosVenta": 1
                }
            ),
            req(
                name="Listar Tipos de Incidencia",
                method="GET",
                url="{{base_url}}/impulsador/incidencias/tipos",
                desc="Obtiene los tipos de incidencia permitidos en el sistema (STOCK, EXHIBICION, ROTURA, COMPETENCIA, etc.)."
            ),
            req(
                name="Reportar Incidencia en Local (Base64)",
                method="POST",
                url="{{base_url}}/impulsador/incidencias",
                desc="Registra una incidencia detectada en el punto de venta. Guarda la evidencia en uploads/evidencias/incidencia_...jpg y la ruta en EVIDENCIAS.ruta_archivo.",
                body={
                    "tipo": "ROTURA",
                    "descripcion": "Se quebró una botella de licor de cacao en el pasillo central",
                    "severidad": "MEDIA",
                    "idPuntosVenta": 1,
                    "foto": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Reportar Incidencia en Local (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/impulsador/incidencias",
                desc="Reporta una incidencia enviando la fotografía física directamente como archivo multipart.",
                formdata=[
                    {"key": "tipo", "value": "ROTURA", "type": "text"},
                    {"key": "descripcion", "value": "Botella rota por caída accidental", "type": "text"},
                    {"key": "severidad", "value": "ALTA", "type": "text"},
                    {"key": "idPuntosVenta", "value": "1", "type": "text"},
                    {"key": "foto", "type": "file", "src": "", "description": "Foto de la incidencia"}
                ]
            ),
            req(
                name="Listar Incidencias Reportadas por el Impulsador",
                method="GET",
                url="{{base_url}}/impulsador/incidencias?estado=PENDIENTE",
                desc="Lista las incidencias registradas por el impulsador autenticado. Filtro opcional: ?estado=PENDIENTE/RESUELTO."
            ),
            req(
                name="Detalle de Incidencia Reportada",
                method="GET",
                url="{{base_url}}/impulsador/incidencias/1",
                desc="Obtiene el detalle completo de una incidencia (fecha, estado, solución y comentarios de supervisión)."
            ),
            req(
                name="Descargar / Ver Foto de Incidencia",
                method="GET",
                url="{{base_url}}/impulsador/incidencias/1/foto",
                desc="Devuelve la imagen física adjunta a la incidencia reportada."
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 5. ASISTENCIAS Y JUSTIFICACIONES
    # ─────────────────────────────────────────────────────────────────────────
    asistencia_folder = {
        "name": "5. Asistencias y Justificaciones",
        "description": "Marcación de asistencias (Ingreso/Salida), justificaciones con foto física en uploads/justificaciones/, revisión y disparo de resumen diario (10:30 AM).",
        "item": [
            req(
                name="Resumen General de Asistencias del Día",
                method="GET",
                url="{{base_url}}/asistencias/resumen",
                desc="Métricas en tiempo real de colaboradores presentes, a tiempo, tardanzas y faltas."
            ),
            req(
                name="Asistencias Recientes del Día",
                method="GET",
                url="{{base_url}}/asistencias/recientes?limite=15",
                desc="Últimas marcas de asistencia registradas hoy en tiempo real."
            ),
            req(
                name="Listar Colaboradores y su Asistencia",
                method="GET",
                url="{{base_url}}/asistencias/colaboradores",
                desc="Lista de todo el personal y su estado de asistencia de la jornada actual."
            ),
            req(
                name="Listar Colaboradores (Ruta raíz /colaboradores)",
                method="GET",
                url="{{base_host}}/colaboradores",
                desc="Ruta directa de compatibilidad para consultar colaboradores."
            ),
            req(
                name="Última Asistencia del Usuario",
                method="GET",
                url="{{base_url}}/asistencias/ultima?idUsuario=8",
                desc="Devuelve el último registro de asistencia de un colaborador para validar si ya marcó ingreso o salida."
            ),
            req(
                name="Última Asistencia (Ruta raíz /asistencias/ultima)",
                method="GET",
                url="{{base_host}}/asistencias/ultima?idUsuario=8",
                desc="Ruta directa de compatibilidad para consultar la última asistencia del usuario."
            ),
            req(
                name="Historial de Asistencias por Colaborador",
                method="GET",
                url="{{base_url}}/asistencias/historial/8",
                desc="Histórico detallado de todas las marcas de asistencia del colaborador indicado."
            ),
            req(
                name="Historial de Asistencias (Ruta raíz /historial/:id)",
                method="GET",
                url="{{base_host}}/historial/8",
                desc="Ruta directa de compatibilidad para consultar el historial de un colaborador."
            ),
            req(
                name="Marcar Asistencia (Ingreso o Salida)",
                method="POST",
                url="{{base_url}}/asistencias/marcar",
                desc="Registra la marca de INGRESO o SALIDA del colaborador. Calcula automáticamente tardanza según la hora oficial.",
                body={
                    "idUsuario": 8,
                    "tipo": "INGRESO",
                    "latitud": -6.771198,
                    "longitud": -79.838557,
                    "direccion": "Av. Balta 123, Chiclayo",
                    "sede": "Chiclayo Central",
                    "fechaHoraDispositivo": "2026-11-19 09:15:00"
                }
            ),
            req(
                name="Marcar Asistencia (Ruta directa /marcar)",
                method="POST",
                url="{{base_host}}/marcar",
                desc="Ruta directa alternativa utilizada por clientes móviles para registrar asistencia.",
                body={
                    "idUsuario": 8,
                    "tipo": "INGRESO",
                    "latitud": -6.771198,
                    "longitud": -79.838557
                }
            ),
            req(
                name="Registrar Justificación (Base64)",
                method="POST",
                url="{{base_url}}/asistencias/justificar",
                desc="Envía justificación de falta o tardanza. Guarda la imagen en uploads/justificaciones/justif_{idUsuario}_{ts}.jpg y la ruta en JUSTIFICACIONES.ruta_sustento.",
                body={
                    "idUsuario": 8,
                    "motivo": "SALUD",
                    "descripcion": "Cita médica por descanso de 24 horas",
                    "fecha": "2026-11-19",
                    "fotoSustentoBase64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Registrar Justificación (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/asistencias/justificar",
                desc="Permite adjuntar el archivo físico de sustento médico mediante multipart/form-data (campo 'foto').",
                formdata=[
                    {"key": "idUsuario", "value": "8", "type": "text"},
                    {"key": "motivo", "value": "SALUD", "type": "text"},
                    {"key": "descripcion", "value": "Descanso médico emitido por ESSALUD", "type": "text"},
                    {"key": "fecha", "value": "2026-11-19", "type": "text"},
                    {"key": "foto", "type": "file", "src": "", "description": "Certificado o receta médica física"}
                ]
            ),
            req(
                name="Registrar Justificación (Ruta directa /justificar)",
                method="POST",
                url="{{base_host}}/justificar",
                desc="Ruta directa alternativa para enviar justificación desde la app.",
                body={
                    "idUsuario": 8,
                    "motivo": "TRAFICO",
                    "descripcion": "Cierre de vías por mantenimiento",
                    "fecha": "2026-11-19"
                }
            ),
            req(
                name="Ver Justificaciones de un Usuario",
                method="GET",
                url="{{base_url}}/asistencias/justificacion/8",
                desc="Consulta la última o todas las justificaciones enviadas por un colaborador y su estado (PENDIENTE, APROBADA, RECHAZADA)."
            ),
            req(
                name="Ver Justificaciones (Ruta raíz /justificacion/:id)",
                method="GET",
                url="{{base_host}}/justificacion/8",
                desc="Ruta directa alternativa para consultar justificaciones de un usuario."
            ),
            req(
                name="Revisar Justificación (Aprobar / Rechazar)",
                method="POST",
                url="{{base_url}}/asistencias/justificacion/revisar",
                desc="El Administrador o Supervisor aprueba o rechaza la justificación. Al aprobar, el estado de la asistencia cambia a A_TIEMPO.",
                body={
                    "idUsuario": 8,
                    "idAsistencia": 15,
                    "idRevisor": 1,
                    "estado": "APROBADA",
                    "comentario": "Descanso médico válido presentado a tiempo"
                }
            ),
            req(
                name="Revisar Justificación (Ruta raíz /justificacion/revisar)",
                method="POST",
                url="{{base_host}}/justificacion/revisar",
                desc="Ruta directa alternativa para revisar y validar justificaciones."
            ),
            req(
                name="Disparar Notificación de Resumen Diario (POST /api/asistencias/notificar-resumen)",
                method="POST",
                url="{{base_url}}/asistencias/notificar-resumen",
                desc="Ejecuta manualmente el resumen diario de asistencias y envía las notificaciones push a los Administradores y Supervisores.",
                auth_inherit=False
            ),
            req(
                name="Disparar Notificación de Resumen Diario (GET /api/asistencias/notificar-resumen)",
                method="GET",
                url="{{base_url}}/asistencias/notificar-resumen",
                desc="Permite invocar el resumen de asistencias mediante método GET para tareas automatizadas tipo cron web.",
                auth_inherit=False
            ),
            req(
                name="Disparar Notificación de Resumen (Ruta raíz POST /notificar-resumen)",
                method="POST",
                url="{{base_host}}/notificar-resumen",
                desc="Ruta raíz directa para ejecutar el resumen de asistencias diario.",
                auth_inherit=False
            ),
            req(
                name="Disparar Notificación de Resumen (Ruta raíz GET /notificar-resumen)",
                method="GET",
                url="{{base_host}}/notificar-resumen",
                desc="Ruta raíz directa GET alternativa para webhook o cron job.",
                auth_inherit=False
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SUPERVISIÓN Y CONTROL
    # ─────────────────────────────────────────────────────────────────────────
    supervision_folder = {
        "name": "6. Supervisión y Control",
        "description": "Gestión de personal de campo, puntos de venta, alertas de stock, atención de incidencias y reasignaciones.",
        "item": [
            req(
                name="Resumen General de Supervisión (Dashboard)",
                method="GET",
                url="{{base_url}}/supervision/resumen",
                desc="Métricas globales para el supervisor: total de personal activo, puntos cubiertos, alertas pendientes e incidencias del día."
            ),
            req(
                name="Listar Mejores Vendedores",
                method="GET",
                url="{{base_url}}/supervision/vendedores",
                desc="Ranking de vendedores por volumen de ventas y cumplimiento de metas comerciales."
            ),
            req(
                name="Detalle de Vendedor",
                method="GET",
                url="{{base_url}}/supervision/vendedores/8",
                desc="Perfil comercial completo del vendedor: histórico de ventas, puntos asignados y efectividad."
            ),
            req(
                name="Historial de Asignaciones de Vendedor",
                method="GET",
                url="{{base_url}}/supervision/vendedores/8/historial-asignaciones",
                desc="Locales y rutas que ha tenido asignados el vendedor a lo largo del tiempo."
            ),
            req(
                name="Historial de Asignaciones (Alias /personal/:id/historial-asignaciones)",
                method="GET",
                url="{{base_url}}/supervision/personal/8/historial-asignaciones",
                desc="Ruta alias para consultar historial de asignaciones de personal."
            ),
            req(
                name="Historial de Asignaciones (Alias /impulsadores/:id/historial-asignaciones)",
                method="GET",
                url="{{base_url}}/supervision/impulsadores/8/historial-asignaciones",
                desc="Ruta alias para consultar historial de asignaciones de impulsadores."
            ),
            req(
                name="Rendimiento Histórico de Vendedor",
                method="GET",
                url="{{base_url}}/supervision/vendedores/8/rendimiento-historico",
                desc="Gráfico y métricas de desempeño histórico de ventas del colaborador."
            ),
            req(
                name="Rendimiento Histórico (Alias /personal/:id/rendimiento-historico)",
                method="GET",
                url="{{base_url}}/supervision/personal/8/rendimiento-historico",
                desc="Ruta alias para consultar rendimiento histórico de personal."
            ),
            req(
                name="Rendimiento Histórico (Alias /impulsadores/:id/rendimiento-historico)",
                method="GET",
                url="{{base_url}}/supervision/impulsadores/8/rendimiento-historico",
                desc="Ruta alias para consultar rendimiento histórico de impulsadores."
            ),
            req(
                name="Reasignar Vendedor a Punto de Venta (POST)",
                method="POST",
                url="{{base_url}}/supervision/vendedores/8/reasignar",
                desc="Cambia el punto de venta donde opera el vendedor y registra el motivo en la auditoría.",
                body={
                    "idPuntosVenta": 2,
                    "motivo": "Relevo por incremento de demanda de fin de semana"
                }
            ),
            req(
                name="Reasignar Vendedor (PUT /supervision/vendedores/:id/reasignar)",
                method="PUT",
                url="{{base_url}}/supervision/vendedores/8/reasignar",
                desc="Método PUT alternativo para reasignar vendedor a otro local.",
                body={
                    "idPuntosVenta": 2,
                    "motivo": "Reasignación de zona"
                }
            ),
            req(
                name="Reasignar Personal (Alias POST /personal/:id/reasignar)",
                method="POST",
                url="{{base_url}}/supervision/personal/8/reasignar",
                desc="Ruta alias para reasignar personal de campo.",
                body={
                    "idPuntosVenta": 2,
                    "motivo": "Reasignación operativa"
                }
            ),
            req(
                name="Reasignar Personal (Alias PUT /personal/:id/reasignar)",
                method="PUT",
                url="{{base_url}}/supervision/personal/8/reasignar",
                desc="Ruta alias PUT para reasignar personal.",
                body={
                    "idPuntosVenta": 2,
                    "motivo": "Rotación periódica"
                }
            ),
            req(
                name="Reasignar Impulsador (Alias POST /impulsadores/:id/reasignar)",
                method="POST",
                url="{{base_url}}/supervision/impulsadores/8/reasignar",
                desc="Ruta alias POST para reasignar impulsadores.",
                body={
                    "idPuntosVenta": 2,
                    "motivo": "Cobertura especial"
                }
            ),
            req(
                name="Reasignar Impulsador (Alias PUT /impulsadores/:id/reasignar)",
                method="PUT",
                url="{{base_url}}/supervision/impulsadores/8/reasignar",
                desc="Ruta alias PUT para reasignar impulsadores.",
                body={
                    "idPuntosVenta": 2,
                    "motivo": "Rotación comercial"
                }
            ),
            req(
                name="Reasignar Impulsador (Ruta Global /reasignar-impulsador)",
                method="POST",
                url="{{base_url}}/supervision/reasignar-impulsador",
                desc="Endpoint centralizado para cambiar de local a cualquier impulsador.",
                body={
                    "idUsuario": 8,
                    "idPuntosVenta": 3,
                    "motivo": "Cobertura en Plaza Norte"
                }
            ),
            req(
                name="Listar Impulsadores (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/impulsadores",
                desc="Lista todo el personal de campo registrado para supervisión operativa."
            ),
            req(
                name="Foto de Impulsador",
                method="GET",
                url="{{base_url}}/supervision/impulsadores/8/foto",
                desc="Obtiene la foto de perfil del impulsador indicado."
            ),
            req(
                name="Listar Puntos de Venta (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta",
                desc="Lista todos los puntos de venta con métricas de ventas y cobertura de impulsadores."
            ),
            req(
                name="Detalle de Punto de Venta (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/1",
                desc="Ficha completa del punto de venta con estado, responsable y coordenadas."
            ),
            req(
                name="Stock de Productos en Punto de Venta",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/1/stock",
                desc="Consulta el inventario actual de botellas en exhibición y almacén del punto de venta."
            ),
            req(
                name="Stock de Productos (Alias /productos)",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/1/productos",
                desc="Ruta alternativa para obtener el inventario de productos del punto de venta."
            ),
            req(
                name="Historial de Impulsadores en Punto de Venta",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/1/historial",
                desc="Historial de colaboradores que han estado destacados en este local comercial."
            ),
            req(
                name="Reasignar Impulsador desde Punto de Venta (POST)",
                method="POST",
                url="{{base_url}}/supervision/puntos-venta/1/reasignar",
                desc="Asigna un nuevo impulsador al punto de venta indicado.",
                body={
                    "idUsuario": 8,
                    "motivo": "Cobertura del turno tarde"
                }
            ),
            req(
                name="Reasignar Impulsador desde PDV (PUT)",
                method="PUT",
                url="{{base_url}}/supervision/puntos-venta/1/reasignar",
                desc="Método PUT para reasignar impulsador a un punto de venta.",
                body={
                    "idUsuario": 8,
                    "motivo": "Relevo semanal"
                }
            ),
            req(
                name="Listar Alertas de Stock Pendientes",
                method="GET",
                url="{{base_url}}/supervision/alertas?estado=PENDIENTE",
                desc="Lista las alertas por quiebre de stock o producto crítico en anaqueles."
            ),
            req(
                name="Detalle de Alerta de Stock",
                method="GET",
                url="{{base_url}}/supervision/alertas/1",
                desc="Detalle del producto en desabastecimiento, punto de venta y fecha de la alerta."
            ),
            req(
                name="Cambiar Estado de Alerta (PATCH)",
                method="PATCH",
                url="{{base_url}}/supervision/alertas/1/estado",
                desc="Actualiza el estado de la alerta de stock con un comentario explicativo.",
                body={
                    "estado": "ATENDIDA",
                    "comentario": "Se despachó pedido de emergencia de 24 unidades"
                }
            ),
            req(
                name="Cambiar Estado de Alerta (PUT)",
                method="PUT",
                url="{{base_url}}/supervision/alertas/1/estado",
                desc="Método PUT para cambiar el estado de la alerta.",
                body={
                    "estado": "ATENDIDA",
                    "comentario": "Stock repuesto en tienda"
                }
            ),
            req(
                name="Cambiar Estado de Alerta (POST)",
                method="POST",
                url="{{base_url}}/supervision/alertas/1/estado",
                desc="Método POST para cambiar el estado de la alerta.",
                body={
                    "estado": "ATENDIDA",
                    "comentario": "Alerta atendida satisfactoriamente"
                }
            ),
            req(
                name="Marcar Alerta como Atendida (PUT)",
                method="PUT",
                url="{{base_url}}/supervision/alertas/1/atender",
                desc="Acceso directo para marcar la alerta como resuelta/atendida.",
                body={
                    "comentario": "Stock repuesto en tienda satisfactoriamente"
                }
            ),
            req(
                name="Marcar Alerta como Atendida (POST)",
                method="POST",
                url="{{base_url}}/supervision/alertas/1/atender",
                desc="Método POST alternativo para marcar la alerta como atendida.",
                body={
                    "comentario": "Mercadería recibida en góndola"
                }
            ),
            req(
                name="Marcar Alerta como Ignorada (PUT)",
                method="PUT",
                url="{{base_url}}/supervision/alertas/1/ignorar",
                desc="Ignora la alerta (por ejemplo, si el producto se retiró de exhibición deliberadamente).",
                body={
                    "comentario": "Local en inventario general"
                }
            ),
            req(
                name="Marcar Alerta como Ignorada (POST)",
                method="POST",
                url="{{base_url}}/supervision/alertas/1/ignorar",
                desc="Método POST alternativo para ignorar una alerta de stock.",
                body={
                    "comentario": "Producto descontinuado temporalmente"
                }
            ),
            req(
                name="Listar Incidencias (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/incidencias?estado=PENDIENTE&severidad=ALTA",
                desc="Bandeja de incidencias reportadas en campo para gestión y resolución por supervisión."
            ),
            req(
                name="Detalle de Incidencia (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/incidencias/1",
                desc="Información completa de la incidencia y fecha de reporte."
            ),
            req(
                name="Atender / Resolver Incidencia (PUT)",
                method="PUT",
                url="{{base_url}}/supervision/incidencias/1/atender",
                desc="El supervisor da por atendida o resuelta la incidencia registrando la solución aplicada.",
                body={
                    "estado": "RESUELTO",
                    "comentario": "Se coordinó con el área logística la reposición del material dañado"
                }
            ),
            req(
                name="Atender / Resolver Incidencia (POST)",
                method="POST",
                url="{{base_url}}/supervision/incidencias/1/atender",
                desc="Método POST alternativo para resolver una incidencia.",
                body={
                    "estado": "RESUELTO",
                    "comentario": "Incidencia atendida en local"
                }
            ),
            req(
                name="Foto de Incidencia (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/incidencias/1/foto",
                desc="Descarga la imagen de sustento de la incidencia para auditoría."
            ),
            req(
                name="Foto de Producto en Supervisión",
                method="GET",
                url="{{base_url}}/supervision/productos/1/foto",
                desc="Descarga o visualiza la fotografía oficial del producto."
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 7. PROSPECTOS (PUNTOS POTENCIALES)
    # ─────────────────────────────────────────────────────────────────────────
    prospectos_folder = {
        "name": "7. Prospectos (Puntos Potenciales)",
        "description": "Registro de clientes potenciales, fotos de fachada (físicas en uploads/evidencias/ y uploads/prospectos/), pipeline de negociación, conversión automática a Punto de Venta (Distribución) y seguimientos.",
        "item": [
            req(
                name="Listar Prospectos (Con Filtros)",
                method="GET",
                url="{{base_url}}/prospectos?estado=NUEVO&potencial=ALTO",
                desc="Lista prospectos. Filtros: ?estado=NUEVO, EN_NEGOCIACION, CONVERTIDO, DESCARTADO y ?potencial=ALTO, MEDIO, BAJO."
            ),
            req(
                name="Detalle de Prospecto por ID",
                method="GET",
                url="{{base_url}}/prospectos/1",
                desc="Obtiene los datos completos del prospecto junto con todo su historial de seguimientos comerciales."
            ),
            req(
                name="Registrar Nuevo Prospecto (JSON con Base64 / Ruta)",
                method="POST",
                url="{{base_url}}/prospectos",
                desc="Registra un prospecto. Si envía foto_fachada o url_foto en Base64, el servidor la guarda en uploads/evidencias/ y registra la ruta corta en MySQL.",
                body={
                    "nombre_comercial": "Licorería El Parral",
                    "tipo_local": "Licorería",
                    "direccion": "Av. Bolognesi 450",
                    "contacto": "Juan Pérez",
                    "telefono": "978123456",
                    "potencial": "ALTO",
                    "estado": "NUEVO",
                    "latitud": -6.772500,
                    "longitud": -79.840200,
                    "idDistrito": 1,
                    "notas": "Interesado en cócteles de crema para temporada de verano",
                    "url_foto": "uploads/prospectos/prospecto_parral.jpg"
                }
            ),
            req(
                name="Registrar Nuevo Prospecto (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/prospectos",
                desc="Permite registrar el prospecto adjuntando directamente el archivo físico de fachada (campo 'foto').",
                formdata=[
                    {"key": "nombre_comercial", "value": "Bodega Santa Rosa", "type": "text"},
                    {"key": "tipo_local", "value": "Bodega", "type": "text"},
                    {"key": "direccion", "value": "Calle Dos de Mayo 1291", "type": "text"},
                    {"key": "contacto", "value": "Alfonso Llontop", "type": "text"},
                    {"key": "telefono", "value": "999792030", "type": "text"},
                    {"key": "potencial", "value": "MEDIO", "type": "text"},
                    {"key": "estado", "value": "NUEVO", "type": "text"},
                    {"key": "latitud", "value": "-6.771234", "type": "text"},
                    {"key": "longitud", "value": "-79.839876", "type": "text"},
                    {"key": "idDistrito", "value": "1", "type": "text"},
                    {"key": "notas", "value": "Cliente con buen flujo peatonal", "type": "text"},
                    {"key": "foto", "type": "file", "src": "", "description": "Fotografía de fachada del local"}
                ]
            ),
            req(
                name="Actualizar Datos de Prospecto",
                method="PUT",
                url="{{base_url}}/prospectos/1",
                desc="Modifica datos de contacto, dirección, notas o potencial del prospecto.",
                body={
                    "contacto": "Juan Pérez Gómez",
                    "telefono": "978654321",
                    "potencial": "ALTO",
                    "notas": "Se acordó segunda visita comercial con degustación"
                }
            ),
            req(
                name="Cambiar Estado de Prospecto (Al CONVERTIR -> Crea Punto de Venta en BD)",
                method="PUT",
                url="{{base_url}}/prospectos/1/estado",
                desc="Actualiza el estado: NUEVO, EN_NEGOCIACION, CONVERTIDO o DESCARTADO. Si se envía CONVERTIDO, la API crea automáticamente un registro en PUNTOS_VENTA con tipo DISTRIBUCIÓN.",
                body={
                    "estado": "CONVERTIDO"
                }
            ),
            req(
                name="Cambiar Estado a EN_NEGOCIACION",
                method="PUT",
                url="{{base_url}}/prospectos/1/estado",
                desc="Pasa el estado a EN_NEGOCIACION cuando se inician tratos formales.",
                body={
                    "estado": "EN_NEGOCIACION"
                }
            ),
            req(
                name="Descartar Prospecto (Con Motivo de Descarte)",
                method="PATCH",
                url="{{base_url}}/prospectos/1/estado",
                desc="Pasa el estado a DESCARTADO especificando el motivo del descarte en MySQL.",
                body={
                    "estado": "DESCARTADO",
                    "motivo_descarte": "Volumen de compra muy bajo para venta mayorista"
                }
            ),
            req(
                name="Asignar Promotor a Prospecto (PUT)",
                method="PUT",
                url="{{base_url}}/prospectos/1/asignar",
                desc="Asigna el promotor responsable de cerrar la negociación con el prospecto.",
                body={
                    "idUsuario": 8
                }
            ),
            req(
                name="Asignar Promotor a Prospecto (POST)",
                method="POST",
                url="{{base_url}}/prospectos/1/asignar",
                desc="Ruta POST alternativa para asignar promotor comercial a un prospecto.",
                body={
                    "idUsuario": 8
                }
            ),
            req(
                name="Registrar Seguimiento Comercial (Visita / Llamada)",
                method="POST",
                url="{{base_url}}/prospectos/1/seguimientos",
                desc="Registra una acción de seguimiento comercial realizada sobre el prospecto.",
                body={
                    "tipo_contacto": "VISITA",
                    "observacion": "Se entregaron muestras de Licor de Jamaica y lista de precios mayorista",
                    "acuerdos": "El dueño responderá el día viernes para el primer pedido",
                    "proximo_contacto": "2026-11-22 10:00:00"
                }
            ),
            req(
                name="Listar Seguimientos de un Prospecto",
                method="GET",
                url="{{base_url}}/prospectos/1/seguimientos",
                desc="Obtiene la cronología completa de visitas, llamadas y acuerdos realizados con el prospecto."
            ),
            req(
                name="Actualizar Foto de Prospecto (Base64)",
                method="PUT",
                url="{{base_url}}/prospectos/1/foto",
                desc="Guarda la fotografía física en uploads/prospectos/prospecto_1.jpg y actualiza url_foto en la BD.",
                body={
                    "foto_fachada": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Actualizar Foto de Prospecto (Multipart Form-Data)",
                method="POST",
                url="{{base_url}}/prospectos/1/foto",
                desc="Sube la fotografía física de fachada de un prospecto existente en multipart/form-data (campo 'foto').",
                formdata=[
                    {"key": "foto", "type": "file", "src": "", "description": "Archivo de imagen de fachada"}
                ]
            ),
            req(
                name="Obtener Foto de Prospecto (Stream)",
                method="GET",
                url="{{base_url}}/prospectos/1/foto",
                desc="Retorna en streaming binario la imagen física registrada del prospecto."
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 8. DISPOSITIVO Y NOTIFICACIONES PUSH
    # ─────────────────────────────────────────────────────────────────────────
    dispositivo_folder = {
        "name": "8. Dispositivo y Notificaciones Push",
        "description": "Registro de dispositivo físico para geolocalización, sincronización y notificaciones push FCM.",
        "item": [
            req(
                name="Actualizar Dispositivo del Usuario",
                method="PUT",
                url="{{base_url}}/dispositivo",
                desc="Registra el identificador único del hardware, modelo y token FCM del usuario.",
                body={
                    "id_dispositivo": "android_hardware_device_uuid_987654",
                    "modelo": "Samsung Galaxy S23 Ultra",
                    "sistema_operativo": "Android 14",
                    "fcm_token": "fcm_token_valido_de_firebase_cloud_messaging"
                }
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 9. ARCHIVOS Y MULTIMEDIA (UPLOADS)
    # ─────────────────────────────────────────────────────────────────────────
    uploads_folder = {
        "name": "9. Archivos y Multimedia (Uploads)",
        "description": "Rutas estáticas para descargar y servir fotos de perfil, evidencias e imágenes subidas en el servidor.",
        "item": [
            req(
                name="Estado del Servidor API (Ruta Raíz /)",
                method="GET",
                url="{{base_host}}/",
                desc="Verifica la disponibilidad del servidor Flask y estado de la API REST.",
                auth_inherit=False
            ),
            req(
                name="Servir Foto de Prospecto (Prefijo /api/uploads)",
                method="GET",
                url="{{base_url}}/uploads/prospectos/prospecto_1.jpg",
                desc="Sirve directamente cualquier archivo en uploads/ a través de la ruta estándar /api/uploads/<carpeta>/<archivo>.",
                auth_inherit=False
            ),
            req(
                name="Servir Foto de Perfil (Ruta Raíz /uploads)",
                method="GET",
                url="{{base_host}}/uploads/perfiles/user_8.jpg",
                desc="Sirve directamente el archivo físico alojado en la carpeta uploads/ desde la raíz del dominio.",
                auth_inherit=False
            ),
            req(
                name="Servir Evidencia de Incidencia o Reposición",
                method="GET",
                url="{{base_url}}/uploads/evidencias/incidencia_8_1700000000.jpg",
                desc="Descarga la foto de evidencia física guardada para incidencias o reposición de stock.",
                auth_inherit=False
            ),
            req(
                name="Servir Sustento de Justificación",
                method="GET",
                url="{{base_url}}/uploads/justificaciones/justif_8_1700000000.jpg",
                desc="Descarga la foto del certificado médico o justificación laboral.",
                auth_inherit=False
            ),
            req(
                name="Servir Foto de Punto de Venta",
                method="GET",
                url="{{base_url}}/uploads/prospectos/pdv_20.jpg",
                desc="Descarga la foto de fachada del punto de venta.",
                auth_inherit=False
            )
        ]
    }

    collection["item"] = [
        auth_folder,
        pdv_folder,
        pedidos_folder,
        productos_folder,
        impulsador_folder,
        asistencia_folder,
        supervision_folder,
        prospectos_folder,
        dispositivo_folder,
        uploads_folder
    ]

    return collection

if __name__ == "__main__":
    col = build_collection()
    
    # 1. Guardar en postman/PiccoliField_API_Collection.json
    os.makedirs("postman", exist_ok=True)
    target1 = os.path.join("postman", "PiccoliField_API_Collection.json")
    with open(target1, "w", encoding="utf-8") as f:
        json.dump(col, f, indent=2, ensure_ascii=False)
    print(f"Colección guardada exitosamente en: {target1}")

    # 2. Guardar en la raíz como PiccoliField API - Despacho y Puntos de Distribución.postman_collection.json
    target2 = "PiccoliField API - Despacho y Puntos de Distribución.postman_collection.json"
    with open(target2, "w", encoding="utf-8") as f:
        json.dump(col, f, indent=2, ensure_ascii=False)
    print(f"Colección actualizada en la raíz: {target2}")
