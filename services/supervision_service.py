from database import get_connection
from repositories.supervision_repository import SupervisionRepository

class SupervisionService:
    def listar_mejores_vendedores(self):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_mejores_vendedores()
            
            if data is None:
                return None, "Error interno al obtener los vendedores", 500
                
            if len(data) == 0:
                return [], "No se encontraron ventas registradas", 200
                
            return data, "Mejores vendedores listados exitosamente", 200
            
        except Exception as e:
            print(f"Error en el servicio de supervisión: {e}")
            return None, "Ocurrió un error inesperado", 500
        finally:
            connection.close()

    def obtener_resumen_dashboard(self):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_resumen()
            return data, "Resumen obtenido exitosamente", 200
        except Exception as e:
            print(f"Error resumen dashboard: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def obtener_detalle_vendedor(self, idUsuario):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_detalle_vendedor(idUsuario)
            if not data:
                return None, "Vendedor no encontrado o no tiene ventas", 404
            return data, "Detalle obtenido exitosamente", 200
        except Exception as e:
            print(f"Error detalle vendedor: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()
            
    def obtener_detalle_alerta(self, idAlerta):
        connection = get_connection()
        try:
            repo = SupervisionRepository(connection)
            data = repo.obtener_detalle_alerta(idAlerta)
            if not data:
                return None, "Alerta no encontrada", 404
            return data, "Detalle obtenido exitosamente", 200
        except Exception as e:
            print(f"Error detalle alerta: {e}")
            return None, "Error interno", 500
        finally:
            connection.close()

    def listar_puntos_venta(self):
        try:
            query = """
                SELECT 
                    idPuntosVenta AS id, 
                    puntosVenta AS nombre, 
                    direccion, 
                    estado 
                FROM PUNTOS_VENTA
                ORDER BY puntosVenta ASC
            """

            data = []
            for row in resultados:
                data.append({
                    "id": row['id'],
                    "nombre": row['nombre'],
                    "direccion": row['direccion'],
                    "estado": row['estado']
                })
                
            return data, "Puntos de venta obtenidos exitosamente", 200
        except Exception as e:
            return None, str(e), 500

    def listar_alertas(self):
        try:
            query = """
                SELECT 
                    a.idAlertas AS idAlerta,
                    a.estado AS estado_resolucion,
                    a.tipo AS nivel_alerta,
                    pv.puntosVenta AS local_nombre,
                    p.producto AS nombre_producto
                FROM ALERTAS_STOCK a
                INNER JOIN PUNTOS_VENTA pv ON a.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN PRODUCTOS p ON a.idProductos = p.idProductos
                ORDER BY a.idAlertas DESC
            """
            
            data = []
            for row in resultados:
                data.append({
                    "idAlerta": row['idAlerta'],
                    "estado_resolucion": row['estado_resolucion'],
                    "nivel_alerta": row['nivel_alerta'],
                    "local_nombre": row['local_nombre'],
                    "nombre_producto": row['nombre_producto']
                })
                
            return data, "Alertas obtenidas exitosamente", 200
        except Exception as e:
            return None, str(e), 500