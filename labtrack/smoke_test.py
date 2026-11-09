import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import init_db, get_db

def run_smoke_test():
    print("=================================================================")
    print("       INICIANDO SMOKE TEST INTEGRAL - LABTRACK (HU-01 a HU-05)  ")
    print("=================================================================\n")

    # 0. Base de datos limpia
    init_db(force=True)
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    # -------------------------------------------------------------
    # PASO 1: Validar HU-01 (Autenticación y Bloqueo de 3 intentos)
    # -------------------------------------------------------------
    print("[PASO 1] Probando HU-01: Autenticación Segura y Bloqueo por Fuerza Bruta...")
    # Intento 1
    r = client.post('/login', data={'codigo': 'N0001', 'password': 'mala'}, follow_redirects=True)
    assert b'Credenciales' in r.data, "No mostró 'Credenciales inválidas' en intento 1"
    
    # Intento 2
    r = client.post('/login', data={'codigo': 'N0001', 'password': 'mala'}, follow_redirects=True)
    assert b'Credenciales' in r.data, "No mostró 'Credenciales inválidas' en intento 2"

    # Intento 3
    r = client.post('/login', data={'codigo': 'N0001', 'password': 'mala'}, follow_redirects=True)
    assert b'bloqueada' in r.data.lower(), "No bloqueó la cuenta en el intento 3"

    # Intento con clave correcta para cuenta bloqueada
    r = client.post('/login', data={'codigo': 'N0001', 'password': '123456'}, follow_redirects=True)
    assert b'bloqueada' in r.data.lower(), "Permitió ingresar a cuenta bloqueada"

    # Login exitoso con N0002
    r = client.post('/login', data={'codigo': 'N0002', 'password': '123456'}, follow_redirects=True)
    assert r.status_code == 200
    assert b'Cat' in r.data and b'Mar' in r.data  # María Gómez
    print("  -> HU-01 Aprobado al 100%: 3 intentos fallidos bloquean la cuenta, login válido exitoso.\n")

    # -------------------------------------------------------------
    # PASO 2: Validar HU-02 (Catálogo y Filtrado)
    # -------------------------------------------------------------
    print("[PASO 2] Probando HU-02: Catálogo y Filtrado por Categorías...")
    # Listar todos
    r = client.get('/catalogo')
    assert b'Laptop Dell' in r.data and b'Osciloscopio' in r.data and b'Switch Cisco' in r.data

    # Filtrar Cómputo
    r_comp = client.get('/catalogo?categoria=Cómputo')
    assert b'Laptop Dell' in r_comp.data and b'Switch Cisco' not in r_comp.data

    # Filtrar Electrónica
    r_elec = client.get('/catalogo?categoria=Electrónica')
    assert b'Osciloscopio' in r_elec.data and b'Laptop Dell' not in r_elec.data

    # Filtrar Redes
    r_red = client.get('/catalogo?categoria=Redes')
    assert b'Switch Cisco' in r_red.data and b'Osciloscopio' not in r_red.data
    print("  -> HU-02 Aprobado al 100%: Filtros exactos de Cómputo, Electrónica y Redes funcionando.\n")

    # -------------------------------------------------------------
    # PASO 3: Validar HU-03 (Solicitud de Reserva y Reglas de Negocio)
    # -------------------------------------------------------------
    print("[PASO 3] Probando HU-03: Solicitud de Reserva y Límite de 1 Equipo Simultáneo...")
    # Estudiante N0002 solicita equipo 1 (Laptop Dell) para 2026-11-10 de 08:00 a 10:00
    r = client.post('/reservar', data={
        'equipo_id': 1,
        'fecha': '2026-11-10',
        'hora_inicio': '08:00',
        'hora_fin': '10:00'
    }, follow_redirects=True)
    assert b'Solicitud de reserva registrada exitosamente' in r.data

    # Intento de 2da reserva simultánea con N0002
    r_segunda = client.post('/reservar', data={
        'equipo_id': 2,
        'fecha': '2026-11-10',
        'hora_inicio': '14:00',
        'hora_fin': '16:00'
    }, follow_redirects=True)
    assert b'Regla de negocio: Un estudiante no puede tener' in r_segunda.data
    print("  -> HU-03 Regla de 1 equipo simultáneo Aprobada con éxito.\n")

    # -------------------------------------------------------------
    # PASO 4: Validar HU-04 (Gestión de Administrador: Aprobar y Rechazar)
    # -------------------------------------------------------------
    print("[PASO 4] Probando HU-04: Panel de Encargado (Aprobación y Rechazo con Motivo)...")
    client.get('/logout')
    
    # Login de Administrador
    r_adm_login = client.post('/login', data={'codigo': 'ADM01', 'password': 'admin123'}, follow_redirects=True)
    assert b'Panel del Encargado de Laboratorio' in r_adm_login.data
    assert b'Solicitudes Pendientes' in r_adm_login.data

    # Aprobar la reserva de N0002 (reserva_id = 1)
    r_aprob = client.post('/admin/aprobar/1', follow_redirects=True)
    assert b'Reserva aprobada exitosamente' in r_aprob.data

    # Verificar que el equipo 1 pasó a 'Prestado'
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT estado FROM equipos WHERE id = 1")
    assert cursor.fetchone()['estado'] == 'Prestado', "El equipo no cambió a Prestado"
    print("  -> HU-04 Aprobación y cambio de equipo a 'Prestado' Aprobado.")

    # Validar HU-03 Cruce de Horario: Estudiante N0003 intenta reservar equipo 1 en horario cruzado (09:00 a 11:00)
    client.get('/logout')
    client.post('/login', data={'codigo': 'N0003', 'password': '123456'}, follow_redirects=True)
    r_cruce = client.post('/reservar', data={
        'equipo_id': 1,
        'fecha': '2026-11-10',
        'hora_inicio': '09:00',
        'hora_fin': '11:00'
    }, follow_redirects=True)
    assert b'se cruza con el solicitado' in r_cruce.data
    print("  -> HU-03 Bloqueo por cruce de horario contra reserva aprobada Aprobado con éxito.")

    # Estudiante N0003 solicita equipo 2
    client.post('/reservar', data={
        'equipo_id': 2,
        'fecha': '2026-11-10',
        'hora_inicio': '14:00',
        'hora_fin': '16:00'
    }, follow_redirects=True)

    # Encargado rechaza reserva 2
    client.get('/logout')
    client.post('/login', data={'codigo': 'ADM01', 'password': 'admin123'}, follow_redirects=True)

    # Intento de rechazo sin motivo
    r_rech_vacio = client.post('/admin/rechazar/2', data={'motivo': ''}, follow_redirects=True)
    assert b'obligatorio' in r_rech_vacio.data.lower()

    # Rechazo con motivo válido
    r_rech_ok = client.post('/admin/rechazar/2', data={'motivo': 'Equipo en mantenimiento programado'}, follow_redirects=True)
    assert b'Reserva rechazada correctamente' in r_rech_ok.data
    print("  -> HU-04 Rechazo con motivo obligatorio Aprobado al 100%.\n")

    # -------------------------------------------------------------
    # PASO 5: Validar HU-05 (Devolución y Penalización Automática)
    # -------------------------------------------------------------
    print("[PASO 5] Probando HU-05: Devolución Física y Penalización por Retraso...")
    # Devolver reserva 1 simulando entrega tardía (hora pactada era 10:00, entregado 11:30)
    r_dev = client.post('/admin/devolver/1', data={'fecha_hora_simulada': '2026-11-10 11:30'}, follow_redirects=True)
    assert b'PENALIZADO' in r_dev.data

    # Comprobar que equipo 1 vuelve a estar Disponible
    cursor.execute("SELECT estado FROM equipos WHERE id = 1")
    assert cursor.fetchone()['estado'] == 'Disponible', "El equipo no volvió a Disponible"

    # Comprobar que estudiante N0002 ahora tiene estado 'Penalizado'
    cursor.execute("SELECT estado FROM usuarios WHERE codigo = 'N0002'")
    assert cursor.fetchone()['estado'] == 'Penalizado', "El estudiante no quedó Penalizado"

    # Verificar que el estudiante penalizado N0002 tiene bloqueadas nuevas reservas
    client.get('/logout')
    client.post('/login', data={'codigo': 'N0002', 'password': '123456'}, follow_redirects=True)
    r_penal = client.post('/reservar', data={
        'equipo_id': 3,
        'fecha': '2026-11-11',
        'hora_inicio': '10:00',
        'hora_fin': '12:00'
    }, follow_redirects=True)
    assert b'Penalizado' in r_penal.data
    print("  -> HU-05 Devolución física, liberación de equipo y penalización automática Aprobada al 100%.\n")

    conn.close()
    print("=================================================================")
    print(" [EXITO TOTAL] TODAS LAS HISTORIAS HU-01 A HU-05 ESTAN LISTAS ")
    print("               Y VERIFICADAS DE PUNTA A PUNTA                ")
    print("=================================================================\n")

if __name__ == '__main__':
    run_smoke_test()
