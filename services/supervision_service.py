import os
from config import Config, BASE_DIR
from database import get_connection
from repositories.supervision_repository import SupervisionRepository

class SupervisionService:
    def listar_mejores_vendedores(self):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_mejores_vendedores()
            
            if data is None:
                return None, "Error interno al obtener los vendedores", 500
                
            if len(data) == 0:
                return [], "No se encontraron ventas registradas", 200
                
            return data, "Mejores vendedores listados exitosamente", 200
            
        except Exception as e:
            print(f"Error en el servicio de supervisión: {e}")
            return None, "Ocurrió un error inesperado", 500
        finally:
            connection.close()

    def obtener_resumen_dashboard(self):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_resumen()
            return data, "Resumen obtenido exitosamente", 200
        except Exception as e:
            print(f"Error resumen dashboard: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def obtener_detalle_vendedor(self, idUsuario):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_detalle_vendedor(idUsuario)
            if not data:
                return None, "Vendedor no encontrado o no tiene ventas", 404
            return data, "Detalle obtenido exitosamente", 200
        except Exception as e:
            print(f"Error detalle vendedor: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()
            
    def obtener_detalle_alerta(self, idAlerta):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_detalle_alerta(idAlerta)
            if not data:
                return None, "Alerta no encontrada", 404
            return data, "Detalle obtenido exitosamente", 200
        except Exception as e:
            print(f"Error detalle alerta: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def listar_puntos_venta(self):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.listar_puntos_venta()
            
            if data is None:
                return None, "Error interno al obtener puntos de venta", 500
                
            return data, "Puntos de venta obtenidos exitosamente", 200
        except Exception as e:
            print(f"Error en listar_puntos_venta: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def obtener_detalle_punto_venta(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_detalle_punto_venta(idPuntosVenta)
            if not data:
                return None, "Punto de venta no encontrado o no es de tipo VENTA", 404
            return data, "Detalle del punto de venta obtenido exitosamente", 200
        except Exception as e:
            print(f"Error detalle punto venta: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def obtener_historial_impulsadores(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data, message = repo.obtener_historial_impulsadores(idPuntosVenta)
            if data is None:
                return None, message, 404
            return data, message, 200
        except Exception as e:
            print(f"Error historial impulsadores: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def reasignar_impulsador(self, idPuntosVenta, idUsuario, idUsuarioRegistra, motivo=None):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data, message, http_code = repo.reasignar_impulsador(
                idPuntosVenta=idPuntosVenta,
                idUsuario=idUsuario,
                idUsuarioRegistra=idUsuarioRegistra,
                motivo=motivo
            )
            return data, message, http_code
        except Exception as e:
            print(f"Error reasignar impulsador: {e}")
            return None, "Error interno al reasignar impulsador", 500
        finally:
            connection.close()

    def listar_impulsadores(self):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.listar_impulsadores()
            if data is None:
                return None, "Error interno al obtener impulsadores", 500
            return data, "Impulsadores listados exitosamente", 200
        except Exception as e:
            print(f"Error en listar_impulsadores: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def obtener_ruta_foto_impulsador(self, idUsuario):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            usuario = repo.buscar_foto_impulsador(idUsuario)
            if not usuario:
                return None, "Usuario no encontrado", 404

            foto = usuario.get("url_foto")
            if foto:
                nombre_archivo = os.path.basename(foto)
                ruta_directa = os.path.join(Config.PROFILE_PHOTO_DIR, nombre_archivo)
                if os.path.isfile(ruta_directa):
                    return ruta_directa, "Foto encontrada", 200

                ruta_relativa = os.path.join(BASE_DIR, foto)
                if os.path.isfile(ruta_relativa):
                    return ruta_relativa, "Foto encontrada", 200

            # Fallback a default.png si existe
            default_foto = os.path.join(Config.PROFILE_PHOTO_DIR, "default.png")
            if os.path.isfile(default_foto):
                return default_foto, "Foto por defecto", 200

            return None, "No se encontró foto ni imagen por defecto", 404
        except Exception as e:
            print(f"Error foto impulsador: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def obtener_ruta_foto_producto(self, idProductos):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            producto = repo.buscar_foto_producto(idProductos)
            if not producto:
                return None, "Producto no encontrado", 404

            foto = producto.get("url_foto")
            if foto:
                nombre_archivo = os.path.basename(foto)
                ruta_directa = os.path.join(Config.PRODUCT_PHOTO_DIR, nombre_archivo)
                if os.path.isfile(ruta_directa):
                    return ruta_directa, "Imagen encontrada", 200

                ruta_relativa = os.path.join(BASE_DIR, foto)
                if os.path.isfile(ruta_relativa):
                    return ruta_relativa, "Imagen encontrada", 200

            return None, "El producto no tiene una imagen registrada", 404
        except Exception as e:
            print(f"Error foto producto: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def listar_alertas(self):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.listar_alertas()
            
            if data is None:
                return None, "Error interno al obtener alertas", 500
                
            return data, "Alertas obtenidas exitosamente", 200
        except Exception as e:
            print(f"Error en listar_alertas: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()
