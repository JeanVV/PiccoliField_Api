class PedidoRepository:
    def __init__(self, connection):
        self.connection = connection

    def listar_pedidos(self, idPuntosVenta=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    p.idPedido,
                    p.cantSolicitada,
                    p.fecha,
                    pv.idPuntosVenta,
                    pv.puntosVenta,
                    pv.direccion,
                    pr.idProductos,
                    pr.sku,
                    pr.producto,
                    pr.presentacion,
                    CASE 
                        WHEN sr.idStock IS NOT NULL THEN 'ENTREGADO'
                        ELSE 'PENDIENTE'
                    END AS estado_despacho,
                    sr.fecha AS fecha_entrega
                FROM Pedido p
                INNER JOIN PUNTOS_VENTA pv ON p.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN PRODUCTOS pr ON p.idProductos = pr.idProductos
                LEFT JOIN STOCK_REGISTROS sr ON p.idPedido = sr.PedidoidPedido
                WHERE 1=1
            """
            params = []
            if idPuntosVenta:
                sql += " AND p.idPuntosVenta = %s"
                params.append(idPuntosVenta)

            sql += " ORDER BY p.idPedido DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def buscar_por_id(self, idPedido):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    p.idPedido,
                    p.cantSolicitada,
                    p.fecha,
                    pv.idPuntosVenta,
                    pv.puntosVenta,
                    pv.direccion,
                    pr.idProductos,
                    pr.sku,
                    pr.producto,
                    pr.presentacion,
                    CASE 
                        WHEN sr.idStock IS NOT NULL THEN 'ENTREGADO'
                        ELSE 'PENDIENTE'
                    END AS estado_despacho
                FROM Pedido p
                INNER JOIN PUNTOS_VENTA pv ON p.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN PRODUCTOS pr ON p.idProductos = pr.idProductos
                LEFT JOIN STOCK_REGISTROS sr ON p.idPedido = sr.PedidoidPedido
                WHERE p.idPedido = %s
                LIMIT 1
            """
            cursor.execute(sql, (idPedido,))
            return cursor.fetchone()
        finally:
            cursor.close()

    # Transacción COMMIT / ROLLBACK: inserción de múltiples pedidos en una sola operación atómica
    def crear_pedido_multiple(self, idPuntosVenta, productos):
        cursor = self.connection.cursor()
        try:
            sql = "INSERT INTO Pedido (cantSolicitada, idPuntosVenta, idProductos) VALUES (%s, %s, %s)"
            pedidos_creados = []

            for item in productos:
                cursor.execute(sql, (item["cantSolicitada"], idPuntosVenta, item["idProductos"]))
                pedidos_creados.append(cursor.lastrowid)

            self.connection.commit()
            return pedidos_creados
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def actualizar(self, idPedido, cantSolicitada):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE Pedido SET cantSolicitada = %s WHERE idPedido = %s"
            cursor.execute(sql, (cantSolicitada, idPedido))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def eliminar(self, idPedido):
        cursor = self.connection.cursor()
        try:
            sql = "DELETE FROM Pedido WHERE idPedido = %s"
            cursor.execute(sql, (idPedido,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    # Transacción COMMIT / ROLLBACK: Confirmar entrega, actualizar stock y cerrar alertas
    def completar_entrega_transaccional(self, idPedido, cant_exhibida, cant_almacen, observacion="Entrega conforme"):
        cursor = self.connection.cursor()
        try:
            # 1. Obtener datos del pedido
            cursor.execute("SELECT idPuntosVenta, idProductos FROM Pedido WHERE idPedido = %s", (idPedido,))
            pedido = cursor.fetchone()
            if not pedido:
                raise ValueError("Pedido no encontrado")

            idPuntosVenta = pedido["idPuntosVenta"]
            idProductos = pedido["idProductos"]

            # 2. Registrar en STOCK_REGISTROS
            sql_stock = """
                INSERT INTO STOCK_REGISTROS (
                    cant_exhibida, cant_almacen, estado_stock, observacion, stock_minimo,
                    idPuntosVenta, idProductos, PedidoidPedido
                ) VALUES (%s, %s, 'OPTIMO', %s, 6, %s, %s, %s)
            """
            cursor.execute(sql_stock, (
                cant_exhibida,
                cant_almacen,
                observacion,
                idPuntosVenta,
                idProductos,
                idPedido
            ))

            # 3. Marcar alertas de stock previas como atendidas
            sql_alerta = """
                UPDATE ALERTAS_STOCK
                SET estado = 'ATENDIDA', fecha_atencion = NOW()
                WHERE idPuntosVenta = %s AND idProductos = %s AND estado = 'PENDIENTE'
            """
            cursor.execute(sql_alerta, (idPuntosVenta, idProductos))

            self.connection.commit()
            return True
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def listar_repartidores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idUsuario,
                    nombres,
                    apePaterno,
                    apeMaterno,
                    correo,
                    rol,
                    estado
                FROM USUARIOS
                WHERE estado = 'ACTIVO'
                ORDER BY nombres ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
