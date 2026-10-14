import math

class PuntoVentaRepository:
    def __init__(self, connection):
        self.connection = connection

    def listar_todos(self, search=None, distrito=None, estado="ACTIVO"):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.codigo,
                    pv.puntosVenta,
                    pv.direccion,
                    pv.estado,
                    pv.latitud,
                    pv.longitud,
                    d.distrito,
                    p.provincia,
                    dep.departamento,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE 1=1
            """
            params = []

            if estado:
                sql += " AND pv.estado = %s"
                params.append(estado)

            if distrito:
                sql += " AND (pv.idDistrito = %s OR d.distrito LIKE %s)"
                params.append(distrito)
                params.append(f"%{distrito}%")

            if search:
                sql += " AND (pv.puntosVenta LIKE %s OR pv.direccion LIKE %s OR pv.codigo LIKE %s)"
                term = f"%{search}%"
                params.extend([term, term, term])

            sql += " ORDER BY pv.idPuntosVenta DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def buscar_cercanos(self, lat, lng, radio_km=10):
        cursor = self.connection.cursor()
        try:
            # Fórmula de Haversine para cálculo de distancia en Km
            sql = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.codigo,
                    pv.puntosVenta,
                    pv.direccion,
                    pv.estado,
                    pv.latitud,
                    pv.longitud,
                    d.distrito,
                    ROUND(
                        6371 * acos(
                            cos(radians(%s)) * cos(radians(pv.latitud)) * 
                            cos(radians(pv.longitud) - radians(%s)) + 
                            sin(radians(%s)) * sin(radians(pv.latitud))
                        ), 2
                    ) AS distancia_km
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                WHERE pv.estado = 'ACTIVO'
                HAVING distancia_km <= %s
                ORDER BY distancia_km ASC
            """
            cursor.execute(sql, (lat, lng, lat, radio_km))
            return cursor.fetchall()
        finally:
            cursor.close()

    def buscar_por_id(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.codigo,
                    pv.puntosVenta,
                    pv.direccion,
                    pv.estado,
                    pv.latitud,
                    pv.longitud,
                    pv.idDistrito,
                    d.distrito,
                    p.provincia,
                    dep.departamento,
                    pv.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado,
                    u.correo AS promotor_correo
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE pv.idPuntosVenta = %s
                LIMIT 1
            """
            cursor.execute(sql, (idPuntosVenta,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def productos_por_punto(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pr.idProductos,
                    pr.sku,
                    pr.codigo_ean,
                    pr.producto,
                    pr.categoria,
                    pr.presentacion,
                    COALESCE(sr.cant_exhibida, 0) AS cant_exhibida,
                    COALESCE(sr.cant_almacen, 0) AS cant_almacen,
                    COALESCE(sr.estado_stock, 'OPTIMO') AS estado_stock,
                    sr.fecha AS ultima_actualizacion
                FROM PRODUCTOS pr
                LEFT JOIN (
                    SELECT s1.*
                    FROM STOCK_REGISTROS s1
                    INNER JOIN (
                        SELECT idProductos, MAX(idStock) as max_id
                        FROM STOCK_REGISTROS
                        WHERE idPuntosVenta = %s
                        GROUP BY idProductos
                    ) s2 ON s1.idStock = s2.max_id
                ) sr ON pr.idProductos = sr.idProductos
                WHERE pr.estado = 'ACTIVO'
                ORDER BY pr.idProductos ASC
            """
            cursor.execute(sql, (idPuntosVenta,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def crear(self, data):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO PUNTOS_VENTA (
                    codigo, puntosVenta, direccion, estado, latitud, longitud, idDistrito, idUsuario
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data["codigo"],
                data["puntosVenta"],
                data["direccion"],
                data.get("estado", "ACTIVO"),
                data["latitud"],
                data["longitud"],
                data["idDistrito"],
                data["idUsuario"]
            ))
            self.connection.commit()
            return cursor.lastrowid
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def actualizar(self, idPuntosVenta, data):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE PUNTOS_VENTA
                SET puntosVenta = %s,
                    direccion = %s,
                    latitud = %s,
                    longitud = %s,
                    idDistrito = %s
                WHERE idPuntosVenta = %s
            """
            cursor.execute(sql, (
                data["puntosVenta"],
                data["direccion"],
                data["latitud"],
                data["longitud"],
                data["idDistrito"],
                idPuntosVenta
            ))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def cambiar_estado(self, idPuntosVenta, estado):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE PUNTOS_VENTA SET estado = %s WHERE idPuntosVenta = %s"
            cursor.execute(sql, (estado, idPuntosVenta))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def mapa_calor_pedidos(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.puntosVenta,
                    pv.direccion,
                    pv.latitud,
                    pv.longitud,
                    COUNT(p.idPedido) AS total_pedidos,
                    COALESCE(SUM(p.cantSolicitada), 0) AS total_unidades_solicitadas,
                    CASE 
                        WHEN COALESCE(SUM(p.cantSolicitada), 0) >= 100 THEN 'ALTO'
                        WHEN COALESCE(SUM(p.cantSolicitada), 0) >= 30 THEN 'MEDIO'
                        ELSE 'BAJO'
                    END AS intensidad_calor
                FROM PUNTOS_VENTA pv
                LEFT JOIN Pedido p ON pv.idPuntosVenta = p.idPuntosVenta
                WHERE pv.estado = 'ACTIVO'
                GROUP BY pv.idPuntosVenta, pv.puntosVenta, pv.direccion, pv.latitud, pv.longitud
                ORDER BY total_unidades_solicitadas DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def historial_pedidos(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    p.idPedido,
                    p.cantSolicitada,
                    p.fecha,
                    pr.idProductos,
                    pr.sku,
                    pr.producto,
                    pr.presentacion
                FROM Pedido p
                INNER JOIN PRODUCTOS pr ON p.idProductos = pr.idProductos
                WHERE p.idPuntosVenta = %s
                ORDER BY p.fecha DESC
            """
            cursor.execute(sql, (idPuntosVenta,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def resumen_demanda(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    COUNT(p.idPedido) AS total_pedidos,
                    COALESCE(SUM(p.cantSolicitada), 0) AS total_unidades,
                    MAX(p.fecha) AS ultimo_pedido,
                    (
                        SELECT pr2.producto 
                        FROM Pedido p2
                        INNER JOIN PRODUCTOS pr2 ON p2.idProductos = pr2.idProductos
                        WHERE p2.idPuntosVenta = %s
                        GROUP BY pr2.idProductos, pr2.producto
                        ORDER BY SUM(p2.cantSolicitada) DESC
                        LIMIT 1
                    ) AS producto_mas_pedido
                FROM Pedido p
                WHERE p.idPuntosVenta = %s
            """
            cursor.execute(sql, (idPuntosVenta, idPuntosVenta))
            return cursor.fetchone()
        finally:
            cursor.close()
