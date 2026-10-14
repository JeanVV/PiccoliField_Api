from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from utils.json_provider import CustomJSONProvider
from routes.asistencia_routes import asistencia_bp
from routes.auth_routes import auth_bp
from routes.usuario_routes import usuario_bp
from routes.punto_venta_routes import punto_venta_bp
from routes.pedido_routes import pedido_bp
from routes.control_routes import control_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.json = CustomJSONProvider(app)

    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(asistencia_bp)
    app.register_blueprint(punto_venta_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(control_bp)

    @app.get("/")
    def inicio():
        return {
            "data": {
                "app": "PiccoliField API REST"
            },
            "message": "API disponible",
            "status": True
        }, 200
    return app

app = create_app()

if __name__ == "__main__":
        app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )