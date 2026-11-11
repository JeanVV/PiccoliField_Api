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

            if rol not in ("ADMINISTRADOR", "PROMOTOR"):
                return None, f"Rol {rol} no autorizado para ver pedidos", 403

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
            print(f"Error en listar_pedidos: {e}")
            return None, "Error interno al obtener los pedidos", 500
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
            print(f"Error en obtener_pedido: {e}")
            return None, "Error interno al obtener el pedido", 500
        finally:
            connection.close()

    def crear_pedido(self, idUsuario, payload, operation_id=None):
        connection = get_connection()
        try:
            user_repo = UsuarioRepository(connection)
            usuario = user_repo.buscar_por_id(idUsuario)

            if not usuario:
                return None, "Usuario no autenticado", 401

            rol = str(usuario.get("rol", "")).upper()
            if rol == "IMPULSADOR":
                return None, "Los impulsadores no tienen permisos para registrar pedidos", 403

            if rol not in ("ADMINISTRADOR", "PROMOTOR"):
                return None, f"Rol {rol} no autorizado para registrar pedidos", 403

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

            # Validar campos de entrada
            idPuntosVenta = payload.get("idPuntosVenta")
            idProductos = payload.get("idProductos")
            cantSolicitada = payload.get("cantSolicitada")
            if cantSolicitada is None:
                cantSolicitada = payload.get("cantidad")

            if idPuntosVenta is None or idProductos is None or cantSolicitada is None:
                return None, "Los campos idPuntosVenta, idProductos y cantSolicitada son obligatorios", 400

            try:
                idPuntosVenta = int(idPuntosVenta)
                idProductos = int(idProductos)
                cantSolicitada = int(cantSolicitada)
            except (ValueError, TypeError):
                return None, "idPuntosVenta, idProductos y cantSolicitada deben ser números enteros", 400

            # Validar regla: cantidad > 0 (422)
            if cantSolicitada <= 0:
                return None, "La cantidad solicitada debe ser mayor a 0", 422

            # Validar PDV
            pdv = repo.validar_pdv(idPuntosVenta)
            if not pdv:
                return None, "Punto de venta no encontrado", 404

            if str(pdv.get("estado", "")).upper() != "ACTIVO":
                return None, f"El punto de venta no se encuentra ACTIVO (estado actual: {pdv.get('estado')})", 422

            tipo_pdv = str(pdv.get("tipo", "")).upper()
            if tipo_pdv not in ("DISTRIBUCION", "DISTRIBUCIÓN"):
                return None, f"El punto de venta debe ser de tipo DISTRIBUCIÓN (tipo actual: {tipo_pdv})", 422

            # Validar regla: si es Promotor, debe estar asignado a ese PDV (403)
            if rol == "PROMOTOR":
                pdv_responsable = pdv.get("idUsuario")
                if pdv_responsable is None or pdv_responsable != int(idUsuario):
                    return None, "No tiene permisos para registrar pedidos en este punto de venta (no asignado como responsable)", 403

            # Validar producto activo
            producto = repo.validar_producto(idProductos)
            if not producto:
                return None, "El producto especificado no existe", 422

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
            print(f"Error en crear_pedido: {e}")
            return None, "Error interno al registrar el pedido", 500
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
            # Regla de negocio: quién cambia el estado es el Administrador
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

            # Reglas de transición:
            # 1. Estados finales
            if estado_actual in ("ENTREGADO", "CANCELADO"):
                return None, f"No se puede modificar un pedido en estado final ({estado_actual})", 422

            # 2. Mismo estado
            if estado_actual == nuevo_estado:
                return None, f"El pedido ya se encuentra en estado {nuevo_estado}", 422

            # 3. Transiciones válidas:
            # REGISTRADO → EN_PREPARACION, CANCELADO
            # EN_PREPARACION → ENTREGADO, CANCELADO
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
            print(f"Error en actualizar_estado: {e}")
            return None, "Error interno al actualizar el estado del pedido", 500
        finally:
            connection.close()

