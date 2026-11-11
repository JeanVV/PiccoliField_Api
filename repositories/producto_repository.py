class ProductoRepository:
    def __init__(self, connection):
        self.connection = connection

    def listar_activos(self, search=None, categoria=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idProductos,
                    sku,
                    codigo_ean,
                    producto,
                    categoria,
                    precio,
                    descripcion,
                    url_foto,
                    estado
                FROM PRODUCTOS
                WHERE estado = 'ACTIVO'
            """
            params = []

            if categoria:
                sql += " AND categoria = %s"
                params.append(categoria)

            if search:
                sql += " AND (producto LIKE %s OR sku LIKE %s OR codigo_ean LIKE %s)"
                term = f"%{search}%"
                params.extend([term, term, term])

            sql += " ORDER BY idProductos ASC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def buscar_por_id(self, idProductos):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idProductos,
                    sku,
                    codigo_ean,
                    producto,
                    categoria,
                    precio,
                    descripcion,
                    url_foto,
                    estado
                FROM PRODUCTOS
                WHERE idProductos = %s
                LIMIT 1
            """
            cursor.execute(sql, (idProductos,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def buscar_por_ean_o_sku(self, codigo):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idProductos,
                    sku,
                    codigo_ean,
                    producto,
                    categoria,
                    precio,
                    descripcion,
                    url_foto,
                    estado
                FROM PRODUCTOS
                WHERE (codigo_ean = %s OR sku = %s) AND estado = 'ACTIVO'
                LIMIT 1
            """
            cursor.execute(sql, (str(codigo).strip(), str(codigo).strip()))
            return cursor.fetchone()
        finally:
            cursor.close()

