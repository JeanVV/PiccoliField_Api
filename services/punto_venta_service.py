from database import get_connection
from repositories.punto_venta_repository import PuntoVentaRepository

class PuntoVentaService:

    def listar_puntos(self, search=None, distrito=None, estado="ACTIVO"):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            puntos = repo.listar_todos(search=search, distrito=distrito, estado=estado)
            return puntos, "Puntos de venta obtenidos correctamente", 200
        finally:
            connection.close()

    def buscar_cercanos(self, lat, lng, radio_km=10):
        try:
            lat = float(lat)
            lng = float(lng)
            radio_km = float(radio_km)
        except (ValueError, TypeError):
            return None, "Latitud, longitud y radio deben ser valores numéricos válidos", 400

        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            puntos = repo.buscar_cercanos(lat, lng, radio_km)
            return puntos, f"Se encontraron {len(puntos)} puntos cercanos", 200
        finally:
            connection.close()

    def obtener_detalle(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            punto = repo.buscar_por_id(idPuntosVenta)
            if not punto:
                return None, "Punto de distribución no encontrado", 404
            return punto, "Detalle obtenido correctamente", 200
        finally:
            connection.close()

    def obtener_productos(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            punto = repo.buscar_por_id(idPuntosVenta)
            if not punto:
                return None, "Punto de distribución no encontrado", 404

            productos = repo.productos_por_punto(idPuntosVenta)
            return productos, "Productos del punto obtenidos correctamente", 200
        finally:
            connection.close()

    def crear_punto(self, data):
        required = ["codigo", "puntosVenta", "direccion", "latitud", "longitud", "idDistrito", "idUsuario"]
        for field in required:
            if field not in data or data[field] is None:
                return None, f"El campo '{field}' es obligatorio", 400

        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            nuevo_id = repo.crear(data)
            punto = repo.buscar_por_id(nuevo_id)
            return punto, "Punto de distribución creado exitosamente", 201
        except Exception as e:
            return None, f"Error al registrar punto: {str(e)}", 500
        finally:
            connection.close()

    def actualizar_punto(self, idPuntosVenta, data):
        required = ["puntosVenta", "direccion", "latitud", "longitud", "idDistrito"]
        for field in required:
            if field not in data or data[field] is None:
                return None, f"El campo '{field}' es obligatorio", 400

        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            punto = repo.buscar_por_id(idPuntosVenta)
            if not punto:
                return None, "Punto de distribución no encontrado", 404

            repo.actualizar(idPuntosVenta, data)
            actualizado = repo.buscar_por_id(idPuntosVenta)
            return actualizado, "Punto de distribución actualizado correctamente", 200
        except Exception as e:
            return None, f"Error al actualizar punto: {str(e)}", 500
        finally:
            connection.close()

    def cambiar_estado(self, idPuntosVenta, estado):
        if estado not in ["ACTIVO", "INACTIVO", "CLAUSURADO"]:
            return None, "Estado no válido. Debe ser ACTIVO, INACTIVO o CLAUSURADO", 400

        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            punto = repo.buscar_por_id(idPuntosVenta)
            if not punto:
                return None, "Punto de distribución no encontrado", 404

            repo.cambiar_estado(idPuntosVenta, estado)
            return {"idPuntosVenta": idPuntosVenta, "estado": estado}, f"Estado cambiado a {estado}", 200
        except Exception as e:
            return None, f"Error al cambiar estado: {str(e)}", 500
        finally:
            connection.close()

    def mapa_calor(self):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            datos = repo.mapa_calor_pedidos()
            return datos, "Datos de mapa de calor obtenidos correctamente", 200
        finally:
            connection.close()

    def historial_pedidos(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            punto = repo.buscar_por_id(idPuntosVenta)
            if not punto:
                return None, "Punto de distribución no encontrado", 404

            historial = repo.historial_pedidos(idPuntosVenta)
            return historial, "Historial de pedidos obtenido correctamente", 200
        finally:
            connection.close()

    def resumen_demanda(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            punto = repo.buscar_por_id(idPuntosVenta)
            if not punto:
                return None, "Punto de distribución no encontrado", 404

            resumen = repo.resumen_demanda(idPuntosVenta)
            return resumen, "Resumen de demanda obtenido correctamente", 200
        finally:
            connection.close()
