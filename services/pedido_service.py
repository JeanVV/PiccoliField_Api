from database import get_connection
from repositories.pedido_repository import PedidoRepository

class PedidoService:

    def listar_pedidos(self, idPuntosVenta=None):
        connection = get_connection()
        try:
            repo = PedidoRepository(connection)
            pedidos = repo.listar_pedidos(idPuntosVenta=idPuntosVenta)
            return pedidos, "Pedidos obtenidos correctamente", 200
        finally:
            connection.close()

    def obtener_detalle(self, idPedido):
        connection = get_connection()
        try:
            repo = PedidoRepository(connection)
            pedido = repo.buscar_por_id(idPedido)
            if not pedido:
                return None, "Pedido no encontrado", 404
            return pedido, "Detalle del pedido obtenido correctamente", 200
        finally:
            connection.close()

    def crear_pedido(self, data):
        idPuntosVenta = data.get("idPuntosVenta")
        productos = data.get("productos")

        if not idPuntosVenta:
            return None, "El campo 'idPuntosVenta' es obligatorio", 400

        if not productos or not isinstance(productos, list):
            return None, "Debe enviar una lista de 'productos' con sus cantidades", 400

        for item in productos:
            if "idProductos" not in item or "cantSolicitada" not in item:
                return None, "Cada producto debe tener 'idProductos' y 'cantSolicitada'", 400
            if int(item["cantSolicitada"]) <= 0:
                return None, "La cantidad solicitada debe ser mayor a 0", 400

        connection = get_connection()
        try:
            repo = PedidoRepository(connection)
            pedidos_ids = repo.crear_pedido_multiple(idPuntosVenta, productos)
            return {
                "idPuntosVenta": idPuntosVenta,
                "pedidos_creados": pedidos_ids,
                "total_items": len(pedidos_ids)
            }, "Pedido registrado exitosamente mediante transacción", 201
        except Exception as e:
            return None, f"Error al registrar pedido: {str(e)}", 500
        finally:
            connection.close()

    def actualizar_pedido(self, idPedido, data):
        cantSolicitada = data.get("cantSolicitada")
        if not cantSolicitada or int(cantSolicitada) <= 0:
            return None, "Debe enviar una cantidad solicitada válida", 400

        connection = get_connection()
        try:
            repo = PedidoRepository(connection)
            pedido = repo.buscar_por_id(idPedido)
            if not pedido:
                return None, "Pedido no encontrado", 404

            repo.actualizar(idPedido, int(cantSolicitada))
            actualizado = repo.buscar_por_id(idPedido)
            return actualizado, "Pedido actualizado correctamente", 200
        except Exception as e:
            return None, f"Error al actualizar pedido: {str(e)}", 500
        finally:
            connection.close()

    def cancelar_pedido(self, idPedido):
        connection = get_connection()
        try:
            repo = PedidoRepository(connection)
            pedido = repo.buscar_por_id(idPedido)
            if not pedido:
                return None, "Pedido no encontrado", 404

            repo.eliminar(idPedido)
            return {"idPedido": idPedido, "estado": "CANCELADO"}, "Pedido cancelado/eliminado correctamente", 200
        except Exception as e:
            return None, f"Error al cancelar pedido: {str(e)}", 500
        finally:
            connection.close()

    def completar_entrega(self, idPedido, data):
        cant_exhibida = int(data.get("cant_exhibida", 0))
        cant_almacen = int(data.get("cant_almacen", data.get("cant_entregada", 0)))
        observacion = data.get("observacion", "Entrega completada por el repartidor")

        connection = get_connection()
        try:
            repo = PedidoRepository(connection)
            pedido = repo.buscar_por_id(idPedido)
            if not pedido:
                return None, "Pedido no encontrado", 404

            repo.completar_entrega_transaccional(idPedido, cant_exhibida, cant_almacen, observacion)
            return {
                "idPedido": idPedido,
                "estado_despacho": "ENTREGADO",
                "observacion": observacion
            }, "Despacho entregado y stock actualizado correctamente", 200
        except Exception as e:
            return None, f"Error al completar entrega: {str(e)}", 500
        finally:
            connection.close()

    def listar_repartidores(self):
        connection = get_connection()
        try:
            repo = PedidoRepository(connection)
            repartidores = repo.listar_repartidores()
            return repartidores, "Repartidores obtenidos correctamente", 200
        finally:
            connection.close()
