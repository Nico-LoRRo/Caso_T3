import os
import secrets
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .database import init_db, DB_PATH

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Mitigación de credencial fija: obtener de variable de entorno o generar dinámicamente
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)
    app.config['SECRET_KEY'] = secret_key
    app.config['DATABASE'] = DB_PATH

    # Habilitar protección CSRF
    csrf.init_app(app)

    # Inicializar BD automáticamente si no existe
    init_db()

    # Registrar rutas y controladores
    from .routes import main_bp
    app.register_blueprint(main_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'LabTrack base activa'}

    return app
