import traceback
from database import get_connection
from repositories.pedido_repository import PedidoRepository
from repositories.usuario_repository import UsuarioRepository


class PedidoService:

    def listar_pedidos(self, idUsuario, idPuntosVenta=None, estado=None, tipo_pdv=None):
        connection = get_connection()
        try:
            user_repo = UsuarioRepository(connection)
            usuario = user_repo.buscar_por_id(idUsuario)

            if not usuario:
                return None, "Usuario autenticado no encontrado", 401

            rol = str(usuario.get("rol", "")).upper()
            if rol == "IMPULSADOR":
                return None, "Los impulsadores no tienen acceso al módulo de pedidos", 403

            repo = PedidoRepository(connection)
            pedidos = repo.listar_pedidos(
                idUsuario=idUsuario,
                rol=rol,
                idPuntosVenta=idPuntosVenta,
                estado=estado,
                tipo_pdv=tipo_pdv
            )

            return pedidos, "Pedidos obtenidos correctamente", 200
        except Exception as e:
            traceback.print_exc()
            return None, f"Error interno al obtener los pedidos: {str(e)}", 500
        finally:
            connection.close()

    def obtener_pedido(self, idUsuario, idPedido):
        connection = get_connection()
        try:
            user_repo = UsuarioRepository(connection)
            usuario = user_repo.buscar_por_id(idUsuario)

            if not usuario:
                return None, "Usuario no autenticado", 401

            rol = str(usuario.get("rol", "")).upper()
            if rol == "IMPULSADOR":
                return None, "Los impulsadores no tienen acceso al módulo de pedidos", 403

            repo = PedidoRepository(connection)
            pedido = repo.obtener_por_id(idPedido)

            if not pedido:
                return None, "Pedido no encontrado", 404

            # Si es PROMOTOR, solo puede ver pedidos de sus PDV asignados
            if rol == "PROMOTOR" and pedido.get("idPromotorResponsable") != int(idUsuario):
                return None, "No tiene permisos para ver este pedido", 403

            return pedido, "Pedido obtenido correctamente", 200
        except Exception as e:
            traceback.print_exc()
            return None, f"Error interno al obtener el pedido: {str(e)}", 500
        finally:
            connection.close()

    def crear_pedido(self, idUsuario, payload, operation_id=None, idPuntosVenta_url=None):
        connection = get_connection()
        try:
            user_repo = UsuarioRepository(connection)
            usuario = user_repo.buscar_por_id(idUsuario)

            if not usuario:
                return None, "Usuario no autenticado", 401

            rol = str(usuario.get("rol", "")).upper()
            if rol == "IMPULSADOR":
                return None, "Los impulsadores no tienen permisos para registrar pedidos", 403

            repo = PedidoRepository(connection)

            # Idempotencia mediante X-Operation-Id u operation_id
            op_id = operation_id or payload.get("operation_id") or payload.get("idOperacion")
            if op_id:
                op_existente = repo.buscar_operacion_sync(op_id)
                if op_existente:
                    return (
                        op_existente.get("resultado_json"),
                        "Operación procesada previamente (idempotente)",
                        200
                    )

            # Extraer idPuntosVenta (de URL o del body)
            idPuntosVenta = (
                idPuntosVenta_url
                or payload.get("idPuntosVenta")
                or payload.get("idPuntoVenta")
                or payload.get("id_puntos_venta")
                or payload.get("id_punto_venta")
                or payload.get("punto_venta_id")
            )

            if idPuntosVenta is None:
                return None, "El campo 'idPuntosVenta' es obligatorio", 400

            try:
                idPuntosVenta = int(idPuntosVenta)
            except (ValueError, TypeError):
                return None, "idPuntosVenta debe ser un número entero válido", 400

            # Validar PDV
            pdv = repo.validar_pdv(idPuntosVenta)
            if not pdv:
                return None, f"Punto de venta con ID {idPuntosVenta} no encontrado", 404

            if str(pdv.get("estado", "")).upper() != "ACTIVO":
                return None, f"El punto de venta no se encuentra ACTIVO (estado actual: {pdv.get('estado')})", 422

            tipo_pdv = str(pdv.get("tipo", "")).upper()
            if tipo_pdv not in ("DISTRIBUCION", "DISTRIBUCIÓN"):
                return None, f"El punto de venta debe ser de tipo DISTRIBUCIÓN (tipo actual: {tipo_pdv})", 422

            # Validar si es Promotor asignado
            if rol == "PROMOTOR":
                pdv_responsable = pdv.get("idUsuario")
                if pdv_responsable is None:
                    return None, "El punto de venta no tiene un promotor asignado", 403
                if int(pdv_responsable) != int(idUsuario):
                    return None, "No está asignado como responsable de este punto de distribución", 403

            # Soporte para lista de productos: payload["productos"] = [...]
            lista_productos = payload.get("productos")
            if lista_productos and isinstance(lista_productos, list):
                pedidos_creados = []
                for item in lista_productos:
                    id_prod = item.get("idProductos") or item.get("idProducto")
                    cant = item.get("cantSolicitada") or item.get("cantidad")

                    if not id_prod or not cant:
                        return None, "Cada producto de la lista debe tener 'idProductos' y 'cantSolicitada'", 400

                    cant = int(cant)
                    if cant <= 0:
                        return None, "La cantidad solicitada debe ser mayor a 0", 422

                    prod = repo.validar_producto(int(id_prod))
                    if not prod or str(prod.get("estado", "")).upper() != "ACTIVO":
                        return None, f"El producto {id_prod} no existe o está inactivo", 422

                    creado = repo.crear_pedido(
                        cantSolicitada=cant,
                        idPuntosVenta=idPuntosVenta,
                        idProductos=int(id_prod),
                        idOperacion=None,
                        idUsuario=idUsuario
                    )
                    pedidos_creados.append(creado)

                if op_id:
                    repo.registrar_operacion_sync(op_id, "CREAR_PEDIDO_MULTIPLE", pedidos_creados, idUsuario)

                return pedidos_creados, "Pedidos registrados exitosamente", 201

            # Caso producto individual
            idProductos = (
                payload.get("idProductos")
                or payload.get("idProducto")
                or payload.get("id_productos")
                or payload.get("id_producto")
                or payload.get("producto_id")
            )

            # Si viene código en lugar de idProductos (ej. código EAN o SKU)
            if idProductos is None:
                codigo = (
                    payload.get("codigo_ean")
                    or payload.get("codigo")
                    or payload.get("sku")
                    or payload.get("codigo_barras")
                )
                if codigo:
                    prod_buscado = repo.buscar_producto_por_codigo(codigo)
                    if prod_buscado:
                        idProductos = prod_buscado["idProductos"]

            cantSolicitada = (
                payload.get("cantSolicitada")
                or payload.get("cantidad")
                or payload.get("cant_solicitada")
                or payload.get("cantidad_solicitada")
            )

            if idProductos is None or cantSolicitada is None:
                return None, "Los campos 'idProductos' y 'cantSolicitada' son obligatorios", 400

            try:
                idProductos = int(idProductos)
                cantSolicitada = int(cantSolicitada)
            except (ValueError, TypeError):
                return None, "idProductos y cantSolicitada deben ser números enteros", 400

            if cantSolicitada <= 0:
                return None, "La cantidad solicitada debe ser mayor a 0", 422

            # Validar producto activo
            producto = repo.validar_producto(idProductos)
            if not producto:
                return None, f"El producto con ID {idProductos} no existe", 422

            if str(producto.get("estado", "")).upper() != "ACTIVO":
                return None, "El producto se encuentra inactivo", 422

            # Registrar pedido
            pedido_creado = repo.crear_pedido(
                cantSolicitada=cantSolicitada,
                idPuntosVenta=idPuntosVenta,
                idProductos=idProductos,
                idOperacion=op_id,
                idUsuario=idUsuario
            )

            return pedido_creado, "Pedido registrado exitosamente", 201

        except Exception as e:
            traceback.print_exc()
            return None, f"Error al registrar pedido: {str(e)}", 500
        finally:
            connection.close()

    def actualizar_estado(self, idUsuario, idPedido, nuevo_estado):
        connection = get_connection()
        try:
            user_repo = UsuarioRepository(connection)
            usuario = user_repo.buscar_por_id(idUsuario)

            if not usuario:
                return None, "Usuario no autenticado", 401

            rol = str(usuario.get("rol", "")).upper()
            if rol != "ADMINISTRADOR":
                return None, "Solo los administradores pueden cambiar el estado del pedido", 403

            if not nuevo_estado:
                return None, "El campo 'estado' es obligatorio", 400

            nuevo_estado = str(nuevo_estado).strip().upper().replace(" ", "_")
            estados_validos = ("REGISTRADO", "EN_PREPARACION", "ENTREGADO", "CANCELADO")
            if nuevo_estado not in estados_validos:
                return None, f"Estado inválido. Valores permitidos: {', '.join(estados_validos)}", 400

            repo = PedidoRepository(connection)
            pedido = repo.obtener_por_id(idPedido)
            if not pedido:
                return None, "Pedido no encontrado", 404

            estado_actual = str(pedido.get("estado", "")).upper().replace(" ", "_")

            if estado_actual in ("ENTREGADO", "CANCELADO"):
                return None, f"No se puede modificar un pedido en estado final ({estado_actual})", 422

            if estado_actual == nuevo_estado:
                return None, f"El pedido ya se encuentra en estado {nuevo_estado}", 422

            transiciones_permitidas = {
                "REGISTRADO": ("EN_PREPARACION", "CANCELADO"),
                "EN_PREPARACION": ("ENTREGADO", "CANCELADO")
            }

            permitidos = transiciones_permitidas.get(estado_actual, ())
            if nuevo_estado not in permitidos:
                return None, f"Transición no permitida de {estado_actual} a {nuevo_estado}", 422

            pedido_actualizado = repo.actualizar_estado(idPedido, nuevo_estado)
            return pedido_actualizado, f"Estado del pedido actualizado a {nuevo_estado} exitosamente", 200

        except Exception as e:
            traceback.print_exc()
            return None, f"Error interno al actualizar el estado del pedido: {str(e)}", 500
        finally:
            connection.close()
