class PuntoVentaRepository:
    def __init__(self, connection):
        self.connection = connection

    def listar_todos(self, search=None, distrito=None, estado="ACTIVO", tipo=None, idUsuario=None):
        cursor = self.connection.cursor()
        try:
            sql = """
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
                    p.provincia,
                    dep.departamento,
                    pv.idUsuario AS idResponsable,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado,
                    u.correo AS correo_responsable,
                    u.rol AS rol_responsable
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE 1=1
            """
            params = []

            if estado:
                sql += " AND pv.estado = %s"
                params.append(estado)

            if tipo:
                if tipo.upper() in ("DISTRIBUCION", "DISTRIBUCIÓN"):
                    sql += " AND pv.tipo IN ('DISTRIBUCION', 'DISTRIBUCIÓN')"
                else:
                    sql += " AND pv.tipo = %s"
                    params.append(tipo.upper())

            if idUsuario is not None:
                sql += " AND pv.idUsuario = %s"
                params.append(idUsuario)

            if distrito:
                sql += " AND (pv.idDistrito = %s OR d.distrito LIKE %s)"
                params.append(distrito)
                params.append(f"%{distrito}%")

            if search:
                sql += " AND (pv.puntoVenta LIKE %s OR pv.direccion LIKE %s OR pv.codigo LIKE %s)"
                term = f"%{search}%"
                params.extend([term, term, term])

            sql += " ORDER BY pv.idPuntosVenta DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def buscar_por_id(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
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
                    p.provincia,
                    dep.departamento,
                    pv.idUsuario AS idResponsable,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado,
                    u.correo AS correo_responsable,
                    u.rol AS rol_responsable
                FROM PUNTOS_VENTA pv
                INNER JOIN DISTRITO d ON pv.idDistrito = d.idDistrito
                INNER JOIN PROVINCIA p ON d.idProvincia = p.idProvincia
                INNER JOIN DEPARTAMENTO dep ON p.idDepartamento = dep.idDepartamento
                LEFT JOIN USUARIOS u ON pv.idUsuario = u.idUsuario
                WHERE pv.idPuntosVenta = %s
                LIMIT 1
            """
            cursor.execute(sql, (idPuntosVenta,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def asignar_responsable(self, idPuntosVenta, idUsuarioNuevo, idUsuarioRegistra, motivo=None):
        cursor = self.connection.cursor()
        try:
            # 1. Validar PDV
            cursor.execute(
                "SELECT idPuntosVenta, puntoVenta, estado, tipo, idUsuario FROM PUNTOS_VENTA WHERE idPuntosVenta = %s",
                (idPuntosVenta,)
            )
            pdv = cursor.fetchone()
            if not pdv:
                return None, "Punto de venta no encontrado", 404

            # 2. Validar nuevo usuario
            cursor.execute(
                "SELECT idUsuario, CONCAT(nombres, ' ', apePaterno) AS nombre, rol, estado FROM USUARIOS WHERE idUsuario = %s",
                (idUsuarioNuevo,)
            )
            nuevo_user = cursor.fetchone()
            if not nuevo_user:
                return None, "Usuario responsable no encontrado", 404

            if nuevo_user["estado"] != "ACTIVO":
                return None, "El usuario a asignar no se encuentra ACTIVO", 422

            # En distribución debe ser Promotor (o Administrador)
            tipo_pdv = str(pdv.get("tipo", "")).upper()
            if tipo_pdv in ("DISTRIBUCION", "DISTRIBUCIÓN") and nuevo_user["rol"] not in ("PROMOTOR", "ADMINISTRADOR"):
                return None, f"Para un punto de DISTRIBUCIÓN el responsable debe tener rol PROMOTOR (rol actual: {nuevo_user['rol']})", 422

            if pdv.get("idUsuario") == idUsuarioNuevo:
                return None, f"{nuevo_user['nombre']} ya se encuentra asignado a este punto de venta", 422

            # 3. Transacción: cerrar asignación anterior y registrar la nueva
            cursor.execute("""
                UPDATE HISTORIAL_ASIGNACIONES
                SET fecha_fin = CURDATE()
                WHERE idPuntosVenta = %s AND fecha_fin IS NULL
            """, (idPuntosVenta,))

            cursor.execute("""
                UPDATE PUNTOS_VENTA
                SET idUsuario = %s
                WHERE idPuntosVenta = %s
            """, (idUsuarioNuevo, idPuntosVenta))

            cursor.execute("""
                INSERT INTO HISTORIAL_ASIGNACIONES (
                    fecha_inicio,
                    motivo,
                    idPuntosVenta,
                    idUsuario,
                    idUsuarioRegistra
                ) VALUES (
                    CURDATE(),
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (motivo or "Asignación de responsable", idPuntosVenta, idUsuarioNuevo, idUsuarioRegistra))

            self.connection.commit()
            pdv_actualizado = self.buscar_por_id(idPuntosVenta)
            return pdv_actualizado, "Responsable asignado correctamente", 200

        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def obtener_historial_asignaciones(self, idPuntosVenta):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    ha.idHistorial,
                    ha.fecha_inicio,
                    ha.fecha_fin,
                    ha.motivo,
                    ha.idUsuario,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS nombre_responsable,
                    u.rol AS rol_responsable,
                    ha.idUsuarioRegistra,
                    CONCAT(ur.nombres, ' ', ur.apePaterno) AS asignado_por
                FROM HISTORIAL_ASIGNACIONES ha
                INNER JOIN USUARIOS u ON ha.idUsuario = u.idUsuario
                LEFT JOIN USUARIOS ur ON ha.idUsuarioRegistra = ur.idUsuario
                WHERE ha.idPuntosVenta = %s
                ORDER BY ha.fecha_inicio DESC, ha.idHistorial DESC
            """
            cursor.execute(sql, (idPuntosVenta,))
            return cursor.fetchall()
        finally:
            cursor.close()
