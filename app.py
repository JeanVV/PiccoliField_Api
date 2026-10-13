from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from utils.json_provider import CustomJSONProvider

from routes.auth_routes import auth_bp
from routes.usuario_routes import usuario_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.json = CustomJSONProvider(app)

    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(usuario_bp)

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