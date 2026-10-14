class ControlRepository:
    def __init__(self, connection):
        self.connection = connection

    def listar_promotores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.correo,
                    u.rol,
                    u.estado,
                    COUNT(pv.idPuntosVenta) AS total_puntos_asignados
                FROM USUARIOS u
                LEFT JOIN PUNTOS_VENTA pv ON u.idUsuario = pv.idUsuario
                WHERE u.estado = 'ACTIVO'
                GROUP BY u.idUsuario, u.nombres, u.apePaterno, u.apeMaterno, u.correo, u.rol, u.estado
                ORDER BY u.nombres ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def asignar_punto(self, idUsuario, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE PUNTOS_VENTA SET idUsuario = %s WHERE idPuntosVenta = %s"
            cursor.execute(sql, (idUsuario, idPuntosVenta))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def desasignar_punto(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE PUNTOS_VENTA SET idUsuario = 1 WHERE idPuntosVenta = %s"
            cursor.execute(sql, (idPuntosVenta,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def puntos_por_promotor(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.codigo,
                    pv.puntosVenta,
                    pv.direccion,
                    pv.estado,
                    d.distrito
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                WHERE pv.idUsuario = %s
                ORDER BY pv.puntosVenta ASC
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def asistencias_supervision(self, fecha=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    a.idAsistencias,
                    a.tipo,
                    a.fecha_hora_servidor,
                    a.estado,
                    a.minutos_tardanza,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor,
                    u.rol,
                    s.sede
                FROM ASISTENCIAS a
                INNER JOIN USUARIOS u ON a.idUsuario = u.idUsuario
                LEFT JOIN SEDES s ON u.idSede = s.idSede
                WHERE 1=1
            """
            params = []
            if fecha:
                sql += " AND DATE(a.fecha_hora_servidor) = %s"
                params.append(fecha)

            sql += " ORDER BY a.fecha_hora_servidor DESC LIMIT 50"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def alertas_stock(self, estado="PENDIENTE"):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    a.idAlertas,
                    a.tipo,
                    a.estado,
                    a.comentario,
                    a.fecha_atencion,
                    pr.producto,
                    pr.presentacion,
                    pv.puntosVenta,
                    pv.direccion
                FROM ALERTAS_STOCK a
                INNER JOIN PRODUCTOS pr ON a.idProductos = pr.idProductos
                INNER JOIN PUNTOS_VENTA pv ON a.idPuntosVenta = pv.idPuntosVenta
                WHERE 1=1
            """
            params = []
            if estado:
                sql += " AND a.estado = %s"
                params.append(estado)

            sql += " ORDER BY a.idAlertas DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def atender_alerta(self, idAlertas, comentario=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE ALERTAS_STOCK 
                SET estado = 'ATENDIDA', fecha_atencion = NOW(), comentario = COALESCE(%s, comentario)
                WHERE idAlertas = %s
            """
            cursor.execute(sql, (comentario, idAlertas))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def dashboard_kpis(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    (SELECT COUNT(*) FROM PUNTOS_VENTA WHERE estado = 'ACTIVO') AS total_puntos_activos,
                    (SELECT COUNT(*) FROM USUARIOS WHERE estado = 'ACTIVO') AS total_personal_activo,
                    (SELECT COUNT(*) FROM Pedido) AS total_pedidos_historicos,
                    (SELECT COUNT(*) FROM ALERTAS_STOCK WHERE estado = 'PENDIENTE') AS alertas_stock_pendientes
            """
            cursor.execute(sql)
            return cursor.fetchone()
        finally:
            cursor.close()

    def productos_destacados(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idProductos,
                    sku,
                    codigo_ean,
                    producto,
                    categoria,
                    presentacion
                FROM PRODUCTOS
                WHERE estado = 'ACTIVO'
                ORDER BY idProductos ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def distritos_activos(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT DISTINCT 
                    d.idDistrito,
                    d.distrito,
                    p.provincia,
                    COUNT(pv.idPuntosVenta) AS total_puntos
                FROM DISTRITO d
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN PUNTOS_VENTA pv ON d.idDistrito = pv.idDistrito
                WHERE pv.estado = 'ACTIVO'
                GROUP BY d.idDistrito, d.distrito, p.provincia
                ORDER BY d.distrito ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
