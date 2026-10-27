import base64
import hashlib
import os
import time
from config import Config, BASE_DIR
from database import get_connection
from repositories.impulsador_repository import ImpulsadorRepository


class ImpulsadorService:
    # ── 1. DASHBOARD COMPLETO DEL IMPULSADOR ──────────────────────────────────
    def obtener_dashboard(self, idUsuario):
        connection = get_connection()
        try:
            repo = ImpulsadorRepository(connection)
            usuario = repo.obtener_datos_impulsador(idUsuario)
            if not usuario:
                return None, "Usuario no encontrado", 404

            # Local asignado
            pdv = repo.obtener_asignacion_actual(idUsuario)

            # Resumen de ventas
            ventas = repo.obtener_resumen_ventas(idUsuario)

            # Meta de ventas y cálculo de progreso
            meta = usuario.get("meta_ventas", 0) or 0
            monto_mes = ventas.get("monto_mes", 0)
            progreso_porcentaje = 0.0
            if meta > 0:
                progreso_porcentaje = round(min(100.0, (monto_mes / meta) * 100), 1)

            # Resumen de inventario del local
            inventario = {"total_productos": 0, "stock_bajo": 0, "stock_agotado": 0}
            if pdv and "idPuntosVenta" in pdv:
                inventario = repo.obtener_resumen_inventario_pdv(pdv["idPuntosVenta"])

            # Horario configurado
            horario = repo.obtener_horario()

            data = {
                "impulsador": {
                    "idUsuario": usuario["idUsuario"],
                    "nombre": usuario["nombre_completo"],
                    "correo": usuario["correo"],
                    "rol": usuario["rol"],
                    "url_foto": usuario["url_foto"],
                    "meta_ventas": meta
                },
                "punto_venta": pdv,
                "tiene_asignacion": pdv is not None,
                "progreso_ventas": {
                    "meta_mensual": meta,
                    "monto_hoy": ventas["monto_hoy"],
                    "unidades_hoy": ventas["unidades_hoy"],
                    "transacciones_hoy": ventas["transacciones_hoy"],
                    "monto_mes": ventas["monto_mes"],
                    "unidades_mes": ventas["unidades_mes"],
                    "porcentaje_alcanzado": progreso_porcentaje
                },
                "inventario_resumen": inventario,
                "horario": horario
            }

            return data, "Dashboard de impulsador obtenido correctamente", 200

        except Exception as e:
            print(f"Error en obtener_dashboard impulsador: {e}")
            return None, f"Error interno al obtener dashboard: {str(e)}", 500
        finally:
            connection.close()

    # ── 2. HISTORIAL DE LOCALES ───────────────────────────────────────────────
    def obtener_historial(self, idUsuario):
        connection = get_connection()
        try:
            repo = ImpulsadorRepository(connection)
            data = repo.obtener_historial_asignaciones(idUsuario)
            return data, "Historial de asignaciones obtenido correctamente", 200
        except Exception as e:
            print(f"Error en obtener_historial impulsador: {e}")
            return None, f"Error interno al obtener historial: {str(e)}", 500
        finally:
            connection.close()

    # ── 3. BUSCAR PRODUCTO POR CÓDIGO DE BARRAS / SKU ─────────────────────────
    def buscar_producto(self, idUsuario, codigo, idPuntosVenta=None):
        if not codigo or not str(codigo).strip():
            return None, "Debe ingresar o escanear un código de barras o SKU", 400

        connection = get_connection()
        try:
            repo = ImpulsadorRepository(connection)

            # Si no se pasó idPuntosVenta explícito, usar el asignado actualmente
            if not idPuntosVenta:
                pdv = repo.obtener_asignacion_actual(idUsuario)
                if not pdv:
                    return None, "No tiene un punto de venta asignado actualmente", 400
                idPuntosVenta = pdv["idPuntosVenta"]

            producto = repo.buscar_producto_por_codigo(idPuntosVenta, codigo)
            if not producto:
                return None, f"No se encontró ningún producto con código '{codigo}' en su local", 404

            # Estado amigable para el BottomSheet de Android
            stock = producto["stock_actual"]
            stock_min = producto["stock_minimo"]
            if stock == 0:
                disponibilidad = "AGOTADO"
            elif stock <= stock_min:
                disponibilidad = "BAJO"
            else:
                disponibilidad = "DISPONIBLE"

            data = {
                "idProductos": producto["idProductos"],
                "sku": producto["sku"],
                "codigo_ean": producto["codigo_ean"],
                "producto": producto["producto"],
                "categoria": producto["categoria"],
                "descripcion": producto["descripcion"],
                "url_foto": producto["url_foto"],
                "precio": float(producto["precio"]),
                "stock_actual": stock,
                "stock_minimo": stock_min,
                "disponibilidad": disponibilidad,
                "puede_vender": stock > 0,
                "idPuntosVenta": idPuntosVenta
            }

            return data, "Producto encontrado", 200

        except Exception as e:
            print(f"Error en buscar_producto: {e}")
            return None, f"Error interno al buscar producto: {str(e)}", 500
        finally:
            connection.close()

    # ── 4. LISTAR PRODUCTOS DEL LOCAL ─────────────────────────────────────────
    def listar_productos_local(self, idUsuario, search=None, idPuntosVenta=None):
        connection = get_connection()
        try:
            repo = ImpulsadorRepository(connection)

            if not idPuntosVenta:
                pdv = repo.obtener_asignacion_actual(idUsuario)
                if not pdv:
                    return [], "No tiene un punto de venta asignado actualmente", 200
                idPuntosVenta = pdv["idPuntosVenta"]

            data = repo.listar_productos_pdv(idPuntosVenta, search=search)
            for item in data:
                item["precio"] = float(item["precio"])

            return data, "Productos listados exitosamente", 200
        except Exception as e:
            print(f"Error en listar_productos_local: {e}")
            return None, f"Error interno: {str(e)}", 500
        finally:
            connection.close()

    # ── 5. REGISTRAR VENTA POR CÓDIGO DE BARRAS ────────────────────────────────
    def registrar_venta(self, idUsuario, payload):
        codigo_barras = payload.get("codigo_barras") or payload.get("codigo") or payload.get("codigo_ean")
        idProductos = payload.get("idProductos")
        cantidad = payload.get("cantidad", 1)
        idPuntosVenta = payload.get("idPuntosVenta")

        try:
            cantidad = int(cantidad)
            if cantidad <= 0:
                return None, "La cantidad a vender debe ser mayor a 0", 400
        except (ValueError, TypeError):
            return None, "La cantidad debe ser un número entero válido", 400

        if not codigo_barras and not idProductos:
            return None, "Debe enviar 'codigo_barras' o 'idProductos'", 400

        connection = get_connection()
        try:
            repo = ImpulsadorRepository(connection)

            # Determinar el punto de venta
            if not idPuntosVenta:
                pdv = repo.obtener_asignacion_actual(idUsuario)
                if not pdv:
                    return None, "El usuario no tiene un punto de venta asignado actualmente", 400
                idPuntosVenta = pdv["idPuntosVenta"]

            # Si se envió código de barras pero no idProductos, resolver producto
            if not idProductos:
                prod = repo.buscar_producto_por_codigo(idPuntosVenta, codigo_barras)
                if not prod:
                    return None, f"No se encontró ningún producto con código '{codigo_barras}' en este local", 404
                idProductos = prod["idProductos"]

            # Ejecutar venta en el repositorio
            resultado, mensaje, http_code = repo.registrar_venta(
                idUsuario=idUsuario,
                idPuntosVenta=idPuntosVenta,
                idProductos=idProductos,
                cantidad=cantidad
            )

            return resultado, mensaje, http_code

        except Exception as e:
            print(f"Error en registrar_venta: {e}")
            return None, f"Error interno al procesar la venta: {str(e)}", 500
        finally:
            connection.close()

    # ── 6. REPORTAR INCIDENCIA ─────────────────────────────────────────────────
    def reportar_incidencia(self, idUsuario, payload, archivo_foto=None):
        tipo = str(payload.get("tipo", "")).strip().upper()
        severidad = str(payload.get("severidad", "MEDIA")).strip().upper()
        descripcion = str(payload.get("descripcion", "")).strip()
        idPuntosVenta = payload.get("idPuntosVenta")
        foto_base64 = payload.get("foto_base64")

        if not tipo:
            return None, "El campo 'tipo' de incidencia es obligatorio", 400
        if not descripcion:
            return None, "El campo 'descripcion' es obligatorio", 400

        if severidad not in ("ALTA", "MEDIA", "BAJA"):
            severidad = "MEDIA"

        connection = get_connection()
        try:
            repo = ImpulsadorRepository(connection)

            # Resolver punto de venta si no vino explícito
            if not idPuntosVenta:
                pdv = repo.obtener_asignacion_actual(idUsuario)
                if pdv:
                    idPuntosVenta = pdv["idPuntosVenta"]
                else:
                    return None, "No se pudo identificar el punto de venta del impulsador", 400

            ruta_relativa = None
            hash_sha = None

            # Manejo de fotografía (sea archivo Multipart o string Base64)
            evidencias_dir = getattr(Config, "EVIDENCIAS_DIR", os.path.join(BASE_DIR, "uploads", "evidencias"))
            os.makedirs(evidencias_dir, exist_ok=True)

            contenido_bytes = None
            nombre_archivo = f"incidencia_u{idUsuario}_{int(time.time())}.jpg"

            if archivo_foto and hasattr(archivo_foto, "read"):
                contenido_bytes = archivo_foto.read()
            elif foto_base64 and isinstance(foto_base64, str):
                try:
                    # Remover prefijo data:image/...;base64, si existe
                    if "base64," in foto_base64:
                        foto_base64 = foto_base64.split("base64,")[1]
                    contenido_bytes = base64.b64decode(foto_base64)
                except Exception as ex:
                    print(f"Error al decodificar base64: {ex}")

            if contenido_bytes:
                hash_sha = hashlib.sha256(contenido_bytes).hexdigest()
                ruta_fisica = os.path.join(evidencias_dir, nombre_archivo)
                with open(ruta_fisica, "wb") as f:
                    f.write(contenido_bytes)
                ruta_relativa = f"uploads/evidencias/{nombre_archivo}"

            resultado, mensaje, http_code = repo.registrar_incidencia(
                idUsuario=idUsuario,
                idPuntosVenta=idPuntosVenta,
                tipo=tipo,
                severidad=severidad,
                descripcion=descripcion,
                ruta_evidencia=ruta_relativa,
                hash_sha=hash_sha
            )

            return resultado, mensaje, http_code

        except Exception as e:
            print(f"Error en reportar_incidencia: {e}")
            return None, f"Error interno al reportar incidencia: {str(e)}", 500
        finally:
            connection.close()
