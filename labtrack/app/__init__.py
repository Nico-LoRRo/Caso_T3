import os
from flask import Flask
from .database import init_db, DB_PATH

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'labtrack_secret_key_2026_semana13'
    app.config['DATABASE'] = DB_PATH

    # Inicializar BD automáticamente si no existe
    init_db()

    # Registrar rutas y controladores
    from .routes import main_bp
    app.register_blueprint(main_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'message': 'LabTrack base activa'}

    return app
