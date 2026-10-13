import hashlib

from flask_jwt_extended import create_access_token

from database import get_connection
from repositories.usuario_repository import UsuarioRepository


class AuthService:
    def login(self, correo, password):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_correo(correo)

            if usuario is None:
                return None, "Correo o contraseña incorrectos", 401

            if usuario["estado"] != "ACTIVO":
                return None, "El usuario se encuentra inactivo", 403

            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if usuario["password_hash"] != password_hash:
                return None, "Correo o contraseña incorrectos", 401

            token = create_access_token(identity=str(usuario["id"]))

            data = {
                "token": token,
                "usuario": {
                    "id": usuario["id"],
                    "correo": usuario["correo"],
                    "usuario": usuario["usuario"],
                    "rol": usuario["rol"]
                }
            }

            return data, "Inicio de sesión exitoso", 200
        finally:
            connection.close()
