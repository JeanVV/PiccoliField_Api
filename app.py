from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from utils.json_provider import CustomJSONProvider
from routes.asistencia_routes import asistencia_bp
from routes.auth_routes import auth_bp
from routes.usuario_routes import usuario_bp
from routes.punto_venta_routes import punto_venta_bp
from routes.supervision_routes import supervision_bp
from routes.impulsador_routes import impulsador_bp
from routes.dispositivo_routes import dispositivo_bp
from routes.pedido_routes import pedido_bp
from routes.producto_routes import producto_bp
from routes.prospecto_routes import prospecto_bp
from utils.scheduler import iniciar_scheduler


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.json = CustomJSONProvider(app)

    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(asistencia_bp)
    app.register_blueprint(punto_venta_bp)
    app.register_blueprint(supervision_bp)
    app.register_blueprint(impulsador_bp)
    app.register_blueprint(dispositivo_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(producto_bp)
    app.register_blueprint(prospecto_bp)

    # Asegurar existencia de carpetas en uploads/
    import os
    from flask import send_from_directory
    from config import BASE_DIR

    UPLOADS_ROOT = os.path.join(BASE_DIR, "uploads")
    for sub in ["evidencias", "justificaciones", "perfiles", "productos", "prospectos", "puntos_venta"]:
        os.makedirs(os.path.join(UPLOADS_ROOT, sub), exist_ok=True)

    @app.get("/")
    def inicio():
        return {
            "data": {"app": "PiccoliField API REST"},
            "message": "API disponible",
            "status": True,
        }, 200

    @app.route("/uploads/<path:filename>", methods=["GET"])
    @app.route("/api/uploads/<path:filename>", methods=["GET"])
    def servir_archivo(filename):
        # 1. Normalizar si el cliente envía 'uploads/' en la ruta solicitada
        clean_name = filename.replace("\\", "/").strip("/")
        if clean_name.lower().startswith("uploads/"):
            clean_name = clean_name[len("uploads/"):].strip("/")

        full_path = os.path.join(UPLOADS_ROOT, clean_name)

        # 2. Si no existe exactamente, verificar extensiones de imagen (.jpg, .jpeg, .png, .webp)
        if not os.path.isfile(full_path):
            for ext in [".jpg", ".jpeg", ".png", ".webp", ".JPG", ".PNG"]:
                if os.path.isfile(full_path + ext):
                    clean_name = clean_name + ext
                    full_path = full_path + ext
                    break

        if not os.path.isfile(full_path):
            return {
                "data": None,
                "message": f"Archivo '{filename}' no encontrado en el servidor",
                "status": False
            }, 404

        rel_dir = os.path.dirname(clean_name)
        file_basename = os.path.basename(clean_name)
        target_dir = os.path.join(UPLOADS_ROOT, rel_dir) if rel_dir else UPLOADS_ROOT
        return send_from_directory(target_dir, file_basename)

    iniciar_scheduler(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
