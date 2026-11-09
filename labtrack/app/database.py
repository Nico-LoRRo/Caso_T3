import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'labtrack.db')

def get_db(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=None, force=False):
    """Crea las tablas y carga datos semilla si la BD no existe o si force=True"""
    path = db_path or DB_PATH
    
    if force and os.path.exists(path):
        os.remove(path)

    conn = get_db(path)
    cursor = conn.cursor()

    # Tabla Usuarios (HU-01, HU-04, HU-05)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('estudiante', 'encargado')),
        intentos_fallidos INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'Activo' CHECK(estado IN ('Activo', 'Bloqueado', 'Penalizado'))
    );
    """)

    # Tabla Equipos (HU-02, HU-03, HU-04, HU-05)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_inventario TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL CHECK(categoria IN ('Cómputo', 'Electrónica', 'Redes')),
        estado TEXT DEFAULT 'Disponible' CHECK(estado IN ('Disponible', 'Prestado'))
    );
    """)

    # Tabla Reservas (HU-03, HU-04, HU-05)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        equipo_id INTEGER NOT NULL REFERENCES equipos(id) ON DELETE CASCADE,
        fecha TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL,
        estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Aprobada', 'Rechazada', 'Devuelta')),
        motivo_rechazo TEXT,
        fecha_devolucion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Carga de datos semilla si la tabla de usuarios está vacía
    cursor.execute("SELECT COUNT(*) as total FROM usuarios")
    if cursor.fetchone()['total'] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()

    # Usuarios de prueba
    usuarios = [
        # Código, Nombre, Password, Rol, Intentos, Estado
        ('N0001', 'Juan Pérez', generate_password_hash('123456'), 'estudiante', 0, 'Activo'),
        ('N0002', 'María Gómez', generate_password_hash('123456'), 'estudiante', 0, 'Activo'),
        ('N0003', 'Carlos Ruiz', generate_password_hash('123456'), 'estudiante', 0, 'Activo'),
        ('ADM01', 'Prof. Arribasplata (Encargado)', generate_password_hash('admin123'), 'encargado', 0, 'Activo')
    ]
    cursor.executemany("""
    INSERT INTO usuarios (codigo, nombre, password_hash, rol, intentos_fallidos, estado)
    VALUES (?, ?, ?, ?, ?, ?);
    """, usuarios)

    # Catálogo de equipos de prueba
    equipos = [
        # Cómputo
        ('EQ-CMP-01', 'Laptop Dell Precision 3581', 'Cómputo', 'Disponible'),
        ('EQ-CMP-02', 'Laptop Lenovo ThinkPad P14s', 'Cómputo', 'Disponible'),
        ('EQ-CMP-03', 'Estación HP Workstation Z2', 'Cómputo', 'Disponible'),

        # Electrónica
        ('EQ-ELC-01', 'Osciloscopio Digital Tektronix 100MHz', 'Electrónica', 'Disponible'),
        ('EQ-ELC-02', 'Generador de Funciones Rigol DG1022Z', 'Electrónica', 'Disponible'),
        ('EQ-ELC-03', 'Fuente Regulable DC 30V 5A', 'Electrónica', 'Disponible'),

        # Redes
        ('EQ-RED-01', 'Switch Cisco Catalyst 2960-X', 'Redes', 'Disponible'),
        ('EQ-RED-02', 'Router Cisco ISR 4331', 'Redes', 'Disponible'),
        ('EQ-RED-03', 'Punto de Acceso UniFi 6 Pro', 'Redes', 'Disponible')
    ]
    cursor.executemany("""
    INSERT INTO equipos (codigo_inventario, nombre, categoria, estado)
    VALUES (?, ?, ?, ?);
    """, equipos)

    conn.commit()

if __name__ == '__main__':
    print("Inicializando base de datos LabTrack...")
    init_db(force=True)
    print("Base de datos inicializada con éxito en:", DB_PATH)
