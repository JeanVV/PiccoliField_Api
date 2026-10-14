from database import get_connection
from repositories.control_repository import ControlRepository

class ControlService:

    def listar_promotores(self):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            promotores = repo.listar_promotores()
            return promotores, "Promotores obtenidos correctamente", 200
        finally:
            connection.close()

    def asignar_punto(self, idUsuario, idPuntosVenta):
        if not idUsuario or not idPuntosVenta:
            return None, "idUsuario e idPuntosVenta son obligatorios", 400

        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            repo.asignar_punto(idUsuario, idPuntosVenta)
            return {
                "idUsuario": idUsuario,
                "idPuntosVenta": idPuntosVenta
            }, "Promotor asignado correctamente al punto de venta", 200
        except Exception as e:
            return None, f"Error al asignar promotor: {str(e)}", 500
        finally:
            connection.close()

    def desasignar_punto(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            repo.desasignar_punto(idPuntosVenta)
            return {
                "idPuntosVenta": idPuntosVenta
            }, "Punto de venta desasignado correctamente", 200
        except Exception as e:
            return None, f"Error al desasignar punto: {str(e)}", 500
        finally:
            connection.close()

    def puntos_por_promotor(self, idUsuario):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            puntos = repo.puntos_por_promotor(idUsuario)
            return puntos, "Puntos del promotor obtenidos correctamente", 200
        finally:
            connection.close()

    def asistencias_supervision(self, fecha=None):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            asistencias = repo.asistencias_supervision(fecha=fecha)
            return asistencias, "Asistencias de supervisión obtenidas correctamente", 200
        finally:
            connection.close()

    def alertas_stock(self, estado="PENDIENTE"):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            alertas = repo.alertas_stock(estado=estado)
            return alertas, "Alertas de stock obtenidas correctamente", 200
        finally:
            connection.close()

    def atender_alerta(self, idAlertas, comentario=None):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            repo.atender_alerta(idAlertas, comentario=comentario)
            return {
                "idAlertas": idAlertas,
                "estado": "ATENDIDA"
            }, "Alerta de stock atendida exitosamente", 200
        except Exception as e:
            return None, f"Error al atender alerta: {str(e)}", 500
        finally:
            connection.close()

    def dashboard_kpis(self):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            kpis = repo.dashboard_kpis()
            return kpis, "Métricas KPI obtenidas correctamente", 200
        finally:
            connection.close()

    def categorias_locales(self):
        categorias = [
            {"id": "todos", "nombre": "Todos", "icono": "store"},
            {"id": "tiendas", "nombre": "Tiendas", "icono": "shop"},
            {"id": "supermercados", "nombre": "Supermercados", "icono": "shopping_cart"},
            {"id": "bares_restaurantes", "nombre": "Bares y restaurantes", "icono": "local_bar"}
        ]
        return categorias, "Categorías obtenidas correctamente", 200

    def productos_destacados(self):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            productos = repo.productos_destacados()
            return productos, "Cócteles y productos obtenidos correctamente", 200
        finally:
            connection.close()

    def distritos_activos(self):
        connection = get_connection()
        try:
            repo = ControlRepository(connection)
            distritos = repo.distritos_activos()
            return distritos, "Distritos activos obtenidos correctamente", 200
        finally:
            connection.close()
