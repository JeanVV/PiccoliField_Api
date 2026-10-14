from database import get_connection

class AsistenciaRepository:
    def contar_asistencias_hoy(self, fecha):
        """Cuenta total de asistencias esperadas para hoy"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT idUsuario) 
            FROM ASISTENCIAS 
            WHERE DATE(fecha_hora_servidor) = %s
        """, (fecha,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else 0
    
    def contar_por_estado(self, fecha, estado):
        """Cuenta asistencias por estado (A_TIEMPO, TARDANZA, FALTA)"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ASISTENCIAS 
            WHERE DATE(fecha_hora_servidor) = %s 
            AND estado = %s
            AND tipo = 'INGRESO'
        """, (fecha, estado))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else 0
    
    def obtener_ultimas(self, limite=10):
        """Obtiene las últimas asistencias con datos del usuario"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.idAsistencias,
                a.idUsuario,
                u.nombres,
                u.apePaterno,
                u.foto_perfil,
                s.sede,
                a.estado,
                a.fecha_hora_dispositivo,
                a.fecha_hora_servidor
            FROM ASISTENCIAS a
            INNER JOIN USUARIOS u ON a.idUsuario = u.idUsuario
            INNER JOIN SEDES s ON u.idSede = s.idSede
            WHERE a.tipo = 'INGRESO'
            ORDER BY a.fecha_hora_servidor DESC
            LIMIT %s
        """, (limite,))
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    
    def obtener_colaboradores_con_ultimo_registro(self):
        """Obtiene todos los colaboradores activos con su último registro"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                u.idUsuario,
                u.nombres,
                u.apePaterno,
                u.foto_perfil,
                s.sede,
                COALESCE(
                    (SELECT estado 
                     FROM ASISTENCIAS 
                     WHERE idUsuario = u.idUsuario AND tipo = 'INGRESO'
                     ORDER BY fecha_hora_servidor DESC LIMIT 1),
                    'SIN_REGISTRO'
                ) as estado,
                COALESCE(
                    (SELECT fecha_hora_dispositivo 
                     FROM ASISTENCIAS 
                     WHERE idUsuario = u.idUsuario AND tipo = 'INGRESO'
                     ORDER BY fecha_hora_servidor DESC LIMIT 1),
                    NULL
                ) as fecha_hora_dispositivo
            FROM USUARIOS u
            INNER JOIN SEDES s ON u.idSede = s.idSede
            WHERE u.estado = 'ACTIVO'
            ORDER BY u.nombres
        """)
        resultados = cursor.fetchall()
        conn.close()
        return resultados