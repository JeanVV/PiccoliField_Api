class SupervisionRepository:
    def __init__(self, connection):
        self.connection = connection

    def obtener_mejores_vendedores(self):
        cursor = self.connection.cursor()
        try:
            # Tu consulta SQL
            sql = """
                SELECT 
                    u.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS nombre,
                    pdv.puntosVenta AS local, 
                    SUM(dv.cantidad) AS cantidadVendida
                    u.meta_mensual AS meta_asignada
                FROM USUARIOS u
                INNER JOIN VENTAS v ON u.idUsuario = v.idUsuario
                INNER JOIN DETALLE_VENTA dv ON v.idVenta = dv.idVenta
                LEFT JOIN PUNTOS_VENTA pdv ON u.idUsuario = pdv.idUsuario
                WHERE u.rol IN ('PROMOTOR', 'IMPULSADOR', 'VENDEDOR')
                GROUP BY u.idUsuario, u.nombres, u.apePaterno, pdv.puntosVenta -- ¡Aquí se agregó la columna!
                ORDER BY cantidadVendida DESC;
            """
            cursor.execute(sql)
            vendedores = cursor.fetchall()
            
            # Agregamos la posición para el diseño de Android
            for index, vendedor in enumerate(vendedores):
                vendedor['posicion'] = index + 1
                
            return vendedores
        except Exception as e:
            print(f"Error en obtener_mejores_vendedores: {e}")
            return None
        finally:
            cursor.close()

    def obtener_resumen(self):
        cursor = self.connection.cursor()
        try:
            # Ventas Totales
            cursor.execute("SELECT COALESCE(SUM(total), 0) AS monto_total FROM VENTAS")
            monto = cursor.fetchone()['monto_total']
            
            # Puntos de Venta Activos
            cursor.execute("SELECT COUNT(*) AS pdv_activos FROM PUNTOS_VENTA WHERE estado = 'ACTIVO'")
            pdv = cursor.fetchone()['pdv_activos']
            
            # Alertas Pendientes
            cursor.execute("SELECT COUNT(*) AS alertas_pendientes FROM ALERTAS_STOCK WHERE estado = 'PENDIENTE'")
            alertas = cursor.fetchone()['alertas_pendientes']
            
            return {
                "monto_total_ventas": float(monto),
                "cantidad_pdv_activos": pdv,
                "cantidad_alertas": alertas
            }
        finally:
            cursor.close()

    def obtener_detalle_vendedor(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            # Consulta 1: Datos generales y ventas totales
            sql_info = """
                SELECT 
                    CONCAT(u.nombres, ' ', u.apePaterno) AS nombre,
                    pdv.puntosVenta AS local_pertenece,
                    u.meta_mensual AS meta_asignada,
                    COALESCE(SUM(v.total), 0) AS monto_vendido
                FROM USUARIOS u
                LEFT JOIN PUNTOS_VENTA pdv ON u.idUsuario = pdv.idUsuario
                LEFT JOIN VENTAS v ON u.idUsuario = v.idUsuario
                WHERE u.idUsuario = %s AND u.rol IN ('PROMOTOR', 'IMPULSADOR', 'VENDEDOR')
                GROUP BY u.idUsuario, pdv.puntosVenta, u.meta_mensual
            """
            cursor.execute(sql_info, (idUsuario,))
            vendedor = cursor.fetchone()
            
            if not vendedor:
                return None
                
            # Consulta 2: Lista de productos que vendió este trabajador
            sql_productos = """
                SELECT 
                    p.producto AS nombre_producto, 
                    SUM(dv.cantidad) AS cantidad_vendida
                FROM VENTAS v
                INNER JOIN DETALLE_VENTA dv ON v.idVenta = dv.idVenta
                INNER JOIN PRODUCTOS p ON dv.idProductos = p.idProductos
                WHERE v.idUsuario = %s
                GROUP BY p.idProductos, p.producto
                ORDER BY cantidad_vendida DESC
            """
            cursor.execute(sql_productos, (idUsuario,))
            productos = cursor.fetchall()
            
            # Lógica para calcular el Porcentaje automáticamente
            meta = float(vendedor['meta_asignada'])
            vendido = float(vendedor['monto_vendido'])
            porcentaje = round((vendido / meta) * 100, 2) if meta > 0 else 0
            
            # Armamos el JSON final para Android
            return {
                "nombre": vendedor['nombre'],
                "local_pertenece": vendedor['local_pertenece'] or "Sin local asignado",
                "monto_vendido": vendido,
                "meta_asignada": meta,
                "porcentaje_logro": porcentaje,
                "productos_vendidos": productos
            }
        finally:
            cursor.close()

    def obtener_detalle_alerta(self, idAlerta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    p.producto AS nombre_producto,
                    COALESCE(sr.cant_almacen, 0) AS stock_actual,
                    COALESCE(sr.stock_minimo, 0) AS stock_minimo,
                    pdv.puntosVenta AS local_nombre,
                    pdv.direccion AS local_direccion,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS responsable_nombre,
                    u.rol AS responsable_rol,
                    a.estado AS estado_resolucion,
                    a.severidad AS nivel_alerta
                FROM ALERTAS_STOCK a
                INNER JOIN PRODUCTOS p ON a.idProductos = p.idProductos
                INNER JOIN PUNTOS_VENTA pdv ON a.idPuntosVenta = pdv.idPuntosVenta
                INNER JOIN USUARIOS u ON pdv.idUsuario = u.idUsuario
                LEFT JOIN STOCK_REGISTROS sr ON sr.idProductos = p.idProductos AND sr.idPuntosVenta = pdv.idPuntosVenta
                WHERE a.idAlertas = %s
                ORDER BY sr.fecha DESC
                LIMIT 1
            """
            cursor.execute(sql, (idAlerta,))
            return cursor.fetchone()
        finally:
            cursor.close()