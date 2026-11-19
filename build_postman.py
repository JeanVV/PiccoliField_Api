import json
import os

def build_collection():
    collection = {
        "info": {
            "_postman_id": "piccolifield-full-api-v2-updated",
            "name": "PiccoliField API - Colección Completa (Actualizada)",
            "description": "Colección completa y exhaustiva con el 100% de rutas y endpoints de PiccoliField API.\nIncluye Autenticación, Perfil, Notificaciones, Puntos de Venta, Pedidos, Catálogo, Operaciones de Impulsador, Asistencias, Justificaciones, Supervisión, Prospectos, FCM y Archivos Multimedia.",
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
                "description": "URL base en Render. Para local usar: http://localhost:5000/api"
            },
            {
                "key": "base_host",
                "value": "https://piccolifield-api-smkc.onrender.com",
                "type": "string",
                "description": "Host raíz sin prefijo /api (para uploads y rutas directas)"
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

    def req(name, method, url, desc="", body=None, headers=None, auth_inherit=True, tests=None):
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

        if body is not None:
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
        "description": "Login, perfil de usuario, tokens FCM, fotos de perfil y notificaciones push.",
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
                desc="Actualiza la foto de perfil del usuario en sesión (formato Data URL base64 o ruta).",
                body={
                    "url_foto": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/..."
                }
            ),
            req(
                name="Obtener Mi Foto de Perfil (Stream)",
                method="GET",
                url="{{base_url}}/perfil/foto",
                desc="Devuelve la imagen física de la foto de perfil en streaming binario (JPEG/PNG)."
            ),
            req(
                name="Actualizar Foto de un Usuario por ID (Admin / Web)",
                method="PUT",
                url="{{base_url}}/usuarios/8/foto",
                desc="Permite al administrador actualizar la foto de perfil de cualquier usuario en la base de datos.",
                body={
                    "url_foto": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/..."
                }
            ),
            req(
                name="Obtener Foto de un Usuario por ID (Stream)",
                method="GET",
                url="{{base_url}}/usuarios/8/foto",
                desc="Retorna el archivo de imagen de perfil del usuario especificado por su idUsuario."
            ),
            req(
                name="Actualizar FCM Token de Mi Perfil (Push)",
                method="PUT",
                url="{{base_url}}/perfil/fcm-token",
                desc="Registra o actualiza el token de Firebase Cloud Messaging (FCM) del dispositivo móvil para recibir notificaciones push.",
                body={
                    "token": "fcm_token_generado_en_el_dispositivo_movil_firebase_123456",
                    "dispositivo_info": "Samsung Galaxy A54 (Android 14)"
                }
            ),
            req(
                name="Actualizar FCM Token (Ruta /api/usuario/fcm-token)",
                method="POST",
                url="{{base_url}}/usuario/fcm-token",
                desc="Ruta alias para registro de token FCM desde la aplicación móvil.",
                body={
                    "token": "fcm_token_generado_en_el_dispositivo_movil_firebase_123456",
                    "dispositivo_info": "Xiaomi Redmi Note 12"
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
        "description": "Gestión de puntos de venta (tipo VENTA o DISTRIBUCIÓN), asignación de promotores/responsables e historial.",
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
                name="Asignar Responsable / Promotor a Punto de Venta (Admin)",
                method="PUT",
                url="{{base_url}}/puntos-venta/20/responsable",
                desc="Asigna un promotor o vendedor responsable al punto de venta y registra el cambio en HISTORIAL_ASIGNACIONES.",
                body={
                    "idUsuario": 8,
                    "motivo": "Asignación de zona comercial norte"
                }
            ),
            req(
                name="Historial de Asignaciones del Punto de Venta",
                method="GET",
                url="{{base_url}}/puntos-venta/20/historial",
                desc="Lista el histórico de todos los promotores/vendedores que han sido asignados al punto de venta."
            ),
            req(
                name="Actualizar Foto de Punto de Venta (Base64 o Multipart)",
                method="PUT",
                url="{{base_url}}/puntos-venta/20/foto",
                desc="Guarda la fotografía de fachada del punto de venta en uploads/prospectos/pdv_20.jpg y actualiza url_foto en la base de datos.",
                body={
                    "foto_fachada": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Obtener Foto de Punto de Venta (Stream)",
                method="GET",
                url="{{base_url}}/puntos-venta/20/foto",
                desc="Retorna en streaming binario la imagen del punto de venta o del prospecto del que fue convertido."
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
                desc="Registra un pedido vinculando el idPuntosVenta desde la URL (ideal para app Android móvil).",
                body={
                    "idProductos": 1,
                    "cantSolicitada": 3
                }
            ),
            req(
                name="Listar Pedidos de un Punto Específico",
                method="GET",
                url="{{base_url}}/puntos-venta/20/pedidos",
                desc="Obtiene todos los pedidos asociados al punto de venta especificado en la ruta."
            ),
            req(
                name="Actualizar Estado del Pedido (Despacho - Admin)",
                method="PUT",
                url="{{base_url}}/pedidos/1/estado",
                desc="Cambia el estado del pedido: REGISTRADO -> EN_PREPARACION -> ENTREGADO (o CANCELADO). Solo para Administrador.",
                body={
                    "estado": "EN_PREPARACION"
                }
            ),
            req(
                name="Actualizar Estado a ENTREGADO (Despacho)",
                method="PATCH",
                url="{{base_url}}/pedidos/1/estado",
                desc="Marca el pedido como ENTREGADO una vez despachado y entregado al punto de distribución.",
                body={
                    "estado": "ENTREGADO"
                }
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. CATÁLOGO DE PRODUCTOS
    # ─────────────────────────────────────────────────────────────────────────
    productos_folder = {
        "name": "3. Catálogo de Productos",
        "description": "Catálogo general de licores y macerados de Piccoli.",
        "item": [
            req(
                name="Listar Catálogo de Productos Activos",
                method="GET",
                url="{{base_url}}/productos",
                desc="Obtiene la lista de productos activos de la empresa con SKU, EAN, precios y categoría."
            ),
            req(
                name="Buscar Producto por Código EAN o SKU",
                method="GET",
                url="{{base_url}}/productos/ean/7751234567890",
                desc="Busca un producto por su código de barras EAN o su código SKU único."
            ),
            req(
                name="Detalle de Producto por ID",
                method="GET",
                url="{{base_url}}/productos/1",
                desc="Devuelve la ficha técnica completa del producto especificado por su idProductos."
            )
        ]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. IMPULSADOR (OPERACIONES EN CAMPO E INCIDENCIAS)
    # ─────────────────────────────────────────────────────────────────────────
    impulsador_folder = {
        "name": "4. Impulsador (Operaciones en Campo e Incidencias)",
        "description": "Dashboard, ventas con lector de barras, reposición de stock, incidencias y catálogo del local asignado.",
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
                name="Reponer Stock de Producto",
                method="POST",
                url="{{base_url}}/impulsador/stock/reponer",
                desc="Actualiza las unidades en exhibición y almacén del producto en el punto de venta.",
                body={
                    "idProductos": 1,
                    "cantExhibida": 15,
                    "cantAlmacen": 30,
                    "idPuntosVenta": 1,
                    "observacion": "Reposición matutina de anaqueles"
                }
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
                name="Reportar Incidencia en Local",
                method="POST",
                url="{{base_url}}/impulsador/incidencias",
                desc="Registra una incidencia detectada en el punto de venta con nivel de severidad y sustento.",
                body={
                    "tipo": "ROTURA",
                    "descripcion": "Se quebró una botella de licor de cacao en el pasillo central",
                    "severidad": "MEDIA",
                    "idPuntosVenta": 1,
                    "foto": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
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
        "description": "Marcación de asistencias (Ingreso/Salida), justificaciones, revisión y disparo de resumen diario (10:30 AM).",
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
                name="Historial de Asistencias por Colaborador",
                method="GET",
                url="{{base_url}}/asistencias/historial/8",
                desc="Histórico detallado de todas las marcas de asistencia del colaborador indicado."
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
                name="Registrar Justificación de Inasistencia / Tardanza",
                method="POST",
                url="{{base_url}}/asistencias/justificar",
                desc="Envía una justificación de falta o tardanza con motivo, descripción y foto de sustento médica/laboral.",
                body={
                    "idUsuario": 8,
                    "motivo": "SALUD",
                    "descripcion": "Cita médica por descanso de 24 horas",
                    "fecha": "2026-11-19",
                    "fotoSustentoBase64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
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
                name="Disparar Notificación de Resumen Diario (10:30 AM / Manual)",
                method="POST",
                url="{{base_url}}/asistencias/notificar-resumen",
                desc="Ejecuta manualmente el resumen diario de asistencias y envía las notificaciones push a los Administradores y Supervisores.",
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
                name="Detalle de Vendedor por ID",
                method="GET",
                url="{{base_url}}/supervision/vendedores/8",
                desc="Ficha completa del vendedor, local actual asignado y resumen de rendimiento."
            ),
            req(
                name="Historial de Asignaciones de Vendedor",
                method="GET",
                url="{{base_url}}/supervision/vendedores/8/historial-asignaciones",
                desc="Locales y puntos de venta donde ha sido asignado el colaborador históricamente."
            ),
            req(
                name="Rendimiento Histórico de Vendedor",
                method="GET",
                url="{{base_url}}/supervision/vendedores/8/rendimiento-historico?anio=2026",
                desc="Ventas mensuales acumuladas a lo largo del año para análisis de desempeño."
            ),
            req(
                name="Reasignar Vendedor a Punto de Venta",
                method="PUT",
                url="{{base_url}}/supervision/vendedores/8/reasignar",
                desc="Cambia el local asignado de un vendedor e inserta registro en HISTORIAL_ASIGNACIONES.",
                body={
                    "idPuntosVenta": 2,
                    "motivo": "Refuerzo comercial por campaña navideña"
                }
            ),
            req(
                name="Listar Todos los Impulsadores",
                method="GET",
                url="{{base_url}}/supervision/impulsadores",
                desc="Lista de impulsadores con sus locales asignados y estado actual."
            ),
            req(
                name="Foto de Impulsador",
                method="GET",
                url="{{base_url}}/supervision/impulsadores/8/foto",
                desc="Devuelve la foto del impulsador para visualización en el panel de supervisión."
            ),
            req(
                name="Reasignar Personal (Ruta Genérica /personal/:id/reasignar)",
                method="POST",
                url="{{base_url}}/supervision/personal/8/reasignar",
                desc="Ruta unificada para reasignar cualquier tipo de personal de campo a un nuevo punto de venta.",
                body={
                    "idPuntosVenta": 3,
                    "motivo": "Reubicación estratégica de zona"
                }
            ),
            req(
                name="Reasignar Impulsador (Ruta Directa por Body)",
                method="POST",
                url="{{base_url}}/supervision/reasignar-impulsador",
                desc="Reasignación enviando tanto el idPuntosVenta como el idUsuario en el cuerpo JSON.",
                body={
                    "idPuntosVenta": 2,
                    "idUsuario": 8,
                    "motivo": "Rotación programada de personal"
                }
            ),
            req(
                name="Listar Puntos de Venta (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta?estado=ACTIVO",
                desc="Lista todos los locales comerciales con su impulsador asignado, stock y estado."
            ),
            req(
                name="Detalle de Punto de Venta (Supervisión)",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/1",
                desc="Ficha completa del punto de venta con dirección, coordenadas y responsable."
            ),
            req(
                name="Historial de Impulsadores en Punto de Venta",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/1/historial",
                desc="Lista de todos los colaboradores que han estado a cargo del punto de venta."
            ),
            req(
                name="Reasignar Impulsador desde el Punto de Venta",
                method="PUT",
                url="{{base_url}}/supervision/puntos-venta/1/reasignar",
                desc="Asigna un nuevo impulsador al punto de venta especificado en la URL.",
                body={
                    "idUsuario": 8,
                    "motivo": "Cubrir descanso médico del titular"
                }
            ),
            req(
                name="Stock de Productos en Punto de Venta",
                method="GET",
                url="{{base_url}}/supervision/puntos-venta/1/stock",
                desc="Stock actual en góndola y almacén de todos los productos en el local seleccionado."
            ),
            req(
                name="Listar Alertas de Stock",
                method="GET",
                url="{{base_url}}/supervision/alertas",
                desc="Lista alertas generadas cuando el stock cae por debajo del nivel mínimo (PENDIENTE / ATENDIDA / IGNORADA)."
            ),
            req(
                name="Detalle de Alerta de Stock",
                method="GET",
                url="{{base_url}}/supervision/alertas/1",
                desc="Detalle del producto en desabastecimiento, punto de venta y fecha de la alerta."
            ),
            req(
                name="Cambiar Estado de Alerta (Atender / Ignorar)",
                method="PATCH",
                url="{{base_url}}/supervision/alertas/1/estado",
                desc="Actualiza el estado de la alerta de stock con un comentario explicativo.",
                body={
                    "estado": "ATENDIDA",
                    "comentario": "Se despachó pedido de emergencia de 24 unidades"
                }
            ),
            req(
                name="Marcar Alerta como Atendida",
                method="PUT",
                url="{{base_url}}/supervision/alertas/1/atender",
                desc="Acceso directo para marcar la alerta como resuelta/atendida.",
                body={
                    "comentario": "Stock repuesto en tienda satisfactoriamente"
                }
            ),
            req(
                name="Marcar Alerta como Ignorada",
                method="PUT",
                url="{{base_url}}/supervision/alertas/1/ignorar",
                desc="Ignora la alerta (por ejemplo, si el producto se retiró de exhibición deliberadamente).",
                body={
                    "comentario": "Local en inventario general"
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
                name="Atender / Resolver Incidencia",
                method="PUT",
                url="{{base_url}}/supervision/incidencias/1/atender",
                desc="El supervisor da por atendida o resuelta la incidencia registrando la solución aplicada.",
                body={
                    "estado": "RESUELTO",
                    "comentario": "Se coordinó con el área logística la reposición del material dañado"
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
        "description": "Registro de clientes potenciales, pipeline de negociación, conversión automática a Punto de Venta (Distribución) y seguimientos.",
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
                name="Registrar Nuevo Prospecto",
                method="POST",
                url="{{base_url}}/prospectos",
                desc="Registra un nuevo prospecto comercial en la base de datos.",
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
                name="Cambiar Estado de Prospecto (Al CONVERTIR -> Crea Punto de Venta)",
                method="PUT",
                url="{{base_url}}/prospectos/1/estado",
                desc="Actualiza el estado: NUEVO, EN_NEGOCIACION, CONVERTIDO o DESCARTADO. Si se envía CONVERTIDO, la API crea automáticamente un registro en PUNTOS_VENTA con tipo DISTRIBUCIÓN.",
                body={
                    "estado": "CONVERTIDO"
                }
            ),
            req(
                name="Descartar Prospecto (Con Motivo)",
                method="PATCH",
                url="{{base_url}}/prospectos/1/estado",
                desc="Pasa el estado a DESCARTADO especificando el motivo del descarte.",
                body={
                    "estado": "DESCARTADO",
                    "motivo_descarte": "Volumen de compra muy bajo para venta mayorista"
                }
            ),
            req(
                name="Asignar Promotor a Prospecto",
                method="PUT",
                url="{{base_url}}/prospectos/1/asignar",
                desc="Asigna el promotor responsable de cerrar la negociación con el prospecto.",
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
                name="Actualizar Foto de Prospecto (Base64 o Multipart)",
                method="PUT",
                url="{{base_url}}/prospectos/1/foto",
                desc="Guarda la fotografía de fachada del prospecto en uploads/prospectos/prospecto_1.jpg y actualiza url_foto en la base de datos.",
                body={
                    "foto_fachada": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                }
            ),
            req(
                name="Obtener Foto de Prospecto (Stream)",
                method="GET",
                url="{{base_url}}/prospectos/1/foto",
                desc="Retorna en streaming binario la imagen registrada del prospecto."
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
        "description": "Rutas estáticas para descargar y servir fotos de perfil, evidencias e imágenes subidas.",
        "item": [
            req(
                name="Servir Archivo / Foto Subida (Prefijo /api/uploads)",
                method="GET",
                url="{{base_url}}/uploads/prospectos/prospecto_1.jpg",
                desc="Sirve directamente cualquier archivo en uploads/ a través de la ruta estándar /api/uploads/<carpeta>/<archivo>.",
                auth_inherit=False
            ),
            req(
                name="Servir Archivo / Foto Subida (Ruta Raíz /uploads)",
                method="GET",
                url="{{base_host}}/uploads/perfiles/user_8.jpg",
                desc="Sirve directamente el archivo físico alojado en la carpeta uploads/ desde la raíz del dominio.",
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
