import os
import traceback
from config import BASE_DIR
from database import get_connection
from repositories.prospecto_repository import ProspectoRepository
from repositories.usuario_repository import UsuarioRepository


def normalizar_estado_prospecto(estado_str):
    if not estado_str:
        return None
    s = str(estado_str).strip().upper().replace(" ", "_").replace("-", "_")
    # Remover acentos
    s = s.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")

    # Mapeos al ENUM('NUEVO', 'EN_NEGOCIACION', 'CONVERTIDO', 'DESCARTADO')
    if s in ("EN_NEGOCIACION", "NEGOCIACION", "NEGOCIAR", "CONTACTADO", "CONTACTO", "EN_PROCESO"):
        return "EN_NEGOCIACION"

    if s in ("CONVERTIDO", "CONVERTIR", "CONVERSION", "GANADO", "CLIENTE", "PDV"):
        return "CONVERTIDO"

    if s in ("DESCARTADO", "DESCARTAR", "RECHAZADO", "RECHAZAR", "PERDIDO", "CANCELADO"):
        return "DESCARTADO"

    if s in ("NUEVO", "INICIAL", "REGISTRADO"):
        return "NUEVO"

    if s in ("NUEVO", "EN_NEGOCIACION", "CONVERTIDO", "DESCARTADO"):
        return s

    return None


class ProspectoService:

    def listar_prospectos(self, estado=None, potencial=None, idDistrito=None, idUsuario=None, search=None):
        connection = get_connection()
        try:
            # Normalizar estado de búsqueda si viene como NEGOCIACION, RECHAZADO, etc.
            estado_norm = normalizar_estado_prospecto(estado) if estado else None

            repo = ProspectoRepository(connection)
            prospectos = repo.listar(
                estado=estado_norm,
                potencial=potencial,
                idDistrito=idDistrito,
                idUsuario=idUsuario,
                search=search
            )

            # Enriquecer cada prospecto con alias útiles (id, nombre, estado_label, url_foto)
            for p in (prospectos or []):
                p["id"] = p.get("idProspectos")
                p["nombre"] = p.get("nombre_comercial")
                if not p.get("url_foto"):
                    disk_rel = f"uploads/prospectos/prospecto_{p.get('idProspectos')}.jpg"
                    if os.path.isfile(os.path.join(BASE_DIR, disk_rel)):
                        p["url_foto"] = disk_rel
                est = str(p.get("estado", "")).upper()
                if est == "EN_NEGOCIACION":
                    p["estado_label"] = "En Negociación"
                elif est == "CONVERTIDO":
                    p["estado_label"] = "Convertido"
                elif est == "DESCARTADO":
                    p["estado_label"] = "Descartado"
                else:
                    p["estado_label"] = "Nuevo"

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
            prospecto["id"] = prospecto.get("idProspectos")
            prospecto["nombre"] = prospecto.get("nombre_comercial")
            if not prospecto.get("url_foto"):
                disk_rel = f"uploads/prospectos/prospecto_{prospecto.get('idProspectos')}.jpg"
                if os.path.isfile(os.path.join(BASE_DIR, disk_rel)):
                    prospecto["url_foto"] = disk_rel

            est = str(prospecto.get("estado", "")).upper()
            if est == "EN_NEGOCIACION":
                prospecto["estado_label"] = "En Negociación"
            elif est == "CONVERTIDO":
                prospecto["estado_label"] = "Convertido"
            elif est == "DESCARTADO":
                prospecto["estado_label"] = "Descartado"
            else:
                prospecto["estado_label"] = "Nuevo"

            return prospecto, "Prospecto obtenido correctamente", 200
        except Exception as e:
            traceback.print_exc()
            return None, f"Error al obtener prospecto: {str(e)}", 500
        finally:
            connection.close()

    def crear_prospecto(self, idUsuarioAutenticado, payload):
        connection = get_connection()
        try:
            nombre_comercial = payload.get("nombre_comercial") or payload.get("nombre")
            direccion = payload.get("direccion")
            latitud = payload.get("latitud") or payload.get("lat")
            longitud = payload.get("longitud") or payload.get("lng")
            idDistrito = payload.get("idDistrito") or payload.get("distrito_id")

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

            idUsuarioAsignado = payload.get("idUsuario") or payload.get("idPromotor") or idUsuarioAutenticado

            potencial = str(payload.get("potencial", "MEDIO")).strip().upper()
            if potencial not in ("ALTO", "MEDIO", "BAJO"):
                potencial = "MEDIO"

            # Normalizar estado inicial (si envían NEGOCIACION -> EN_NEGOCIACION)
            estado_raw = payload.get("estado", "NUEVO")
            estado_inicial = normalizar_estado_prospecto(estado_raw) or "NUEVO"

            data_insert = {
                "nombre_comercial": str(nombre_comercial).strip(),
                "tipo_local": payload.get("tipo_local") or payload.get("tipo"),
                "direccion": str(direccion).strip(),
                "contacto": payload.get("contacto"),
                "telefono": payload.get("telefono"),
                "potencial": potencial,
                "estado": estado_inicial,
                "notas": payload.get("notas"),
                "motivo_descarte": payload.get("motivo_descarte"),
                "url_foto": payload.get("url_foto") or payload.get("foto"),
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

            # Si viene cambio de estado dentro del payload general, normalizarlo
            if "estado" in payload and payload["estado"]:
                nuevo_est = normalizar_estado_prospecto(payload["estado"])
                if nuevo_est:
                    payload["estado"] = nuevo_est

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

            # Normalizar estado: NEGOCIACION -> EN_NEGOCIACION, RECHAZAR/RECHAZADO -> DESCARTADO
            estado_normalizado = normalizar_estado_prospecto(nuevo_estado)

            if not estado_normalizado:
                return None, (
                    f"Estado inválido '{nuevo_estado}'. "
                    "Valores permitidos en base de datos: NUEVO, EN_NEGOCIACION, CONVERTIDO, DESCARTADO"
                ), 400

            repo = ProspectoRepository(connection)
            prospecto = repo.buscar_por_id(idProspectos)
            if not prospecto:
                return None, f"Prospecto con ID {idProspectos} no encontrado", 404

            prospecto_act, punto_venta = repo.actualizar_estado(
                idProspectos=idProspectos,
                nuevo_estado=estado_normalizado,
                motivo_descarte=motivo_descarte,
                idUsuarioRevisor=idUsuarioRevisor
            )

            mensaje = f"Estado del prospecto actualizado a {estado_normalizado}"
            if estado_normalizado == "CONVERTIDO" and punto_venta:
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
