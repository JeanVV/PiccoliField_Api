from database import get_connection

class AsistenciaRepository:
    def contar_asistencias_hoy(self, fecha):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT idUsuario) FROM ASISTENCIAS 
            WHERE DATE(fecha_hora_servidor) = %s
        """, (fecha,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else 0
    
    def contar_por_estado(self, fecha, estado):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM ASISTENCIAS 
            WHERE DATE(fecha_hora_servidor) = %s AND estado = %s AND tipo = 'INGRESO'
        """, (fecha, estado))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else 0
    
    def obtener_ultimas(self, limite=10):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.idAsistencias, a.id_turno, a.tipo, a.fecha_hora_servidor,
                   a.fecha_hora_dispositivo, a.estado, a.minutos_tardanza,
                   u.idUsuario, u.nombres, u.apePaterno, u.apeMaterno,
                   u.foto_perfil, s.sede
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
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.idUsuario, u.nombres, u.apePaterno, u.apeMaterno,
                   u.foto_perfil, s.sede,
                   COALESCE((SELECT estado FROM ASISTENCIAS 
                            WHERE idUsuario = u.idUsuario AND tipo = 'INGRESO'
                            ORDER BY fecha_hora_servidor DESC LIMIT 1), 'SIN_REGISTRO') as estado,
                   COALESCE((SELECT fecha_hora_dispositivo FROM ASISTENCIAS 
                            WHERE idUsuario = u.idUsuario AND tipo = 'INGRESO'
                            ORDER BY fecha_hora_servidor DESC LIMIT 1), NULL) as fecha_hora_dispositivo
            FROM USUARIOS u
            INNER JOIN SEDES s ON u.idSede = s.idSede
            WHERE u.estado = 'ACTIVO'
            ORDER BY u.nombres
        """)
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    
    def obtener_detalle_usuario(self, id_usuario):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.idUsuario, u.nombres, u.apePaterno, u.apeMaterno,
                   u.foto_perfil, s.sede, a.estado, a.fecha_hora_dispositivo,
                   a.fecha_hora_servidor, a.minutos_tardanza, a.id_turno
            FROM USUARIOS u
            INNER JOIN SEDES s ON u.idSede = s.idSede
            LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario
            WHERE u.idUsuario = %s AND a.tipo = 'INGRESO'
            ORDER BY a.fecha_hora_servidor DESC LIMIT 1
        """, (id_usuario,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado
    
    def obtener_historial_turnos(self, id_usuario):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_turno, tipo, fecha_hora_dispositivo as fecha_hora, idUsuario
            FROM ASISTENCIAS
            WHERE idUsuario = %s
            ORDER BY fecha_hora_servidor DESC
        """, (id_usuario,))
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    
    def obtener_evidencias(self, id_asistencia):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT idEvidencias, ruta_archivo, hash_sha, tipo, fecha_captura
            FROM EVIDENCIAS
            WHERE idAsistencia = %s
        """, (id_asistencia,))
        resultados = cursor.fetchall()
        conn.close()
        return resultados