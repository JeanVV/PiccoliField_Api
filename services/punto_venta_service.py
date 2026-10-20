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
