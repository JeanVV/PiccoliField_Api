from database import get_connection
from repositories.punto_venta_repository import PuntoVentaRepository
from repositories.usuario_repository import UsuarioRepository


class PuntoVentaService:

    def listar_puntos(self, search=None, distrito=None, estado="ACTIVO", tipo=None, idUsuario=None):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            puntos = repo.listar_todos(
                search=search,
                distrito=distrito,
                estado=estado,
                tipo=tipo,
                idUsuario=idUsuario
            )
            return puntos, "Puntos de venta obtenidos correctamente", 200
        finally:
            connection.close()

    def obtener_punto(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            punto = repo.buscar_por_id(idPuntosVenta)
            if not punto:
                return None, "Punto de venta no encontrado", 404
            return punto, "Punto de venta obtenido correctamente", 200
        finally:
            connection.close()

    def asignar_responsable(self, idPuntosVenta, idUsuarioNuevo, idUsuarioRegistra, motivo=None):
        connection = get_connection()
        try:
            # Validar que quien registra sea Administrador
            user_repo = UsuarioRepository(connection)
            admin = user_repo.buscar_por_id(idUsuarioRegistra)
            if not admin or admin.get("rol") != "ADMINISTRADOR":
                return None, "Solo los administradores pueden asignar responsables a puntos de venta", 403

            repo = PuntoVentaRepository(connection)
            pdv_actualizado, message, code = repo.asignar_responsable(
                idPuntosVenta=idPuntosVenta,
                idUsuarioNuevo=idUsuarioNuevo,
                idUsuarioRegistra=idUsuarioRegistra,
                motivo=motivo
            )
            return pdv_actualizado, message, code
        except Exception as e:
            print(f"Error en asignar_responsable: {e}")
            return None, "Error interno al asignar responsable", 500
        finally:
            connection.close()

    def obtener_historial_asignaciones(self, idPuntosVenta):
        connection = get_connection()
        try:
            repo = PuntoVentaRepository(connection)
            # Verificar si PDV existe
            pdv = repo.buscar_por_id(idPuntosVenta)
            if not pdv:
                return None, "Punto de venta no encontrado", 404

            historial = repo.obtener_historial_asignaciones(idPuntosVenta)
            return historial, "Historial de asignaciones obtenido correctamente", 200
        finally:
            connection.close()
