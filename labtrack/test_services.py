import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db
from app.services.auth_service import autenticar_usuario
from app.services.catalogo_service import listar_equipos
from app.services.reserva_service import (
    crear_reserva, aprobar_reserva, rechazar_reserva, marcar_devolucion
)

def run_tests():
    # 1. Reset DB
    init_db(force=True)
    print("[OK] BD inicializada limpia para pruebas")

    # TEST HU-01: Autenticación Segura
    ok, msg, u = autenticar_usuario('N0001', 'clave_erronea')
    assert not ok and msg == 'Credenciales inválidas', f"Fallo HU-01 intento 1: {msg}"
    
    ok, msg, u = autenticar_usuario('N0001', 'clave_erronea')
    assert not ok and msg == 'Credenciales inválidas', f"Fallo HU-01 intento 2: {msg}"
    
    ok, msg, u = autenticar_usuario('N0001', 'clave_erronea')
    assert not ok and 'Cuenta bloqueada tras 3 intentos' in msg, f"Fallo HU-01 intento 3: {msg}"
    
    ok, msg, u = autenticar_usuario('N0001', '123456')
    assert not ok and 'bloqueada' in msg, f"Fallo HU-01 cuenta bloqueada: {msg}"
    
    ok, msg, u2 = autenticar_usuario('N0002', '123456')
    assert ok and u2['codigo'] == 'N0002', f"Fallo HU-01 login exitoso: {msg}"
    print("[OK] HU-01: Autenticación Segura y Bloqueo al 3.er intento validado")

    # TEST HU-02: Catálogo y Filtros
    eqs, cat = listar_equipos()
    assert len(eqs) == 9 and cat is None
    eqs_comp, cat = listar_equipos('Cómputo')
    assert len(eqs_comp) == 3 and cat == 'Cómputo'
    eqs_elec, cat = listar_equipos('Electrónica')
    assert len(eqs_elec) == 3 and cat == 'Electrónica'
    eqs_red, cat = listar_equipos('Redes')
    assert len(eqs_red) == 3 and cat == 'Redes'
    print("[OK] HU-02: Catálogo y Filtros (Cómputo, Electrónica, Redes) validado")

    # TEST HU-03: Reservas y Reglas de Negocio
    # Usuario N0002 solicita equipo 1 (Laptop Dell) para mañana de 10:00 a 12:00
    ok, msg, r1 = crear_reserva(u2['id'], 1, '2026-11-10', '10:00', '12:00')
    assert ok, f"Fallo crear reserva: {msg}"

    # Regla: Máximo 1 equipo simultáneo
    ok, msg, r2 = crear_reserva(u2['id'], 2, '2026-11-10', '14:00', '16:00')
    assert not ok and 'más de un (1) equipo' in msg, f"Fallo regla máx 1 equipo: {msg}"
    print("[OK] HU-03: Regla de máximo 1 equipo simultáneo validada")

    # TEST HU-04: Gestión Admin (Aprobación)
    ok, msg = aprobar_reserva(r1)
    assert ok, f"Fallo aprobar reserva: {msg}"
    
    # Comprobar que equipo 1 pasó a 'Prestado'
    eq1 = [e for e in listar_equipos()[0] if e['id'] == 1][0]
    assert eq1['estado'] == 'Prestado', f"Estado de equipo no es Prestado: {eq1}"
    print("[OK] HU-04: Aprobación de reserva y pase de equipo a 'Prestado' validado")

    # Regla HU-03 Cruce de Horario:
    # Usuario N0003 intenta reservar equipo 1 en horario que se cruza (11:00 a 13:00)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE codigo = 'N0003'")
    u3 = cursor.fetchone()
    ok, msg, r_cruce = crear_reserva(u3['id'], 1, '2026-11-10', '11:00', '13:00')
    assert not ok and 'se cruza con el solicitado' in msg, f"Fallo regla cruce horario: {msg}"
    print("[OK] HU-03: Regla de Bloqueo por Cruce de Horario validada")

    # TEST HU-04: Rechazo con Justificación Obligatoria
    ok, msg, r3 = crear_reserva(u3['id'], 2, '2026-11-10', '10:00', '12:00')
    assert ok
    # Rechazo sin motivo -> Debe fallar
    ok, msg = rechazar_reserva(r3, '')
    assert not ok and 'obligatorio' in msg, f"Fallo validación motivo obligatorio: {msg}"
    # Rechazo con motivo -> Exitoso
    ok, msg = rechazar_reserva(r3, 'Equipo en mantenimiento preventivo')
    assert ok, f"Fallo rechazo con motivo: {msg}"
    print("[OK] HU-04: Rechazo con Justificación Obligatoria validado")

    # TEST HU-05: Devolución y Penalización Automática
    # Caso 1: Devolución tardía (hora fin era 12:00, devolvemos a las 13:00)
    dt_tardia = datetime.strptime('2026-11-10 13:00', '%Y-%m-%d %H:%M')
    ok, msg, info = marcar_devolucion(r1, fecha_hora_actual=dt_tardia)
    assert ok and info['penalizado'] is True, f"Fallo marcar devolución tardía: {msg}"
    
    # Verificar que el estudiante N0002 quedó en estado 'Penalizado'
    cursor.execute("SELECT estado FROM usuarios WHERE id = ?", (u2['id'],))
    assert cursor.fetchone()['estado'] == 'Penalizado', "Estudiante no fue penalizado"

    # Verificar que el equipo volvió a 'Disponible'
    cursor.execute("SELECT estado FROM equipos WHERE id = 1")
    assert cursor.fetchone()['estado'] == 'Disponible', "Equipo no volvió a Disponible"
    print("[OK] HU-05: Devolución física inmediata a 'Disponible' y Penalización Automática validada")

    conn.close()
    print("\n=======================================================")
    print(" [EXITO] TODAS LAS REGLAS DE NEGOCIO (HU-01 A HU-05) FUNCIONAN AL 100%")
    print("=======================================================\n")

if __name__ == '__main__':
    run_tests()
