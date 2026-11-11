import json


class PedidoRepository:
    def __init__(self, connection):
        self.connection = connection

    def buscar_operacion_sync(self, idOperacion):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT idOperacion, tipo, resultado_json, fecha_proceso, idUsuario
                FROM OPERACIONES_SYNC
                WHERE idOperacion = %s
                LIMIT 1
            """
            cursor.execute(sql, (str(idOperacion),))
            row = cursor.fetchone()
            if row and row.get("resultado_json"):
                if isinstance(row["resultado_json"], str):
                    try:
                        row["resultado_json"] = json.loads(row["resultado_json"])
                    except Exception:
                        pass
            return row
        finally:
            cursor.close()

    def registrar_operacion_sync(self, idOperacion, tipo, resultado_json, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO OPERACIONES_SYNC (idOperacion, tipo, resultado_json, fecha_proceso, idUsuario)
                VALUES (%s, %s, %s, NOW(), %s)
            """
            data_str = json.dumps(resultado_json, ensure_ascii=False) if not isinstance(resultado_json, str) else resultado_json
            cursor.execute(sql, (str(idOperacion), tipo, data_str, idUsuario))
        finally:
            cursor.close()

    def obtener_por_id(self, idPedido):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    ped.idPedido,
                    ped.cantSolicitada,
                    ped.fecha,
                    ped.estado,
                    ped.idPuntosVenta,
                    pv.codigo AS codigo_pdv,
                    pv.puntoVenta,
                    pv.direccion AS direccion_pdv,
                    pv.tipo AS tipo_pdv,
                    pv.estado AS estado_pdv,
                    pv.idUsuario AS idPromotorResponsable,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_responsable,
                    ped.idProductos,
                    pr.sku,
                    pr.codigo_ean,
                    pr.producto,
                    pr.categoria,
                    pr.presentacion
                FROM Pedido ped
                INNER JOIN PUNTOS_VENTA pv ON ped.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN PRODUCTOS pr ON ped.idProductos = pr.idProductos
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE ped.idPedido = %s
                LIMIT 1
            """
            cursor.execute(sql, (idPedido,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def listar_pedidos(self, idUsuario=None, rol=None, idPuntosVenta=None, estado=None, tipo_pdv=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    ped.idPedido,
                    ped.cantSolicitada,
                    ped.fecha,
                    ped.estado,
                    ped.idPuntosVenta,
                    pv.codigo AS codigo_pdv,
                    pv.puntoVenta,
                    pv.direccion AS direccion_pdv,
                    pv.tipo AS tipo_pdv,
                    pv.idUsuario AS idPromotorResponsable,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_responsable,
                    ped.idProductos,
                    pr.sku,
                    pr.codigo_ean,
                    pr.producto,
                    pr.categoria,
                    pr.presentacion
                FROM Pedido ped
                INNER JOIN PUNTOS_VENTA pv ON ped.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN PRODUCTOS pr ON ped.idProductos = pr.idProductos
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE 1=1
            """
            params = []

            # Si es PROMOTOR, restringir solo a los PDV donde es responsable
            if rol == "PROMOTOR" and idUsuario is not None:
                sql += " AND pv.idUsuario = %s"
                params.append(idUsuario)

            if idPuntosVenta:
                sql += " AND ped.idPuntosVenta = %s"
                params.append(idPuntosVenta)

            if estado:
                sql += " AND ped.estado = %s"
                params.append(estado)

            if tipo_pdv:
                # Soportar con y sin tilde
                if tipo_pdv.upper() in ("DISTRIBUCION", "DISTRIBUCIÓN"):
                    sql += " AND pv.tipo IN ('DISTRIBUCION', 'DISTRIBUCIÓN')"
                else:
                    sql += " AND pv.tipo = %s"
                    params.append(tipo_pdv.upper())

            sql += " ORDER BY ped.fecha DESC, ped.idPedido DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def validar_pdv(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT idPuntosVenta, codigo, puntoVenta, estado, tipo, idUsuario
                FROM PUNTOS_VENTA
                WHERE idPuntosVenta = %s
                LIMIT 1
            """
            cursor.execute(sql, (idPuntosVenta,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def validar_producto(self, idProductos):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT idProductos, sku, codigo_ean, producto, estado
                FROM PRODUCTOS
                WHERE idProductos = %s
                LIMIT 1
            """
            cursor.execute(sql, (idProductos,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def crear_pedido(self, cantSolicitada, idPuntosVenta, idProductos, idOperacion=None, idUsuario=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO Pedido (cantSolicitada, fecha, estado, idPuntosVenta, idProductos)
                VALUES (%s, NOW(), 'REGISTRADO', %s, %s)
            """
            cursor.execute(sql, (cantSolicitada, idPuntosVenta, idProductos))
            idPedido = cursor.lastrowid

            pedido_creado = self.obtener_por_id(idPedido)

            if idOperacion and idUsuario:
                self.registrar_operacion_sync(idOperacion, "CREAR_PEDIDO", pedido_creado, idUsuario)

            self.connection.commit()
            return pedido_creado
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def actualizar_estado(self, idPedido, nuevo_estado):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE Pedido
                SET estado = %s
                WHERE idPedido = %s
            """
            cursor.execute(sql, (nuevo_estado, idPedido))
            self.connection.commit()
            return self.obtener_por_id(idPedido)
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

