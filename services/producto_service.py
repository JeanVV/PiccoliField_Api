from database import get_connection
from repositories.producto_repository import ProductoRepository


class ProductoService:

    def listar_productos(self, search=None, categoria=None):
        connection = get_connection()
        try:
            repo = ProductoRepository(connection)
            productos = repo.listar_activos(search=search, categoria=categoria)
            return productos, "Catálogo de productos obtenido correctamente", 200
        finally:
            connection.close()

    def obtener_por_id(self, idProductos):
        connection = get_connection()
        try:
            repo = ProductoRepository(connection)
            producto = repo.buscar_por_id(idProductos)
            if not producto:
                return None, "Producto no encontrado", 404
            return producto, "Producto obtenido correctamente", 200
        finally:
            connection.close()

    def buscar_por_ean(self, codigo):
        connection = get_connection()
        try:
            if not codigo or not str(codigo).strip():
                return None, "Código EAN o SKU inválido", 400

            repo = ProductoRepository(connection)
            producto = repo.buscar_por_ean_o_sku(codigo)
            if not producto:
                return None, f"No se encontró ningún producto con el código {codigo}", 404
            return producto, "Producto encontrado correctamente", 200
        finally:
            connection.close()

