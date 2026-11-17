import os
import time
import threading
from datetime import datetime, timedelta

_scheduler_instancia = None
_scheduler_lock = threading.Lock()


def ejecutar_job_resumen_diario():
    """
    Ejecuta el envío de la notificación de resumen diario de asistencias a las 10:30 AM.
    """
    ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[SCHEDULER {ahora_str}] Iniciando ejecución programada de Resumen Diario de Asistencias (10:30 AM)...")
    try:
        from services.asistencia_service import enviar_notificacion_resumen_diario
        resultado, mensaje, codigo = enviar_notificacion_resumen_diario()
        print(f"[SCHEDULER {ahora_str}] Resumen Diario completado con código {codigo}: {mensaje}")
        return resultado
    except Exception as e:
        print(f"[SCHEDULER {ahora_str}] Error ejecutando Resumen Diario: {e}")
        return None


def _fallback_loop():
    """
    Hilo de respaldo que duerme hasta las 10:30:00 AM cada día
    cuando APScheduler no está instalado o no se encuentra disponible.
    """
    print("[SCHEDULER Fallback] Hilo en segundo plano activado para disparar a las 10:30 AM.")
    while True:
        try:
            ahora = datetime.now()
            # Hora objetivo de hoy a las 10:30:00
            objetivo = ahora.replace(hour=10, minute=30, second=0, microsecond=0)
            if ahora >= objetivo:
                # Ya pasaron las 10:30 de hoy, programar para mañana a las 10:30
                objetivo += timedelta(days=1)

            segundos_espera = (objetivo - ahora).total_seconds()
            print(f"[SCHEDULER Fallback] Próxima ejecución a las: {objetivo.strftime('%Y-%m-%d %H:%M:%S')} (esperando {segundos_espera:.1f} segundos)")

            time.sleep(segundos_espera)
            ejecutar_job_resumen_diario()

            # Dormir 2 segundos adicionales para no reingresar en el mismo segundo
            time.sleep(2)
        except Exception as e:
            print(f"[SCHEDULER Fallback] Error en bucle: {e}")
            time.sleep(60)


def iniciar_scheduler(app=None):
    """
    Inicializa el planificador de tareas programadas (APScheduler o fallback con Thread).
    Configura la ejecución diaria a las 10:30:00 AM.
    """
    global _scheduler_instancia

    with _scheduler_lock:
        if _scheduler_instancia is not None:
            return

        # Evitar duplicar tareas cuando Flask se ejecuta con el reloader en modo debug
        if app and app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            return

        # Intentar inicializar con APScheduler si está instalado
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger

            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(
                func=ejecutar_job_resumen_diario,
                trigger=CronTrigger(hour=10, minute=30, second=0),
                id="resumen_diario_asistencias_1030",
                name="Resumen Diario de Asistencias (10:30 AM)",
                replace_existing=True,
                misfire_grace_time=3600,
            )
            scheduler.start()
            _scheduler_instancia = scheduler
            print("[SCHEDULER] APScheduler iniciado exitosamente. Tarea programada a las 10:30:00 AM todos los días.")
            return scheduler
        except ImportError:
            print("[SCHEDULER] APScheduler no encontrado en el entorno. Utilizando planificador nativo en segundo plano.")
        except Exception as ex:
            print(f"[SCHEDULER] Error al iniciar APScheduler ({ex}). Utilizando planificador nativo en segundo plano.")

        # Fallback autónomo en caso de no tener APScheduler
        t = threading.Thread(target=_fallback_loop, daemon=True, name="CronResumenDiario1030")
        t.start()
        _scheduler_instancia = t
        print("[SCHEDULER] Planificador nativo iniciado a las 10:30:00 AM todos los días.")
        return _scheduler_instancia

