from datetime import datetime, date


class ImpulsadorRepository:
    def __init__(self, connection):
        self.connection = connection

    # ── 1. DATOS DEL IMPULSADOR Y SU LOCAL ACTUAL ──────────────────────────────
    def obtener_datos_impulsador(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    CONCAT(u.nombres, ' ', u.apePaterno, ' ', u.apeMaterno) AS nombre_completo,
                    u.correo,
                    u.rol,
                    u.url_foto,
                    u.meta_ventas,
                    u.estado
                FROM USUARIOS u
                WHERE u.idUsuario = %s
                LIMIT 1
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def obtener_asignacion_actual(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pv.idPuntosVenta,
                    pv.codigo,
                    pv.puntoVenta AS nombre,
                    pv.direccion,
                    pv.estado,
                    pv.latitud,
                    pv.longitud,
                    50.00 AS radio_geocerca,
                    pv.tipo,
                    d.idDistrito,
                    d.distrito,
                    p.idProvincia,
                    p.provincia,
                    dep.idDepartamento,
                    dep.departamento
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                WHERE pv.idUsuario = %s AND pv.estado = 'ACTIVO' AND pv.tipo = 'VENTA'
                LIMIT 1
            """
            cursor.execute(sql, (idUsuario,))
            pdv = cursor.fetchone()

            # Si no está en PUNTOS_VENTA directamente, buscar en HISTORIAL_ASIGNACIONES activa
            if not pdv:
                sql_hist = """
                    SELECT 
                        pv.idPuntosVenta,
                        pv.codigo,
                        pv.puntoVenta AS nombre,
                        pv.direccion,
                        pv.estado,
                        pv.latitud,
                        pv.longitud,
                        50.00 AS radio_geocerca,
                        pv.tipo,
                        d.idDistrito,
                        d.distrito,
                        p.idProvincia,
                        p.provincia,
                        dep.idDepartamento,
                        dep.departamento
                    FROM HISTORIAL_ASIGNACIONES h
                    INNER JOIN PUNTOS_VENTA pv ON h.idPuntosVenta = pv.idPuntosVenta
                    INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                    INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                    INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                    WHERE h.idUsuario = %s AND h.fecha_fin IS NULL AND pv.estado = 'ACTIVO'
                    ORDER BY h.fecha_inicio DESC
                    LIMIT 1
                """
                cursor.execute(sql_hist, (idUsuario,))
                pdv = cursor.fetchone()

            return pdv
        finally:
            cursor.close()

    def obtener_resumen_ventas(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            # Ventas de hoy
            sql_hoy = """
                SELECT 
                    COALESCE(SUM(v.total), 0) AS monto_hoy,
                    COALESCE(SUM(dv.cantidad), 0) AS unidades_hoy,
                    COUNT(DISTINCT v.idVenta) AS transacciones_hoy
                FROM VENTAS v
                LEFT JOIN DETALLE_VENTA dv ON v.idVenta = dv.idVenta
                WHERE v.idUsuario = %s AND v.fecha = CURDATE()
            """
            cursor.execute(sql_hoy, (idUsuario,))
            resumen_hoy = cursor.fetchone() or {"monto_hoy": 0, "unidades_hoy": 0, "transacciones_hoy": 0}

            # Ventas del mes actual
            sql_mes = """
                SELECT 
                    COALESCE(SUM(v.total), 0) AS monto_mes,
                    COALESCE(SUM(dv.cantidad), 0) AS unidades_mes
                FROM VENTAS v
                LEFT JOIN DETALLE_VENTA dv ON v.idVenta = dv.idVenta
                WHERE v.idUsuario = %s 
                  AND MONTH(v.fecha) = MONTH(CURDATE()) 
                  AND YEAR(v.fecha) = YEAR(CURDATE())
            """
            cursor.execute(sql_mes, (idUsuario,))
            resumen_mes = cursor.fetchone() or {"monto_mes": 0, "unidades_mes": 0}

            return {
                "monto_hoy": float(resumen_hoy["monto_hoy"]),
                "unidades_hoy": int(resumen_hoy["unidades_hoy"]),
                "transacciones_hoy": int(resumen_hoy["transacciones_hoy"]),
                "monto_mes": float(resumen_mes["monto_mes"]),
                "unidades_mes": int(resumen_mes["unidades_mes"])
            }
        finally:
            cursor.close()

    def obtener_resumen_inventario_pdv(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    COUNT(*) AS total_productos,
                    COALESCE(SUM(CASE WHEN pdvp.stock_actual <= pdvp.stock_minimo AND pdvp.stock_actual > 0 THEN 1 ELSE 0 END), 0) AS stock_bajo,
                    COALESCE(SUM(CASE WHEN pdvp.stock_actual = 0 THEN 1 ELSE 0 END), 0) AS stock_agotado
                FROM PDV_PRODUCTOS pdvp
                INNER JOIN PRODUCTOS p ON pdvp.idProductos = p.idProductos
                WHERE pdvp.idPuntosVenta = %s AND p.estado = 'ACTIVO'
            """
            cursor.execute(sql, (idPuntosVenta,))
            row = cursor.fetchone() or {"total_productos": 0, "stock_bajo": 0, "stock_agotado": 0}
            return {
                "total_productos": int(row["total_productos"]),
                "stock_bajo": int(row["stock_bajo"]),
                "stock_agotado": int(row["stock_agotado"])
            }
        finally:
            cursor.close()

    def obtener_horario(self):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT clave, valor FROM CONFIGURACION WHERE clave IN ('HORA_ENTRADA_IMPULSADOR', 'HORA_SALIDA_IMPULSADOR', 'HORA_ENTRADA', 'HORA_SALIDA')"
            cursor.execute(sql)
            configs = {row["clave"]: row["valor"] for row in cursor.fetchall()}

            hora_inicio = configs.get("HORA_ENTRADA_IMPULSADOR") or configs.get("HORA_ENTRADA") or "08:30:00"
            hora_fin = configs.get("HORA_SALIDA_IMPULSADOR") or configs.get("HORA_SALIDA") or "17:30:00"

            return {
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin,
                "jornada": f"{hora_inicio[:5]} - {hora_fin[:5]}"
            }
        except Exception:
            return {
                "hora_inicio": "08:30:00",
                "hora_fin": "17:30:00",
                "jornada": "08:30 - 17:30"
            }
        finally:
            cursor.close()

    # ── 2. HISTORIAL DE ASIGNACIONES ──────────────────────────────────────────
    def obtener_historial_asignaciones(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    h.idHistorial,
                    h.idPuntosVenta,
                    pv.codigo AS codigo_pdv,
                    pv.puntoVenta AS nombre_pdv,
                    pv.direccion,
                    d.distrito,
                    DATE_FORMAT(h.fecha_inicio, '%%Y-%%m-%%d') AS fecha_inicio,
                    DATE_FORMAT(h.fecha_fin, '%%Y-%%m-%%d') AS fecha_fin,
                    h.motivo,
                    CASE WHEN h.fecha_fin IS NULL THEN 1 ELSE 0 END AS es_actual
                FROM HISTORIAL_ASIGNACIONES h
                INNER JOIN PUNTOS_VENTA pv ON h.idPuntosVenta = pv.idPuntosVenta
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                WHERE h.idUsuario = %s
                ORDER BY h.fecha_inicio DESC, h.idHistorial DESC
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 3. CATÁLOGO Y BÚSQUEDA DE PRODUCTOS EN EL LOCAL ───────────────────────
    def buscar_producto_por_codigo(self, idPuntosVenta, codigo):
        codigo = str(codigo).strip()
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    p.idProductos,
                    p.sku,
                    p.codigo_ean,
                    p.producto,
                    p.categoria,
                    p.descripcion,
                    p.url_foto,
                    p.estado,
                    pdvp.stock_actual,
                    pdvp.stock_minimo,
                    pdvp.precio
                FROM PDV_PRODUCTOS pdvp
                INNER JOIN PRODUCTOS p ON pdvp.idProductos = p.idProductos
                WHERE pdvp.idPuntosVenta = %s
                  AND (p.codigo_ean = %s OR p.sku = %s)
                  AND p.estado = 'ACTIVO'
                LIMIT 1
            """
            cursor.execute(sql, (idPuntosVenta, codigo, codigo))
            return cursor.fetchone()
        finally:
            cursor.close()

    def listar_productos_pdv(self, idPuntosVenta, search=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    p.idProductos,
                    p.sku,
                    p.codigo_ean,
                    p.producto,
                    p.categoria,
                    p.descripcion,
                    p.url_foto,
                    pdvp.stock_actual,
                    pdvp.stock_minimo,
                    pdvp.precio,
                    CASE 
                        WHEN pdvp.stock_actual = 0 THEN 'AGOTADO'
                        WHEN pdvp.stock_actual <= pdvp.stock_minimo THEN 'BAJO'
                        ELSE 'OPTIMO'
                    END AS estado_stock
                FROM PDV_PRODUCTOS pdvp
                INNER JOIN PRODUCTOS p ON pdvp.idProductos = p.idProductos
                WHERE pdvp.idPuntosVenta = %s AND p.estado = 'ACTIVO'
            """
            params = [idPuntosVenta]
            if search:
                sql += " AND (p.producto LIKE %s OR p.codigo_ean LIKE %s OR p.sku LIKE %s)"
                term = f"%{search}%"
                params.extend([term, term, term])

            sql += " ORDER BY p.producto ASC"
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 4. REGISTRAR VENTA (TRANSACCIÓN) ───────────────────────────────────────
    def registrar_venta(self, idUsuario, idPuntosVenta, idProductos, cantidad):
        cursor = self.connection.cursor()
        try:
            # a) Bloquear la fila del producto en el PDV para lectura consistente
            sql_check = """
                SELECT 
                    pdvp.stock_actual,
                    pdvp.stock_minimo,
                    pdvp.precio,
                    p.producto,
                    p.codigo_ean
                FROM PDV_PRODUCTOS pdvp
                INNER JOIN PRODUCTOS p ON pdvp.idProductos = p.idProductos
                WHERE pdvp.idPuntosVenta = %s AND pdvp.idProductos = %s
                FOR UPDATE
            """
            cursor.execute(sql_check, (idPuntosVenta, idProductos))
            prod_info = cursor.fetchone()

            if not prod_info:
                return None, "El producto no está asignado a este punto de venta", 404

            stock_actual = prod_info["stock_actual"]
            stock_minimo = prod_info["stock_minimo"]
            precio_unitario = float(prod_info["precio"])
            nombre_producto = prod_info["producto"]
            codigo_ean = prod_info["codigo_ean"]

            if stock_actual < cantidad:
                return None, f"Stock insuficiente para '{nombre_producto}'. Stock disponible: {stock_actual}, solicitado: {cantidad}", 400

            subtotal = round(precio_unitario * cantidad, 2)
            nuevo_stock = stock_actual - cantidad

            # b) Insertar cabecera de la venta
            sql_venta = """
                INSERT INTO VENTAS (fecha, hora, total, idUsuario)
                VALUES (CURDATE(), CURTIME(), %s, %s)
            """
            cursor.execute(sql_venta, (subtotal, idUsuario))
            idVenta = cursor.lastrowid

            # c) Insertar detalle de la venta
            sql_detalle = """
                INSERT INTO DETALLE_VENTA (idVenta, idProductos, precio, cantidad)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_detalle, (idVenta, idProductos, precio_unitario, cantidad))

            # d) Descontar stock en PDV_PRODUCTOS
            sql_update_pdv = """
                UPDATE PDV_PRODUCTOS 
                SET stock_actual = %s 
                WHERE idPuntosVenta = %s AND idProductos = %s
            """
            cursor.execute(sql_update_pdv, (nuevo_stock, idPuntosVenta, idProductos))

            # e) Sincronizar en STOCK_REGISTROS si existe registro activo
            sql_sync_stock = """
                SELECT sr.idStock, sr.cant_exhibida, sr.cant_almacen, sr.idPedido
                FROM Pedido ped
                INNER JOIN STOCK_REGISTROS sr ON sr.idPedido = ped.idPedido
                WHERE ped.idPuntosVenta = %s AND ped.idProductos = %s
                ORDER BY sr.fecha DESC
                LIMIT 1
                FOR UPDATE
            """
            cursor.execute(sql_sync_stock, (idPuntosVenta, idProductos))
            sr_row = cursor.fetchone()

            if sr_row:
                idStock = sr_row["idStock"]
                cant_exh = sr_row["cant_exhibida"]
                cant_alm = sr_row["cant_almacen"]

                # Descontar preferentemente de exhibición
                if cant_exh >= cantidad:
                    cant_exh -= cantidad
                else:
                    restante = cantidad - cant_exh
                    cant_exh = 0
                    cant_alm = max(0, cant_alm - restante)

                estado_sr = "AGOTADO" if (cant_exh + cant_alm) == 0 else ("BAJO" if (cant_exh + cant_alm) <= stock_minimo else "OPTIMO")

                cursor.execute("""
                    UPDATE STOCK_REGISTROS 
                    SET cant_exhibida = %s, cant_almacen = %s, estadoStock = %s, fecha = NOW()
                    WHERE idStock = %s
                """, (cant_exh, cant_alm, estado_sr, idStock))

            # f) Lógica de ALERTA automática si stock llega a nivel crítico
            alerta_generada = False
            idAlerta = None
            if nuevo_stock <= stock_minimo:
                # Comprobar si ya existe una alerta PENDIENTE para este producto en este local
                cursor.execute("""
                    SELECT idAlertas FROM ALERTAS_STOCK 
                    WHERE idPuntosVenta = %s AND idProductos = %s AND estado = 'PENDIENTE'
                    LIMIT 1
                """, (idPuntosVenta, idProductos))
                alerta_existente = cursor.fetchone()

                if not alerta_existente:
                    severidad = "ALTA" if nuevo_stock <= 0 else "MEDIA"
                    tipo_alerta = "STOCK_AGOTADO" if nuevo_stock <= 0 else "STOCK_MINIMO"
                    comentario = f"Stock en nivel crítico tras venta. Stock actual: {nuevo_stock}, Mínimo: {stock_minimo}"

                    cursor.execute("""
                        INSERT INTO ALERTAS_STOCK (
                            tipo,
                            estado,
                            comentario,
                            fechaEmision,
                            horaEmision,
                            severidad,
                            idProductos,
                            idPuntosVenta
                        ) VALUES (%s, 'PENDIENTE', %s, CURDATE(), CURTIME(), %s, %s, %s)
                    """, (tipo_alerta, comentario, severidad, idProductos, idPuntosVenta))
                    idAlerta = cursor.lastrowid
                    alerta_generada = True

            self.connection.commit()

            resultado = {
                "idVenta": idVenta,
                "idProductos": idProductos,
                "producto": nombre_producto,
                "codigo_ean": codigo_ean,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "total": subtotal,
                "stock_anterior": stock_actual,
                "stock_actual": nuevo_stock,
                "stock_minimo": stock_minimo,
                "alerta_generada": alerta_generada,
                "idAlerta": idAlerta
            }

            mensaje = "Venta registrada exitosamente"
            if alerta_generada:
                mensaje += " (Alerta de stock bajo emitida automáticamente)"

            return resultado, mensaje, 201

        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    # ── 5. REPORTAR INCIDENCIA ─────────────────────────────────────────────────
    def registrar_incidencia(self, idUsuario, idPuntosVenta, tipo, severidad, descripcion, ruta_evidencia=None, hash_sha=None):
        cursor = self.connection.cursor()
        try:
            sql_incidencia = """
                INSERT INTO INCIDENCIAS (
                    tipo,
                    severidad,
                    descripcion,
                    estado,
                    fecha_registro,
                    idUsuario,
                    idPuntosVenta
                ) VALUES (%s, %s, %s, 'ABIERTO', NOW(), %s, %s)
            """
            cursor.execute(sql_incidencia, (tipo, severidad or "MEDIA", descripcion, idUsuario, idPuntosVenta))
            idIncidencias = cursor.lastrowid

            idEvidencia = None
            if ruta_evidencia and hash_sha:
                sql_evidencia = """
                    INSERT INTO EVIDENCIAS (
                        ruta_archivo,
                        hash_sha,
                        tipo,
                        fecha_captura,
                        idIncidencias
                    ) VALUES (%s, %s, %s, NOW(), %s)
                """
                cursor.execute(sql_evidencia, (ruta_evidencia, hash_sha, tipo, idIncidencias))
                idEvidencia = cursor.lastrowid

            self.connection.commit()

            return {
                "idIncidencias": idIncidencias,
                "tipo": tipo,
                "severidad": severidad or "MEDIA",
                "descripcion": descripcion,
                "estado": "ABIERTO",
                "idPuntosVenta": idPuntosVenta,
                "idEvidencia": idEvidencia,
                "tiene_foto": bool(ruta_evidencia)
            }, "Incidencia reportada exitosamente", 201

        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
