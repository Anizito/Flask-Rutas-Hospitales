from flask import Flask

def create_app():
    app = Flask(__name__)

    # Configuración inicial
    app.config.from_object('config')

    # Registrar las rutas
    from .routes import main
    app.register_blueprint(main)

    return app