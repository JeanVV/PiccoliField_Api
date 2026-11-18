import traceback
from database import get_connection
from repositories.prospecto_repository import ProspectoRepository
from repositories.usuario_repository import UsuarioRepository


class ProspectoService:

    def listar_prospectos(self, estado=None, potencial=None, idDistrito=None, idUsuario=None, search=None):
        connection = get_connection()
        try:
            repo = ProspectoRepository(connection)
            prospectos = repo.listar(
                estado=estado,
                potencial=potencial,
                idDistrito=idDistrito,
                idUsuario=idUsuario,
                search=search
            )
            return prospectos, "Prospectos obtenidos correctamente", 200
        except Exception as e:
            traceback.print_exc()
            return None, f"Error al listar prospectos: {str(e)}", 500
        finally:
            connection.close()

    def obtener_prospecto(self, idProspectos):
        connection = get_connection()
        try:
            repo = ProspectoRepository(connection)
            prospecto = repo.buscar_por_id(idProspectos)
            if not prospecto:
                return None, "Prospecto no encontrado", 404

            # Adjuntar seguimientos
            seguimientos = repo.listar_seguimientos(idProspectos)
            prospecto["seguimientos"] = seguimientos

            return prospecto, "Prospecto obtenido correctamente", 200
        except Exception as e:
            traceback.print_exc()
            return None, f"Error al obtener prospecto: {str(e)}", 500
        finally:
            connection.close()

    def crear_prospecto(self, idUsuarioAutenticado, payload):
        connection = get_connection()
        try:
            nombre_comercial = payload.get("nombre_comercial")
            direccion = payload.get("direccion")
            latitud = payload.get("latitud")
            longitud = payload.get("longitud")
            idDistrito = payload.get("idDistrito")

            if not nombre_comercial or not direccion:
                return None, "Los campos 'nombre_comercial' y 'direccion' son obligatorios", 400

            if latitud is None or longitud is None:
                return None, "Las coordenadas 'latitud' y 'longitud' son obligatorias", 400

            if idDistrito is None:
                return None, "El campo 'idDistrito' es obligatorio", 400

            try:
                latitud = float(latitud)
                longitud = float(longitud)
                idDistrito = int(idDistrito)
            except (ValueError, TypeError):
                return None, "Latitud, longitud o idDistrito tienen formatos numéricos inválidos", 400

            idUsuarioAsignado = payload.get("idUsuario") or idUsuarioAutenticado

            potencial = str(payload.get("potencial", "MEDIO")).strip().upper()
            if potencial not in ("ALTO", "MEDIO", "BAJO"):
                potencial = "MEDIO"

            estado_inicial = str(payload.get("estado", "NUEVO")).strip().upper()
            if estado_inicial not in ("NUEVO", "EN_NEGOCIACION", "CONVERTIDO", "DESCARTADO"):
                estado_inicial = "NUEVO"

            data_insert = {
                "nombre_comercial": nombre_comercial.strip(),
                "tipo_local": payload.get("tipo_local"),
                "direccion": direccion.strip(),
                "contacto": payload.get("contacto"),
                "telefono": payload.get("telefono"),
                "potencial": potencial,
                "estado": estado_inicial,
                "notas": payload.get("notas"),
                "motivo_descarte": payload.get("motivo_descarte"),
                "url_foto": payload.get("url_foto"),
                "latitud": latitud,
                "longitud": longitud,
                "idDistrito": idDistrito,
                "idUsuario": int(idUsuarioAsignado)
            }

            repo = ProspectoRepository(connection)
            prospecto_creado = repo.crear(data_insert)

            # Si se creó directamente como CONVERTIDO
            punto_venta = None
            if estado_inicial == "CONVERTIDO":
                _, punto_venta = repo.actualizar_estado(
                    idProspectos=prospecto_creado["idProspectos"],
                    nuevo_estado="CONVERTIDO",
                    idUsuarioRevisor=idUsuarioAutenticado
                )
                prospecto_creado["punto_venta"] = punto_venta

            return {
                "prospecto": prospecto_creado,
                "punto_venta": punto_venta
            }, "Prospecto registrado exitosamente", 201

        except Exception as e:
            traceback.print_exc()
            return None, f"Error al registrar prospecto: {str(e)}", 500
        finally:
            connection.close()

    def actualizar_prospecto(self, idProspectos, payload):
        connection = get_connection()
        try:
            repo = ProspectoRepository(connection)
            prospecto = repo.buscar_por_id(idProspectos)
            if not prospecto:
                return None, "Prospecto no encontrado", 404

            actualizado = repo.actualizar(idProspectos, payload)
            return actualizado, "Prospecto actualizado correctamente", 200
        except Exception as e:
            traceback.print_exc()
            return None, f"Error al actualizar prospecto: {str(e)}", 500
        finally:
            connection.close()

    def cambiar_estado(self, idProspectos, nuevo_estado, motivo_descarte=None, idUsuarioRevisor=None):
        connection = get_connection()
        try:
            if not nuevo_estado:
                return None, "El campo 'estado' es obligatorio", 400

            nuevo_estado = str(nuevo_estado).strip().upper()
            estados_validos = ("NUEVO", "EN_NEGOCIACION", "CONVERTIDO", "DESCARTADO")
            if nuevo_estado not in estados_validos:
                return None, f"Estado inválido. Valores permitidos: {', '.join(estados_validos)}", 400

            repo = ProspectoRepository(connection)
            prospecto = repo.buscar_por_id(idProspectos)
            if not prospecto:
                return None, "Prospecto no encontrado", 404

            prospecto_act, punto_venta = repo.actualizar_estado(
                idProspectos=idProspectos,
                nuevo_estado=nuevo_estado,
                motivo_descarte=motivo_descarte,
                idUsuarioRevisor=idUsuarioRevisor
            )

            mensaje = f"Estado del prospecto actualizado a {nuevo_estado}"
            if nuevo_estado == "CONVERTIDO" and punto_venta:
                mensaje = "Prospecto convertido exitosamente a Punto de Venta (Distribución)"

            return {
                "prospecto": prospecto_act,
                "punto_venta": punto_venta
            }, mensaje, 200

        except Exception as e:
            traceback.print_exc()
            return None, f"Error al cambiar estado del prospecto: {str(e)}", 500
        finally:
            connection.close()

    def asignar_promotor(self, idProspectos, idUsuario):
        connection = get_connection()
        try:
            if not idUsuario:
                return None, "El campo 'idUsuario' es obligatorio", 400

            user_repo = UsuarioRepository(connection)
            usuario = user_repo.buscar_por_id(idUsuario)
            if not usuario:
                return None, "Usuario promotor no encontrado", 404

            repo = ProspectoRepository(connection)
            prospecto = repo.buscar_por_id(idProspectos)
            if not prospecto:
                return None, "Prospecto no encontrado", 404

            actualizado = repo.asignar_promotor(idProspectos, int(idUsuario))
            return actualizado, f"Prospecto asignado a {usuario['nombres']} {usuario['apePaterno']} exitosamente", 200
        except Exception as e:
            traceback.print_exc()
            return None, f"Error al asignar promotor: {str(e)}", 500
        finally:
            connection.close()

    # ── SEGUIMIENTOS ─────────────────────────────────────────────────────────
    def crear_seguimiento(self, idProspectos, idUsuario, payload):
        connection = get_connection()
        try:
            tipo = str(payload.get("tipo", "VISITA")).strip().upper()
            tipos_validos = ("LLAMADA", "VISITA", "MENSAJE", "PROPUESTA")
            if tipo not in tipos_validos:
                return None, f"Tipo de seguimiento inválido. Permitidos: {', '.join(tipos_validos)}", 400

            comentario = payload.get("comentario")
            if not comentario or not str(comentario).strip():
                return None, "El campo 'comentario' es obligatorio", 400

            repo = ProspectoRepository(connection)
            prospecto = repo.buscar_por_id(idProspectos)
            if not prospecto:
                return None, "Prospecto no encontrado", 404

            seguimiento = repo.crear_seguimiento(
                idProspectos=idProspectos,
                idUsuario=idUsuario,
                tipo=tipo,
                comentario=comentario.strip(),
                proxima_accion=payload.get("proxima_accion"),
                fecha_proxima_accion=payload.get("fecha_proxima_accion")
            )

            return seguimiento, "Seguimiento registrado exitosamente", 201
        except Exception as e:
            traceback.print_exc()
            return None, f"Error al registrar seguimiento: {str(e)}", 500
        finally:
            connection.close()

    def listar_seguimientos(self, idProspectos):
        connection = get_connection()
        try:
            repo = ProspectoRepository(connection)
            prospecto = repo.buscar_por_id(idProspectos)
            if not prospecto:
                return None, "Prospecto no encontrado", 404

            seguimientos = repo.listar_seguimientos(idProspectos)
            return seguimientos, "Seguimientos obtenidos correctamente", 200
        finally:
            connection.close()
