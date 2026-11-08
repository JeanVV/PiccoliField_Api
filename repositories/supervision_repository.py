class SupervisionRepository:
    def __init__(self, connection):
        self.connection = connection

    def obtener_mejores_vendedores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS nombre,
                    u.url_foto,
                    COALESCE(h_pv.puntoVenta, pdv.puntoVenta, 'Sin local asignado') AS local, 
                    SUM(dv.cantidad) AS cantidadVendida,
                    u.meta_ventas AS meta_asignada
                FROM USUARIOS u
                INNER JOIN VENTAS v ON u.idUsuario = v.idUsuario
                INNER JOIN DETALLE_VENTA dv ON v.idVenta = dv.idVenta
                LEFT JOIN HISTORIAL_ASIGNACIONES h ON h.idUsuario = u.idUsuario AND h.fecha_fin IS NULL
                LEFT JOIN PUNTOS_VENTA h_pv ON h.idPuntosVenta = h_pv.idPuntosVenta
                LEFT JOIN PUNTOS_VENTA pdv ON u.idUsuario = pdv.idUsuario AND pdv.tipo = 'VENTA'
                WHERE u.rol IN ('PROMOTOR', 'IMPULSADOR', 'VENDEDOR')
                GROUP BY u.idUsuario, u.nombres, u.apePaterno, u.url_foto, h_pv.puntoVenta, pdv.puntoVenta, u.meta_ventas
                ORDER BY cantidadVendida DESC;
            """
            cursor.execute(sql)
            vendedores = cursor.fetchall()
            
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
            
            # Puntos de Venta Activos de tipo VENTA
            cursor.execute("SELECT COUNT(*) AS pdv_activos FROM PUNTOS_VENTA WHERE estado = 'ACTIVO' AND tipo = 'VENTA'")
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
                    u.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS nombre,
                    u.url_foto,
                    COALESCE(h_pv.idPuntosVenta, pdv.idPuntosVenta) AS idPuntosVenta,
                    COALESCE(h_pv.puntoVenta, pdv.puntoVenta, 'Sin local asignado') AS local_pertenece,
                    u.meta_ventas AS meta_asignada,
                    COALESCE(SUM(v.total), 0) AS monto_vendido
                FROM USUARIOS u
                LEFT JOIN HISTORIAL_ASIGNACIONES h ON h.idUsuario = u.idUsuario AND h.fecha_fin IS NULL
                LEFT JOIN PUNTOS_VENTA h_pv ON h.idPuntosVenta = h_pv.idPuntosVenta
                LEFT JOIN PUNTOS_VENTA pdv ON u.idUsuario = pdv.idUsuario AND pdv.tipo = 'VENTA'
                LEFT JOIN VENTAS v ON u.idUsuario = v.idUsuario
                WHERE u.idUsuario = %s AND u.rol IN ('PROMOTOR', 'IMPULSADOR', 'VENDEDOR')
                GROUP BY u.idUsuario, u.nombres, u.apePaterno, u.url_foto, h_pv.idPuntosVenta, pdv.idPuntosVenta, h_pv.puntoVenta, pdv.puntoVenta, u.meta_ventas
            """
            cursor.execute(sql_info, (idUsuario,))
            vendedor = cursor.fetchone()
            
            if not vendedor:
                return None
                
            # Consulta 2: Lista de productos que vendió este trabajador (con imagen del producto)
            sql_productos = """
                SELECT 
                    p.idProductos,
                    p.producto AS nombre_producto, 
                    p.url_foto AS url_foto_producto,
                    SUM(dv.cantidad) AS cantidad_vendida
                FROM VENTAS v
                INNER JOIN DETALLE_VENTA dv ON v.idVenta = dv.idVenta
                INNER JOIN PRODUCTOS p ON dv.idProductos = p.idProductos
                WHERE v.idUsuario = %s
                GROUP BY p.idProductos, p.producto, p.url_foto
                ORDER BY cantidad_vendida DESC
            """
            cursor.execute(sql_productos, (idUsuario,))
            productos = cursor.fetchall()
            
            meta = float(vendedor['meta_asignada'])
            vendido = float(vendedor['monto_vendido'])
            porcentaje = round((vendido / meta) * 100, 2) if meta > 0 else 0
            
            return {
                "idUsuario": vendedor['idUsuario'],
                "nombre": vendedor['nombre'],
                "url_foto": vendedor['url_foto'],
                "idPuntosVenta": vendedor['idPuntosVenta'],
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
                    a.idAlertas,
                    p.idProductos,
                    p.producto AS nombre_producto,
                    p.url_foto AS url_foto_producto,
                    COALESCE(sr.cant_almacen, 0) AS stock_actual,
                    COALESCE(sr.stock_minimo, 0) AS stock_minimo,
                    pdv.idPuntosVenta,
                    pdv.puntoVenta AS local_nombre,
                    pdv.direccion AS local_direccion,
                    u.idUsuario AS responsable_id,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS responsable_nombre,
                    u.url_foto AS responsable_foto,
                    u.rol AS responsable_rol,
                    a.estado AS estado_resolucion,
                    a.severidad AS nivel_alerta
                FROM ALERTAS_STOCK a
                INNER JOIN PRODUCTOS p ON a.idProductos = p.idProductos
                INNER JOIN PUNTOS_VENTA pdv ON a.idPuntosVenta = pdv.idPuntosVenta
                INNER JOIN USUARIOS u ON pdv.idUsuario = u.idUsuario
                LEFT JOIN Pedido ped ON ped.idProductos = a.idProductos AND ped.idPuntosVenta = a.idPuntosVenta
                LEFT JOIN STOCK_REGISTROS sr ON sr.idPedido = ped.idPedido
                WHERE a.idAlertas = %s
                ORDER BY sr.fecha DESC
                LIMIT 1;
            """
            cursor.execute(sql, (idAlerta,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def listar_puntos_venta(self, estado=None):
        cursor = self.connection.cursor()
        try:
            query = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.idPuntosVenta AS id, 
                    pv.codigo,
                    pv.puntoVenta,
                    pv.puntoVenta AS nombre, 
                    pv.direccion, 
                    pv.estado,
                    pv.tipo,
                    d.distrito,
                    pv.idUsuario AS idImpulsador,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado,
                    u.url_foto AS impulsador_foto
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE pv.tipo = 'VENTA'
            """
            params = []
            if estado:
                query += " AND pv.estado = %s"
                params.append(estado)
            query += " ORDER BY pv.puntoVenta ASC"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en listar_puntos_venta: {e}")
            return None
        finally:
            cursor.close()

    def obtener_detalle_punto_venta(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql_pdv = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.codigo,
                    pv.puntoVenta,
                    pv.direccion,
                    pv.estado,
                    pv.latitud,
                    pv.longitud,
                    pv.radio_geocerca,
                    pv.tipo,
                    d.idDistrito,
                    d.distrito,
                    p.idProvincia,
                    p.provincia,
                    dep.idDepartamento,
                    dep.departamento,
                    u.idUsuario AS idImpulsador,
                    CONCAT(u.nombres, ' ', u.apePaterno, ' ', u.apeMaterno) AS impulsador_nombre,
                    u.correo AS impulsador_correo,
                    u.url_foto AS impulsador_foto,
                    u.meta_ventas AS impulsador_meta
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE pv.idPuntosVenta = %s AND pv.tipo = 'VENTA'
                LIMIT 1
            """
            cursor.execute(sql_pdv, (idPuntosVenta,))
            pdv = cursor.fetchone()
            if not pdv:
                return None

            # Productos asociados a este punto de venta con su imagen y stock mínimo
            sql_productos = """
                SELECT 
                    p.idProductos,
                    p.sku,
                    p.codigo_ean,
                    p.producto,
                    p.categoria,
                    p.descripcion,
                    p.url_foto,
                    p.estado,
                    pdvp.stock_minimo
                FROM PDV_PRODUCTOS pdvp
                INNER JOIN PRODUCTOS p ON pdvp.idProductos = p.idProductos
                WHERE pdvp.idPuntosVenta = %s AND p.estado = 'ACTIVO'
                ORDER BY p.producto ASC
            """
            cursor.execute(sql_productos, (idPuntosVenta,))
            productos = cursor.fetchall()
            pdv['productos'] = productos

            return pdv
        finally:
            cursor.close()

    def obtener_historial_impulsadores(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "SELECT idPuntosVenta, puntoVenta, tipo FROM PUNTOS_VENTA WHERE idPuntosVenta = %s",
                (idPuntosVenta,)
            )
            pdv = cursor.fetchone()
            if not pdv:
                return None, "Punto de venta no encontrado"
            if pdv['tipo'] != 'VENTA':
                return None, "El punto de venta no es de tipo VENTA"

            sql = """
                SELECT 
                    h.idHistorial,
                    h.idPuntosVenta,
                    pv.puntoVenta,
                    DATE_FORMAT(h.fecha_inicio, '%%Y-%%m-%%d') AS fecha_inicio,
                    DATE_FORMAT(h.fecha_fin, '%%Y-%%m-%%d') AS fecha_fin,
                    h.motivo,
                    h.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno, ' ', u.apeMaterno) AS impulsador_nombre,
                    u.correo AS impulsador_correo,
                    u.url_foto AS impulsador_foto,
                    u.rol AS impulsador_rol,
                    h.idUsuarioRegistra,
                    CONCAT(ur.nombres, ' ', ur.apePaterno) AS registrado_por,
                    CASE WHEN h.fecha_fin IS NULL THEN 1 ELSE 0 END AS es_actual
                FROM HISTORIAL_ASIGNACIONES h
                INNER JOIN PUNTOS_VENTA pv ON h.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN USUARIOS u ON h.idUsuario = u.idUsuario
                LEFT JOIN USUARIOS ur ON h.idUsuarioRegistra = ur.idUsuario
                WHERE h.idPuntosVenta = %s
                ORDER BY (h.fecha_fin IS NULL) DESC, h.fecha_inicio DESC, h.idHistorial DESC
            """
            cursor.execute(sql, (idPuntosVenta,))
            historial = cursor.fetchall()
            return historial, "Historial obtenido correctamente"
        finally:
            cursor.close()

    def reasignar_impulsador(self, idPuntosVenta, idUsuario, idUsuarioRegistra, motivo=None):
        cursor = self.connection.cursor()
        try:
            # 1. Validar punto de venta
            cursor.execute(
                "SELECT idPuntosVenta, puntoVenta, estado, tipo, idUsuario FROM PUNTOS_VENTA WHERE idPuntosVenta = %s",
                (idPuntosVenta,)
            )
            pdv = cursor.fetchone()
            if not pdv:
                return None, "Punto de venta no encontrado", 404
            if pdv['tipo'] != 'VENTA':
                return None, "El punto de venta debe ser de tipo VENTA", 400
            if pdv['estado'] != 'ACTIVO':
                return None, "El punto de venta no está ACTIVO", 400

            # 2. Validar impulsador
            cursor.execute(
                "SELECT idUsuario, CONCAT(nombres, ' ', apePaterno) AS nombre, rol, estado FROM USUARIOS WHERE idUsuario = %s",
                (idUsuario,)
            )
            usuario = cursor.fetchone()
            if not usuario:
                return None, "Impulsador no encontrado", 404
            if usuario['estado'] != 'ACTIVO':
                return None, "El impulsador no está ACTIVO", 400
            if usuario['rol'] not in ('IMPULSADOR', 'PROMOTOR', 'VENDEDOR'):
                return None, f"El usuario tiene rol {usuario['rol']}, debe ser IMPULSADOR o PROMOTOR", 400

            # Si ya está asignado al mismo PDV
            if pdv['idUsuario'] == idUsuario:
                return None, f"{usuario['nombre']} ya se encuentra actualmente asignado a {pdv['puntoVenta']}", 400

            # 3. Validar registrador
            cursor.execute("SELECT idUsuario FROM USUARIOS WHERE idUsuario = %s", (idUsuarioRegistra,))
            if not cursor.fetchone():
                return None, "Usuario que registra la asignación no existe", 400

            # 4. Transacción de reasignación
            # a) Cerrar la asignación anterior en este punto de venta
            cursor.execute("""
                UPDATE HISTORIAL_ASIGNACIONES 
                SET fecha_fin = CURDATE() 
                WHERE idPuntosVenta = %s AND fecha_fin IS NULL
            """, (idPuntosVenta,))

            # b) Cerrar cualquier otra asignación activa que tuviera este impulsador
            cursor.execute("""
                UPDATE HISTORIAL_ASIGNACIONES 
                SET fecha_fin = CURDATE() 
                WHERE idUsuario = %s AND fecha_fin IS NULL
            """, (idUsuario,))

            # c) Actualizar PUNTOS_VENTA
            # Si este impulsador estaba asociado a otro punto de venta en PUNTOS_VENTA, reasignarlo para no duplicar
            cursor.execute("SELECT idPuntosVenta FROM PUNTOS_VENTA WHERE idUsuario = %s AND idPuntosVenta != %s", (idUsuario, idPuntosVenta))
            pdvs_previos = cursor.fetchall()
            for pdv_previo in pdvs_previos:
                nuevo_encargado = pdv['idUsuario'] if pdv['idUsuario'] != idUsuario else idUsuarioRegistra
                cursor.execute("UPDATE PUNTOS_VENTA SET idUsuario = %s WHERE idPuntosVenta = %s", (nuevo_encargado, pdv_previo['idPuntosVenta']))

            cursor.execute("""
                UPDATE PUNTOS_VENTA 
                SET idUsuario = %s 
                WHERE idPuntosVenta = %s
            """, (idUsuario, idPuntosVenta))

            # d) Registrar nueva asignación en HISTORIAL_ASIGNACIONES
            cursor.execute("""
                INSERT INTO HISTORIAL_ASIGNACIONES (
                    fecha_inicio,
                    fecha_fin,
                    motivo,
                    idPuntosVenta,
                    idUsuario,
                    idUsuarioRegistra
                ) VALUES (CURDATE(), NULL, %s, %s, %s, %s)
            """, (motivo or "Reasignación de punto de venta", idPuntosVenta, idUsuario, idUsuarioRegistra))

            id_historial = cursor.lastrowid
            self.connection.commit()

            from datetime import date
            return {
                "idHistorial": id_historial,
                "idPuntosVenta": idPuntosVenta,
                "puntoVenta": pdv['puntoVenta'],
                "idUsuario": idUsuario,
                "impulsador": usuario['nombre'],
                "motivo": motivo or "Reasignación de punto de venta",
                "fecha_inicio": date.today().strftime("%Y-%m-%d")
            }, "Impulsador reasignado exitosamente al punto de venta", 200
        except Exception as e:
            self.connection.rollback()
            print(f"Error en reasignar_impulsador: {e}")
            raise e
        finally:
            cursor.close()

    def listar_impulsadores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno, ' ', u.apeMaterno) AS nombre_completo,
                    u.correo,
                    u.rol,
                    u.url_foto,
                    u.meta_ventas,
                    COALESCE(h_pv.idPuntosVenta, pv.idPuntosVenta) AS idPuntosVenta,
                    COALESCE(h_pv.puntoVenta, pv.puntoVenta, 'Sin local asignado') AS local_actual
                FROM USUARIOS u
                LEFT JOIN HISTORIAL_ASIGNACIONES h ON h.idUsuario = u.idUsuario AND h.fecha_fin IS NULL
                LEFT JOIN PUNTOS_VENTA h_pv ON h.idPuntosVenta = h_pv.idPuntosVenta
                LEFT JOIN PUNTOS_VENTA pv ON u.idUsuario = pv.idUsuario AND pv.tipo = 'VENTA'
                WHERE u.rol IN ('IMPULSADOR', 'PROMOTOR') AND u.estado = 'ACTIVO'
                ORDER BY u.nombres ASC, u.apePaterno ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def buscar_foto_impulsador(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT idUsuario, url_foto FROM USUARIOS WHERE idUsuario = %s LIMIT 1"
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def buscar_foto_producto(self, idProductos):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT idProductos, producto, url_foto FROM PRODUCTOS WHERE idProductos = %s LIMIT 1"
            cursor.execute(sql, (idProductos,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def listar_alertas(self):
        cursor = self.connection.cursor()
        try:
            query = """
                SELECT 
                    a.idAlertas AS idAlerta,
                    a.estado AS estado_resolucion,
                    a.tipo AS nivel_alerta,
                    pv.puntoVenta AS local_nombre,
                    p.producto AS nombre_producto
                FROM ALERTAS_STOCK a
                INNER JOIN PUNTOS_VENTA pv ON a.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN PRODUCTOS p ON a.idProductos = p.idProductos
                ORDER BY a.idAlertas DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en listar_alertas: {e}")
            return None
        finally:
            cursor.close()

    # ── 7. RENDIMIENTO HISTÓRICO Y ASIGNACIONES DEL PERSONAL ────────────────────
    def obtener_rendimiento_historico(self, idUsuario, anio=None):
        cursor = self.connection.cursor()
        try:
            from datetime import date
            hoy = date.today()

            # 1. Obtener datos del colaborador
            sql_usuario = """
                SELECT 
                    u.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno, ' ', u.apeMaterno) AS nombre_completo,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS nombre_corto,
                    u.correo,
                    u.rol,
                    u.url_foto,
                    u.meta_ventas AS meta_asignada,
                    COALESCE(h_pv.idPuntosVenta, pdv.idPuntosVenta) AS idPuntosVentaActual,
                    COALESCE(h_pv.puntoVenta, pdv.puntoVenta, 'Sin local asignado') AS local_actual,
                    COALESCE(h_pv.direccion, pdv.direccion) AS direccion_local_actual
                FROM USUARIOS u
                LEFT JOIN HISTORIAL_ASIGNACIONES h ON h.idUsuario = u.idUsuario AND h.fecha_fin IS NULL
                LEFT JOIN PUNTOS_VENTA h_pv ON h.idPuntosVenta = h_pv.idPuntosVenta
                LEFT JOIN PUNTOS_VENTA pdv ON u.idUsuario = pdv.idUsuario AND pdv.tipo = 'VENTA'
                WHERE u.idUsuario = %s
                LIMIT 1
            """
            cursor.execute(sql_usuario, (idUsuario,))
            usuario = cursor.fetchone()
            if not usuario:
                return None, "Colaborador no encontrado", 404

            meta_base = float(usuario.get("meta_asignada") or 0.0)

            # 2. Obtener avance por meses (histórico de ventas agrupadas)
            sql_meses = """
                SELECT 
                    YEAR(v.fecha) AS anio,
                    MONTH(v.fecha) AS mes,
                    COALESCE(SUM(v.total), 0) AS monto_vendido,
                    COALESCE(SUM(dv.cantidad), 0) AS unidades_vendidas,
                    COUNT(DISTINCT v.idVenta) AS cantidad_ventas
                FROM VENTAS v
                LEFT JOIN DETALLE_VENTA dv ON v.idVenta = dv.idVenta
                WHERE v.idUsuario = %s
            """
            params_meses = [idUsuario]
            if anio:
                sql_meses += " AND YEAR(v.fecha) = %s"
                params_meses.append(int(anio))

            sql_meses += " GROUP BY YEAR(v.fecha), MONTH(v.fecha) ORDER BY anio DESC, mes DESC"
            cursor.execute(sql_meses, tuple(params_meses))
            rows_meses = cursor.fetchall() or []

            MESES_ES = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }

            periodos_existentes = {f"{int(r['anio'])}-{int(r['mes']):02d}" for r in rows_meses}
            periodo_actual = f"{hoy.year}-{hoy.month:02d}"

            # Si el mes actual no tiene ventas registradas y entra en el filtro de año, agregarlo para monitorear meta en curso
            if (not anio or int(anio) == hoy.year) and periodo_actual not in periodos_existentes:
                rows_meses.insert(0, {
                    "anio": hoy.year,
                    "mes": hoy.month,
                    "monto_vendido": 0.0,
                    "unidades_vendidas": 0,
                    "cantidad_ventas": 0
                })

            avance_mensual = []
            meses_cumplidos_count = 0
            for r in rows_meses:
                anio_val = int(r["anio"])
                mes_val = int(r["mes"])
                monto_val = float(r["monto_vendido"] or 0.0)
                unidades_val = int(r["unidades_vendidas"] or 0)
                ventas_val = int(r["cantidad_ventas"] or 0)

                porcentaje = round((monto_val / meta_base) * 100, 2) if meta_base > 0 else 0.0
                cumplio = (monto_val >= meta_base) if meta_base > 0 else False
                diferencia = round(monto_val - meta_base, 2)

                if anio_val == hoy.year and mes_val == hoy.month:
                    estado_meta = "CUMPLIDA" if cumplio else "EN_PROCESO"
                else:
                    estado_meta = "CUMPLIDA" if cumplio else "NO_CUMPLIDA"

                if cumplio:
                    meses_cumplidos_count += 1

                avance_mensual.append({
                    "anio": anio_val,
                    "mes": mes_val,
                    "mes_nombre": MESES_ES.get(mes_val, f"Mes {mes_val}"),
                    "periodo": f"{anio_val}-{mes_val:02d}",
                    "monto_vendido": monto_val,
                    "unidades_vendidas": unidades_val,
                    "cantidad_transacciones": ventas_val,
                    "meta_mensual": meta_base,
                    "porcentaje_cumplimiento": porcentaje,
                    "cumplio_meta": cumplio,
                    "diferencia_meta": diferencia,
                    "estado_meta": estado_meta
                })

            total_monto_historico = round(sum(m["monto_vendido"] for m in avance_mensual), 2)
            total_unidades_historico = sum(m["unidades_vendidas"] for m in avance_mensual)
            total_transacciones_historico = sum(m["cantidad_transacciones"] for m in avance_mensual)
            total_meses = len(avance_mensual)
            tasa_exito = round((meses_cumplidos_count / total_meses) * 100, 2) if total_meses > 0 else 0.0

            resumen_kpi = {
                "monto_total_historico": total_monto_historico,
                "unidades_totales_historico": total_unidades_historico,
                "total_transacciones_historico": total_transacciones_historico,
                "meses_evaluados": total_meses,
                "meses_meta_cumplida": meses_cumplidos_count,
                "tasa_cumplimiento_metas": tasa_exito
            }

            # 3. Obtener historial de asignaciones de puntos de venta
            sql_historial = """
                SELECT 
                    h.idHistorial,
                    h.idPuntosVenta,
                    pv.codigo AS codigo_pdv,
                    pv.puntoVenta AS nombre_pdv,
                    pv.puntoVenta,
                    pv.direccion,
                    pv.tipo AS tipo_pdv,
                    d.distrito,
                    p.provincia,
                    dep.departamento,
                    DATE_FORMAT(h.fecha_inicio, '%%Y-%%m-%%d') AS fecha_inicio,
                    DATE_FORMAT(h.fecha_fin, '%%Y-%%m-%%d') AS fecha_fin,
                    h.motivo,
                    CASE WHEN h.fecha_fin IS NULL THEN 1 ELSE 0 END AS es_actual,
                    h.idUsuarioRegistra,
                    CONCAT(ur.nombres, ' ', ur.apePaterno) AS registrado_por
                FROM HISTORIAL_ASIGNACIONES h
                INNER JOIN PUNTOS_VENTA pv ON h.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS ur ON h.idUsuarioRegistra = ur.idUsuario
                WHERE h.idUsuario = %s
                ORDER BY (h.fecha_fin IS NULL) DESC, h.fecha_inicio DESC, h.idHistorial DESC
            """
            cursor.execute(sql_historial, (idUsuario,))
            historial_asig = cursor.fetchall() or []

            # Si aún no tiene registros en HISTORIAL_ASIGNACIONES pero tiene punto de venta asignado
            if not historial_asig and usuario.get("idPuntosVentaActual"):
                sql_pdv_actual = """
                    SELECT 
                        pv.idPuntosVenta,
                        pv.codigo AS codigo_pdv,
                        pv.puntoVenta AS nombre_pdv,
                        pv.puntoVenta,
                        pv.direccion,
                        pv.tipo AS tipo_pdv,
                        d.distrito,
                        p.provincia,
                        dep.departamento
                    FROM PUNTOS_VENTA pv
                    INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                    INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                    INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                    WHERE pv.idPuntosVenta = %s
                    LIMIT 1
                """
                cursor.execute(sql_pdv_actual, (usuario["idPuntosVentaActual"],))
                pdv_row = cursor.fetchone()
                if pdv_row:
                    historial_asig.append({
                        "idHistorial": 0,
                        "idPuntosVenta": pdv_row["idPuntosVenta"],
                        "codigo_pdv": pdv_row["codigo_pdv"],
                        "nombre_pdv": pdv_row["nombre_pdv"],
                        "puntoVenta": pdv_row["puntoVenta"],
                        "direccion": pdv_row["direccion"],
                        "tipo_pdv": pdv_row["tipo_pdv"],
                        "distrito": pdv_row["distrito"],
                        "provincia": pdv_row["provincia"],
                        "departamento": pdv_row["departamento"],
                        "fecha_inicio": hoy.strftime("%Y-%m-%d"),
                        "fecha_fin": None,
                        "motivo": "Asignación inicial activa",
                        "es_actual": 1,
                        "idUsuarioRegistra": None,
                        "registrado_por": "Asignación Inicial"
                    })

            data = {
                "trabajador": {
                    "idUsuario": usuario["idUsuario"],
                    "nombre": usuario["nombre_completo"],
                    "nombre_corto": usuario["nombre_corto"],
                    "correo": usuario["correo"],
                    "rol": usuario["rol"],
                    "url_foto": usuario["url_foto"],
                    "meta_mensual": meta_base,
                    "local_actual": usuario["local_actual"],
                    "idPuntosVentaActual": usuario["idPuntosVentaActual"],
                    "direccion_local_actual": usuario["direccion_local_actual"]
                },
                "resumen": resumen_kpi,
                "avance_mensual": avance_mensual,
                "historial_asignaciones": historial_asig
            }

            return data, "Rendimiento histórico obtenido exitosamente", 200
        except Exception as e:
            print(f"Error en obtener_rendimiento_historico: {e}")
            return None, "Error interno al obtener rendimiento histórico", 500
        finally:
            cursor.close()

    def obtener_historial_asignaciones_usuario(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    h.idHistorial,
                    h.idPuntosVenta,
                    pv.codigo AS codigo_pdv,
                    pv.puntoVenta AS nombre_pdv,
                    pv.puntoVenta,
                    pv.direccion,
                    pv.tipo AS tipo_pdv,
                    d.distrito,
                    p.provincia,
                    dep.departamento,
                    DATE_FORMAT(h.fecha_inicio, '%%Y-%%m-%%d') AS fecha_inicio,
                    DATE_FORMAT(h.fecha_fin, '%%Y-%%m-%%d') AS fecha_fin,
                    h.motivo,
                    CASE WHEN h.fecha_fin IS NULL THEN 1 ELSE 0 END AS es_actual,
                    h.idUsuarioRegistra,
                    CONCAT(ur.nombres, ' ', ur.apePaterno) AS registrado_por
                FROM HISTORIAL_ASIGNACIONES h
                INNER JOIN PUNTOS_VENTA pv ON h.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS ur ON h.idUsuarioRegistra = ur.idUsuario
                WHERE h.idUsuario = %s
                ORDER BY (h.fecha_fin IS NULL) DESC, h.fecha_inicio DESC, h.idHistorial DESC
            """
            cursor.execute(sql, (idUsuario,))
            historial = cursor.fetchall() or []
            return historial, "Historial de asignaciones obtenido correctamente", 200
        except Exception as e:
            print(f"Error en obtener_historial_asignaciones_usuario: {e}")
            return None, "Error interno al obtener historial de asignaciones", 500
        finally:
            cursor.close()
