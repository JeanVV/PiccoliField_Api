class ProspectoRepository:
    def __init__(self, connection):
        self.connection = connection

    def listar(self, estado=None, potencial=None, idDistrito=None, idUsuario=None, search=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pr.idProspectos,
                    pr.nombre_comercial,
                    pr.tipo_local,
                    pr.direccion,
                    pr.contacto,
                    pr.telefono,
                    pr.potencial,
                    pr.estado,
                    pr.notas,
                    pr.motivo_descarte,
                    pr.url_foto,
                    pr.latitud,
                    pr.longitud,
                    pr.fecha_registro,
                    pr.fecha_cierre,
                    pr.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado,
                    pr.idDistrito,
                    d.distrito,
                    p.provincia,
                    dep.departamento
                FROM PROSPECTOS pr
                INNER JOIN DISTRITO d ON pr.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS u ON pr.idUsuario = u.idUsuario
                WHERE 1=1
            """
            params = []

            if estado:
                sql += " AND pr.estado = %s"
                params.append(estado.upper())

            if potencial:
                sql += " AND pr.potencial = %s"
                params.append(potencial.upper())

            if idDistrito:
                sql += " AND pr.idDistrito = %s"
                params.append(int(idDistrito))

            if idUsuario:
                sql += " AND pr.idUsuario = %s"
                params.append(int(idUsuario))

            if search:
                sql += """ AND (
                    pr.nombre_comercial LIKE %s OR 
                    pr.direccion LIKE %s OR 
                    pr.contacto LIKE %s OR 
                    pr.telefono LIKE %s
                )"""
                term = f"%{search}%"
                params.extend([term, term, term, term])

            sql += " ORDER BY pr.idProspectos DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def buscar_por_id(self, idProspectos):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    pr.idProspectos,
                    pr.nombre_comercial,
                    pr.tipo_local,
                    pr.direccion,
                    pr.contacto,
                    pr.telefono,
                    pr.potencial,
                    pr.estado,
                    pr.notas,
                    pr.motivo_descarte,
                    pr.url_foto,
                    pr.latitud,
                    pr.longitud,
                    pr.fecha_registro,
                    pr.fecha_cierre,
                    pr.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado,
                    u.correo AS correo_promotor,
                    pr.idDistrito,
                    d.distrito,
                    p.provincia,
                    dep.departamento
                FROM PROSPECTOS pr
                INNER JOIN DISTRITO d ON pr.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS u ON pr.idUsuario = u.idUsuario
                WHERE pr.idProspectos = %s
                LIMIT 1
            """
            cursor.execute(sql, (idProspectos,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def crear(self, data):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO PROSPECTOS (
                    nombre_comercial,
                    tipo_local,
                    direccion,
                    contacto,
                    telefono,
                    potencial,
                    estado,
                    notas,
                    motivo_descarte,
                    url_foto,
                    latitud,
                    longitud,
                    fecha_registro,
                    idUsuario,
                    idDistrito
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s
                )
            """
            cursor.execute(sql, (
                data["nombre_comercial"],
                data.get("tipo_local"),
                data["direccion"],
                data.get("contacto"),
                data.get("telefono"),
                data.get("potencial", "MEDIO"),
                data.get("estado", "NUEVO"),
                data.get("notas"),
                data.get("motivo_descarte"),
                data.get("url_foto"),
                data["latitud"],
                data["longitud"],
                data["idUsuario"],
                data["idDistrito"]
            ))
            idProspecto = cursor.lastrowid
            self.connection.commit()
            return self.buscar_por_id(idProspecto)
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def actualizar(self, idProspectos, data):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE PROSPECTOS SET
                    nombre_comercial = COALESCE(%s, nombre_comercial),
                    tipo_local = COALESCE(%s, tipo_local),
                    direccion = COALESCE(%s, direccion),
                    contacto = COALESCE(%s, contacto),
                    telefono = COALESCE(%s, telefono),
                    potencial = COALESCE(%s, potencial),
                    notas = COALESCE(%s, notas),
                    url_foto = COALESCE(%s, url_foto),
                    latitud = COALESCE(%s, latitud),
                    longitud = COALESCE(%s, longitud),
                    idDistrito = COALESCE(%s, idDistrito)
                WHERE idProspectos = %s
            """
            cursor.execute(sql, (
                data.get("nombre_comercial"),
                data.get("tipo_local"),
                data.get("direccion"),
                data.get("contacto"),
                data.get("telefono"),
                data.get("potencial"),
                data.get("notas"),
                data.get("url_foto"),
                data.get("latitud"),
                data.get("longitud"),
                data.get("idDistrito"),
                idProspectos
            ))
            self.connection.commit()
            return self.buscar_por_id(idProspectos)
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def actualizar_estado(self, idProspectos, nuevo_estado, motivo_descarte=None, idUsuarioRevisor=None):
        cursor = self.connection.cursor()
        try:
            fecha_cierre_sql = "NOW()" if nuevo_estado in ("CONVERTIDO", "DESCARTADO") else "NULL"
            sql = f"""
                UPDATE PROSPECTOS SET
                    estado = %s,
                    motivo_descarte = %s,
                    fecha_cierre = {fecha_cierre_sql}
                WHERE idProspectos = %s
            """
            cursor.execute(sql, (nuevo_estado, motivo_descarte, idProspectos))

            punto_venta_creado = None

            # ── SI PASA A CONVERTIDO → CREAR AUTOMÁTICAMENTE EL PUNTO DE VENTA ──
            if nuevo_estado == "CONVERTIDO":
                prospecto = self.buscar_por_id(idProspectos)
                if prospecto:
                    # Generar código único para el punto de venta
                    codigo_pdv = f"DIST-{prospecto['idProspectos']:04d}"

                    # Verificar si ya existe un PDV con este código o para este local
                    cursor.execute(
                        "SELECT idPuntosVenta, codigo FROM PUNTOS_VENTA WHERE codigo = %s OR puntoVenta = %s LIMIT 1",
                        (codigo_pdv, prospecto["nombre_comercial"])
                    )
                    pdv_existente = cursor.fetchone()

                    if not pdv_existente:
                        sql_pdv = """
                            INSERT INTO PUNTOS_VENTA (
                                codigo,
                                puntoVenta,
                                direccion,
                                estado,
                                latitud,
                                longitud,
                                radio_geocerca,
                                tipo,
                                idDistrito,
                                idUsuario
                            ) VALUES (
                                %s, %s, %s, 'ACTIVO', %s, %s, 50.00, 'DISTRIBUCIÓN', %s, %s
                            )
                        """
                        cursor.execute(sql_pdv, (
                            codigo_pdv,
                            prospecto["nombre_comercial"],
                            prospecto["direccion"],
                            prospecto["latitud"],
                            prospecto["longitud"],
                            prospecto["idDistrito"],
                            prospecto["idUsuario"]
                        ))
                        id_nuevo_pdv = cursor.lastrowid

                        # Si el prospecto tenía foto, vincularla al nuevo punto de venta
                        if prospecto.get("url_foto"):
                            try:
                                cursor.execute("UPDATE PUNTOS_VENTA SET url_foto = %s WHERE idPuntosVenta = %s", (prospecto["url_foto"], id_nuevo_pdv))
                            except Exception:
                                pass

                        # Registrar en HISTORIAL_ASIGNACIONES si tiene promotor asignado
                        if prospecto["idUsuario"]:
                            sql_hist = """
                                INSERT INTO HISTORIAL_ASIGNACIONES (
                                    fecha_inicio,
                                    motivo,
                                    idPuntosVenta,
                                    idUsuario,
                                    idUsuarioRegistra
                                ) VALUES (
                                    CURDATE(),
                                    'Conversión automática desde prospecto',
                                    %s,
                                    %s,
                                    %s
                                )
                            """
                            cursor.execute(sql_hist, (
                                id_nuevo_pdv,
                                prospecto["idUsuario"],
                                idUsuarioRevisor or prospecto["idUsuario"]
                            ))

                        punto_venta_creado = {
                            "idPuntosVenta": id_nuevo_pdv,
                            "codigo": codigo_pdv,
                            "puntoVenta": prospecto["nombre_comercial"],
                            "tipo": "DISTRIBUCIÓN",
                            "estado": "ACTIVO"
                        }
                    else:
                        punto_venta_creado = pdv_existente

            self.connection.commit()
            prospecto_actualizado = self.buscar_por_id(idProspectos)
            return prospecto_actualizado, punto_venta_creado

        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def asignar_promotor(self, idProspectos, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE PROSPECTOS SET idUsuario = %s WHERE idProspectos = %s"
            cursor.execute(sql, (idUsuario, idProspectos))
            self.connection.commit()
            return self.buscar_por_id(idProspectos)
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    # ── SEGUIMIENTOS DE PROSPECTOS ──────────────────────────────────────────
    def listar_seguimientos(self, idProspectos):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    sp.idSeguimiento,
                    sp.tipo,
                    sp.comentario,
                    sp.fecha,
                    sp.proxima_accion,
                    sp.fecha_proxima_accion,
                    sp.idProspectos,
                    sp.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS usuario_registra
                FROM SEGUIMIENTOS_PROSPECTO sp
                INNER JOIN USUARIOS u ON sp.idUsuario = u.idUsuario
                WHERE sp.idProspectos = %s
                ORDER BY sp.fecha DESC, sp.idSeguimiento DESC
            """
            cursor.execute(sql, (idProspectos,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def crear_seguimiento(self, idProspectos, idUsuario, tipo, comentario, proxima_accion=None, fecha_proxima_accion=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO SEGUIMIENTOS_PROSPECTO (
                    tipo,
                    comentario,
                    fecha,
                    proxima_accion,
                    fecha_proxima_accion,
                    idProspectos,
                    idUsuario
                ) VALUES (
                    %s, %s, NOW(), %s, %s, %s, %s
                )
            """
            cursor.execute(sql, (
                tipo,
                comentario,
                proxima_accion,
                fecha_proxima_accion,
                idProspectos,
                idUsuario
            ))
            idSeguimiento = cursor.lastrowid
            self.connection.commit()

            cursor.execute("SELECT * FROM SEGUIMIENTOS_PROSPECTO WHERE idSeguimiento = %s", (idSeguimiento,))
            return cursor.fetchone()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
