import math

class PuntoVentaRepository:
    def __init__(self, connection):
        self.connection = connection

    def listar_todos(self, search=None, distrito=None, estado="ACTIVO"):
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
                    d.distrito,
                    p.provincia,
                    dep.departamento,
                    CONCAT(u.nombres, ' ', u.apePaterno) AS promotor_asignado
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
