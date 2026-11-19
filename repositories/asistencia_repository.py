from datetime import datetime, timedelta, timezone

try:
    import pytz
    peru_tz = pytz.timezone('America/Lima')
except ImportError:
    peru_tz = timezone(timedelta(hours=-5))

def get_now_peru():
    return datetime.now(peru_tz)

class AsistenciaRepository:
    def __init__(self, connection):
        self.connection = connection

    # ── 1. RESUMEN DEL DÍA ───────────────────────────────────────────────────
    def get_resumen(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    COUNT(u.idUsuario) AS total,
                    COALESCE(SUM(CASE WHEN a.estado IN ('A_TIEMPO', 'TARDANZA') THEN 1 ELSE 0 END), 0) AS presentes,
                    COALESCE(SUM(CASE WHEN a.estado = 'A_TIEMPO' THEN 1 ELSE 0 END), 0) AS aTiempo,
                    COALESCE(SUM(CASE WHEN a.estado = 'TARDANZA' THEN 1 ELSE 0 END), 0) AS tardanzas,
                    COALESCE(SUM(CASE WHEN a.estado = 'FALTA' THEN 1 ELSE 0 END), 0) AS faltas,
                    COALESCE(SUM(CASE WHEN a.idAsistencias IS NULL THEN 1 ELSE 0 END), 0) AS sinMarcar
                FROM USUARIOS u
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE()
                    AND a.tipo = 'INGRESO'
                WHERE u.estado = 'ACTIVO' AND u.rol NOT IN ('ADMINISTRADOR', 'SUPERVISOR')
            """
            cursor.execute(sql)
            resumen = cursor.fetchone() or {}
            total = resumen.get('total', 0)
            presentes = resumen.get('presentes', 0)
            resumen['porcentaje'] = int((presentes / total * 100)) if total > 0 else 0
            return resumen
        finally:
            cursor.close()

    # ── 2. ASISTENCIAS RECIENTES ─────────────────────────────────────────────
    def get_recientes(self, limite=10):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    a.idAsistencias,
                    a.idAsistencias AS id_turno,
                    a.tipo,
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.url_foto AS foto_perfil,
                    s.sede,
                    a.estado,
                    DATE_FORMAT(a.fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_dispositivo,
                    DATE_FORMAT(a.fecha_hora_servidor, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_servidor,
                    a.minutos_tardanza,
                    a.latitud,
                    a.longitud
                FROM ASISTENCIAS a
                INNER JOIN USUARIOS u ON a.idUsuario = u.idUsuario
                INNER JOIN SEDES s ON u.idSede = s.idSede
                WHERE DATE(a.fecha_hora_servidor) = CURDATE()
                ORDER BY a.fecha_hora_servidor DESC
                LIMIT %s
            """
            cursor.execute(sql, (limite,))
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 3. LISTA DE COLABORADORES CON ESTADO Y JUSTIFICACIÓN ─────────────────
    def get_colaboradores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.idUsuario,
                    u.nombres,
                    u.apePaterno,
                    u.apeMaterno,
                    u.url_foto AS foto_perfil,
                    s.sede,
                    a.idAsistencias,
                    COALESCE(a.estado, 'SIN_REGISTRO') AS estado,
                    DATE_FORMAT(a.fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora_dispositivo,
                    COALESCE(a.minutos_tardanza, 0) AS minutos_tardanza,
                    a.latitud,
                    a.longitud,
                    j.motivo AS motivoJustificacion,
                    j.descripcion AS justificacion,
                    j.estado AS estadoJustificacion
                FROM USUARIOS u
                INNER JOIN SEDES s ON u.idSede = s.idSede
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE() 
                    AND a.tipo = 'INGRESO'
                LEFT JOIN JUSTIFICACIONES j ON a.idAsistencias = j.idAsistencias
                WHERE u.estado = 'ACTIVO' AND u.rol != 'ADMINISTRADOR'
                ORDER BY a.fecha_hora_servidor DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 4. HISTORIAL DE TURNOS DE UN USUARIO ─────────────────────────────────
    def get_historial(self, idUsuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    idAsistencias AS id_turno,
                    tipo,
                    DATE_FORMAT(fecha_hora_dispositivo, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_hora,
                    idUsuario
                FROM ASISTENCIAS
                WHERE idUsuario = %s
                ORDER BY fecha_hora_dispositivo DESC
            """
            cursor.execute(sql, (idUsuario,))
            return cursor.fetchall()
        finally:
            cursor.close()

    # ── 5. MARCAR ASISTENCIA (INGRESO / SALIDA) ──────────────────────────────
    def marcar_asistencia(self, id_usuario, tipo, latitud=None, longitud=None, direccion=None, sede=None, fecha_hora_disp=None, **kwargs):
        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()

        try:
            tipo_upper = "SALIDA" if str(tipo).upper() == "SALIDA" else "INGRESO"
            id_user = int(id_usuario) if id_usuario else 1

            # 1. Asegurar idUsuario existente en la tabla USUARIOS
            cursor.execute("SELECT idUsuario FROM USUARIOS WHERE idUsuario = %s LIMIT 1", (id_user,))
            row = cursor.fetchone()
            if not row:
                cursor.execute("SELECT idUsuario FROM USUARIOS LIMIT 1")
                row_first = cursor.fetchone()
                if row_first:
                    id_user = row_first['idUsuario'] if isinstance(row_first, dict) else row_first[0]

            # 2. Control de duplicados el mismo día para INGRESO
            if tipo_upper == 'INGRESO':
                sql_check = """
                    SELECT idAsistencias, DATE_FORMAT(fecha_hora_servidor, '%%H:%%i:%%s') AS hora, estado
                    FROM ASISTENCIAS
                    WHERE idUsuario = %s AND tipo = 'INGRESO' AND DATE(fecha_hora_servidor) = CURDATE()
                    LIMIT 1
                """
                cursor.execute(sql_check, (id_user,))
                existente = cursor.fetchone()
                if existente:
                    if isinstance(existente, dict):
                        id_asist = existente.get('idAsistencias')
                        hora_str = existente.get('hora') or ""
                        est_str = existente.get('estado') or 'A_TIEMPO'
                    else:
                        id_asist = existente[0]
                        hora_str = str(existente[1]) if len(existente) > 1 and existente[1] else ""
                        est_str = str(existente[2]) if len(existente) > 2 and existente[2] else 'A_TIEMPO'

                    return {
                        "idAsistencias": id_asist,
                        "tipo": "INGRESO",
                        "estado": est_str,
                        "minutosTardanza": 0,
                        "yaRegistrado": True,
                        "mensaje": f"Ya has registrado tu ingreso hoy a las {hora_str}",
                        "message": f"Ya has registrado tu ingreso hoy a las {hora_str}"
                    }

            # 3. INSERT a la tabla ASISTENCIAS
            try:
                lat_val = float(latitud) if latitud is not None and str(latitud).strip() not in ("", "null", "None") else -6.7711982
            except (ValueError, TypeError):
                lat_val = -6.7711982

            try:
                lng_val = float(longitud) if longitud is not None and str(longitud).strip() not in ("", "null", "None") else -79.8385571
            except (ValueError, TypeError):
                lng_val = -79.8385571

            obs = f"Sede: {sede or 'Chiclayo'} - Dir: {direccion or 'N/A'}"

            sql = """
                INSERT INTO ASISTENCIAS (
                    tipo, fecha_hora_servidor, fecha_hora_dispositivo, estado,
                    minutos_tardanza, latitud, longitud, radio, precision_m,
                    marcacion_observada, observacion, idUsuario
                ) VALUES (
                    %s, NOW(), NOW(), 'A_TIEMPO',
                    0, %s, %s, 100.0, 5.0,
                    0, %s, %s
                )
            """
            cursor.execute(sql, (tipo_upper, lat_val, lng_val, obs, id_user))
            self.connection.commit()

            id_nuevo = cursor.lastrowid
            return {
                "idAsistencias": id_nuevo,
                "tipo": tipo_upper,
                "estado": "A_TIEMPO",
                "minutosTardanza": 0,
                "yaRegistrado": False,
                "mensaje": "Asistencia registrada correctamente",
                "message": "Asistencia registrada correctamente"
            }
        except Exception as e:
            self.connection.rollback()
            print(f"[ERROR ABSOLUTO MARCAR]: {type(e).__name__} - {str(e)}")
            raise e
        finally:
            cursor.close()

    # ── 6. REGISTRAR JUSTIFICACIÓN ───────────────────────────────────────────
    def registrar_justificacion(self, id_usuario, motivo, descripcion, fecha, ruta_sustento=None):
        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()
        try:
            id_user = int(id_usuario) if id_usuario else 1
            fecha_str = str(fecha).split(" ")[0] if fecha else get_now_peru().strftime("%Y-%m-%d")

            # 1. Asegurar que exista un idAsistencias para la fecha indicada
            sql_check = """
                SELECT idAsistencias FROM ASISTENCIAS 
                WHERE idUsuario = %s AND (DATE(fecha_hora_servidor) = %s OR DATE(fecha_hora_dispositivo) = %s)
                ORDER BY idAsistencias DESC LIMIT 1
            """
            cursor.execute(sql_check, (id_user, fecha_str, fecha_str))
            asistencia = cursor.fetchone()

            if asistencia:
                id_asistencia = asistencia['idAsistencias'] if isinstance(asistencia, dict) else asistencia[0]
            else:
                fecha_disp = f"{fecha_str} 09:00:00"
                sql_insert_asistencia = """
                    INSERT INTO ASISTENCIAS (
                        idUsuario, tipo, estado, fecha_hora_servidor, fecha_hora_dispositivo, observacion
                    ) VALUES (
                        %s, 'INGRESO', 'FALTA', NOW(), %s, 'Inasistencia con justificación'
                    )
                """
                cursor.execute(sql_insert_asistencia, (id_user, fecha_disp))
                id_asistencia = cursor.lastrowid

            # 2. INSERT ultra simple a la tabla JUSTIFICACIONES (100% fiel a piccoliFieldSql.txt)
            ruta_final = ruta_sustento
            if ruta_final and len(str(ruta_final)) > 255:
                try:
                    from services.asistencia_service import guardar_foto_sustento
                    ruta_final = guardar_foto_sustento(ruta_final, id_user) or ""
                except Exception:
                    ruta_final = str(ruta_final)[:255]

            sql_justificacion = """
                INSERT INTO JUSTIFICACIONES (
                    idAsistencias, idUsuario, motivo, descripcion, estado, ruta_sustento, fecha_registro
                ) VALUES (
                    %s, %s, %s, %s, 'PENDIENTE', %s, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    motivo = VALUES(motivo),
                    descripcion = VALUES(descripcion),
                    ruta_sustento = VALUES(ruta_sustento),
                    estado = 'PENDIENTE',
                    fecha_registro = NOW()
            """
            cursor.execute(sql_justificacion, (id_asistencia, id_user, str(motivo), str(descripcion), ruta_final))
            self.connection.commit()

            id_justificacion = cursor.lastrowid
            if not id_justificacion:
                cursor.execute("SELECT idJustificacion FROM JUSTIFICACIONES WHERE idAsistencias = %s LIMIT 1", (id_asistencia,))
                row_j = cursor.fetchone()
                id_justificacion = row_j["idJustificacion"] if isinstance(row_j, dict) else row_j[0]

            return {
                "idJustificacion": id_justificacion,
                "idAsistencias": id_asistencia,
                "idUsuario": id_user,
                "estado": "PENDIENTE",
                "mensaje": "Justificación registrada exitosamente",
                "message": "Justificación registrada exitosamente"
            }
        except Exception as e:
            self.connection.rollback()
            print(f"[ERROR registrar_justificacion]: {type(e).__name__} - {str(e)}")
            raise e
        finally:
            cursor.close()

    # ── 7. OBTENER ÚLTIMA JUSTIFICACIÓN DE UN USUARIO ────────────────────────
    def get_justificacion_usuario(self, id_usuario):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    j.idJustificacion,
                    j.motivo,
                    j.motivo AS motivoJustificacion,
                    j.descripcion,
                    j.descripcion AS justificacion,
                    j.estado,
                    j.estado AS estadoJustificacion,
                    DATE_FORMAT(j.fecha_registro, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_registro,
                    DATE_FORMAT(j.fecha_registro, '%%Y-%%m-%%d %%H:%%i:%%s') AS fechaJustificacion,
                    j.idAsistencias,
                    j.idUsuario
                FROM JUSTIFICACIONES j
                WHERE j.idUsuario = %s
                ORDER BY j.fecha_registro DESC
                LIMIT 1
            """
            cursor.execute(sql, (id_usuario,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def _parse_datetime(self, valor_str):
        if not valor_str:
            return get_now_peru()
        for formato in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(str(valor_str).strip(), formato)
            except ValueError:
                pass
        return get_now_peru()


    # ── 8. OBTENER ÚLTIMA ASISTENCIA DEL USUARIO ─────────────────────────────
    def obtener_ultima_asistencia(self, id_usuario):
        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()
        try:
            query = """
                SELECT 
                    idAsistencias AS id,
                    DATE_FORMAT(fecha_hora_servidor, '%%Y-%%m-%%d') AS fecha,
                    DATE_FORMAT(fecha_hora_servidor, '%%H:%%i:%%s') AS hora,
                    tipo,
                    estado,
                    latitud,
                    longitud,
                    observacion AS direccion
                FROM ASISTENCIAS
                WHERE idUsuario = %s
                ORDER BY idAsistencias DESC
                LIMIT 1
            """
            cursor.execute(query, (id_usuario,))
            resultado = cursor.fetchone()
            
            # Convertir Decimal de MySQL a float para evitar error de serialización JSON
            if resultado:
                if isinstance(resultado, dict):
                    if resultado.get('latitud') is not None:
                        resultado['latitud'] = float(resultado['latitud'])
                    if resultado.get('longitud') is not None:
                        resultado['longitud'] = float(resultado['longitud'])
                else:
                    resultado = {
                        "id": resultado[0],
                        "fecha": resultado[1],
                        "hora": resultado[2],
                        "tipo": resultado[3],
                        "estado": resultado[4],
                        "latitud": float(resultado[5]) if resultado[5] is not None else None,
                        "longitud": float(resultado[6]) if resultado[6] is not None else None,
                        "direccion": resultado[7]
                    }
            
            return resultado
        finally:
            cursor.close()

    # ── 9. REVISAR (APROBAR/RECHAZAR) JUSTIFICACIÓN COMO ADMINISTRADOR ───────
    def revisar_justificacion(self, id_usuario=None, id_revisor=1, estado="APROBADA", comentario="", id_asistencias=None, **kwargs):
        id_user = id_usuario if id_usuario is not None else kwargs.get("id_usuario_colaborador")
        id_asist = id_asistencias if id_asistencias is not None else kwargs.get("idAsistencias")
        est = estado if estado is not None else kwargs.get("estado_nuevo", "APROBADA")
        com = comentario if comentario is not None else kwargs.get("comentario_admin", "")
        rev = id_revisor if id_revisor is not None else kwargs.get("id_revisor", 1)

        estado_enum = "APROBADA" if str(est).upper() in ["APROBADA", "APROBADO"] else "RECHAZADA"

        try:
            cursor = self.connection.cursor(dictionary=True)
        except TypeError:
            cursor = self.connection.cursor()
        try:
            # 1. Ubicar la justificación a actualizar por idAsistencias o idUsuario
            sql_get = """
                SELECT j.idJustificacion, j.idAsistencias
                FROM JUSTIFICACIONES j
                WHERE (%s IS NOT NULL AND j.idAsistencias = %s)
                   OR (%s IS NOT NULL AND j.idUsuario = %s)
                ORDER BY j.idJustificacion DESC LIMIT 1
            """
            cursor.execute(sql_get, (id_asist, id_asist, id_user, id_user))
            row = cursor.fetchone()

            if not row:
                return False

            id_justificacion = row["idJustificacion"] if isinstance(row, dict) else row[0]
            id_asistencia = row["idAsistencias"] if isinstance(row, dict) else row[1]

            # 2. Actualizar estado de la JUSTIFICACIÓN
            sql_update_j = """
                UPDATE JUSTIFICACIONES
                SET estado = %s, comentario_revision = %s, idRevisor = %s, fecha_revision = NOW()
                WHERE idJustificacion = %s
            """
            cursor.execute(sql_update_j, (estado_enum, com, rev, id_justificacion))

            # 3. Si fue APROBADA, actualizar el estado de la ASISTENCIA a 'A_TIEMPO'
            if estado_enum == "APROBADA":
                cursor.execute("""
                    UPDATE ASISTENCIAS
                    SET estado = 'A_TIEMPO', observacion = CONCAT('Justificación Aprobada: ', COALESCE(%s, ''))
                    WHERE idAsistencias = %s
                """, (com, id_asistencia))

            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            print(f"[ERROR revisar_justificacion]: {str(e)}")
            raise e
        finally:
            cursor.close()

    # ── 10. CONSULTA RESUMEN DE ASISTENCIAS DEL DÍA (10:30 AM) ───────────────
    def get_resumen_diario(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    COUNT(u.idUsuario) AS total,
                    COALESCE(SUM(CASE WHEN a.estado IN ('A_TIEMPO', 'TARDANZA') THEN 1 ELSE 0 END), 0) AS presentes,
                    COALESCE(SUM(CASE WHEN a.estado = 'A_TIEMPO' THEN 1 ELSE 0 END), 0) AS aTiempo,
                    COALESCE(SUM(CASE WHEN a.estado = 'TARDANZA' THEN 1 ELSE 0 END), 0) AS tardanzas,
                    COALESCE(SUM(CASE WHEN a.estado = 'FALTA' OR a.idAsistencias IS NULL THEN 1 ELSE 0 END), 0) AS faltas
                FROM USUARIOS u
                LEFT JOIN ASISTENCIAS a ON u.idUsuario = a.idUsuario 
                    AND DATE(a.fecha_hora_servidor) = CURDATE()
                    AND a.tipo = 'INGRESO'
                WHERE u.estado = 'ACTIVO' AND u.rol NOT IN ('ADMINISTRADOR', 'SUPERVISOR');
            """
            cursor.execute(sql)
            return cursor.fetchone()
        finally:
            cursor.close()

    # ── 11. TOKENS FCM DE ADMINISTRADORES Y SUPERVISORES ─────────────────────
    def get_tokens_administradores_supervisores(self):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT DISTINCT 
                    ud.fcm_token,
                    ud.idUsuario,
                    u.rol,
                    u.nombres,
                    u.apePaterno
                FROM USUARIO_DISPOSITIVO ud
                INNER JOIN USUARIOS u ON ud.idUsuario = u.idUsuario
                WHERE u.rol IN ('ADMINISTRADOR', 'SUPERVISOR')
                  AND ud.activo = 1
                  AND ud.fcm_token IS NOT NULL 
                  AND ud.fcm_token != ''
                  AND u.estado = 'ACTIVO';
            """
            cursor.execute(sql)
            return cursor.fetchall() or []
        finally:
            cursor.close()
