from datetime import datetime
from ..database import get_db

def crear_reserva(usuario_id, equipo_id, fecha, hora_inicio, hora_fin, conn=None):
    """
    HU-03: Reserva de Equipos (Flujo Crítico)
    - Regla 1: Un estudiante no puede tener más de 1 equipo reservado de forma simultánea.
    - Regla 2: Bloquear si se cruza con una reserva aprobada para ese equipo y horario.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Validación básica de datos
        if not fecha or not hora_inicio or not hora_fin:
            return False, "Todos los campos de fecha y horario son obligatorios.", None

        if hora_fin <= hora_inicio:
            return False, "La hora de fin debe ser posterior a la hora de inicio.", None

        # Verificar estado del usuario
        cursor.execute("SELECT estado, rol FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = cursor.fetchone()
        if not usuario:
            return False, "Usuario no encontrado.", None

        if usuario['estado'] == 'Penalizado':
            return False, "Operación denegada: El estudiante se encuentra en estado 'Penalizado' y no puede solicitar reservas.", None

        if usuario['estado'] == 'Bloqueado':
            return False, "Operación denegada: La cuenta del estudiante está bloqueada.", None

        # Regla de negocio 1: Máximo 1 equipo reservado de forma simultánea
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM reservas 
            WHERE usuario_id = ? AND estado IN ('Pendiente', 'Aprobada')
        """, (usuario_id,))
        activas = cursor.fetchone()['total']
        if activas >= 1:
            return False, "Regla de negocio: Un estudiante no puede tener más de un (1) equipo reservado de forma simultánea.", None

        # Verificar existencia del equipo
        cursor.execute("SELECT * FROM equipos WHERE id = ?", (equipo_id,))
        equipo = cursor.fetchone()
        if not equipo:
            return False, "El equipo seleccionado no existe.", None

        # Regla de negocio 2: Bloquear si se cruza con una reserva 'Aprobada'
        # Dos intervalos [A_inicio, A_fin] y [B_inicio, B_fin] se solapan si:
        # A_inicio < B_fin AND A_fin > B_inicio
        cursor.execute("""
            SELECT id, hora_inicio, hora_fin 
            FROM reservas 
            WHERE equipo_id = ? 
              AND fecha = ? 
              AND estado = 'Aprobada'
              AND hora_inicio < ? 
              AND hora_fin > ?
        """, (equipo_id, fecha, hora_fin, hora_inicio))

        cruce = cursor.fetchone()
        if cruce:
            return False, f"Regla de negocio: El equipo ya cuenta con una reserva aprobada en el horario {cruce['hora_inicio']} - {cruce['hora_fin']} que se cruza con el solicitado.", None

        # Registrar reserva en estado 'Pendiente'
        cursor.execute("""
            INSERT INTO reservas (usuario_id, equipo_id, fecha, hora_inicio, hora_fin, estado)
            VALUES (?, ?, ?, ?, ?, 'Pendiente')
        """, (usuario_id, equipo_id, fecha, hora_inicio, hora_fin))
        conn.commit()

        reserva_id = cursor.lastrowid
        return True, "Solicitud de reserva registrada exitosamente. Pendiente de aprobación.", reserva_id

    finally:
        if close_conn:
            conn.close()

def listar_reservas_estudiante(usuario_id, conn=None):
    """Historial y reservas activas del estudiante"""
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, e.nombre as equipo_nombre, e.codigo_inventario, e.categoria
            FROM reservas r
            JOIN equipos e ON r.equipo_id = e.id
            WHERE r.usuario_id = ?
            ORDER BY r.id DESC
        """, (usuario_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_conn:
            conn.close()

def listar_solicitudes_pendientes(conn=None):
    """
    HU-04: Panel de Administrador - Solicitudes pendientes
    Campos requeridos: Nombre del estudiante, Equipo, Fecha/Hora solicitada y acciones.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.fecha, r.hora_inicio, r.hora_fin, r.estado,
                   u.nombre as estudiante_nombre, u.codigo as estudiante_codigo,
                   e.nombre as equipo_nombre, e.codigo_inventario as equipo_codigo
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN equipos e ON r.equipo_id = e.id
            WHERE r.estado = 'Pendiente'
            ORDER BY r.id ASC
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_conn:
            conn.close()

def listar_prestamos_activos(conn=None):
    """
    HU-05: Préstamos activos (Reservas aprobadas para marcar devolución)
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.fecha, r.hora_inicio, r.hora_fin, r.estado,
                   u.id as usuario_id, u.nombre as estudiante_nombre, u.codigo as estudiante_codigo, u.estado as estudiante_estado,
                   e.id as equipo_id, e.nombre as equipo_nombre, e.codigo_inventario as equipo_codigo
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN equipos e ON r.equipo_id = e.id
            WHERE r.estado = 'Aprobada'
            ORDER BY r.id ASC
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if close_conn:
            conn.close()

def aprobar_reserva(reserva_id, conn=None):
    """
    HU-04: Al hacer clic en 'Aprobar', el estado de la reserva cambia a 'Aprobada'
    y el equipo pasa a estado 'Prestado'.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        reserva = cursor.fetchone()
        if not reserva:
            return False, "Reserva no encontrada."

        if reserva['estado'] != 'Pendiente':
            return False, f"La reserva ya no está pendiente (estado actual: {reserva['estado']})."

        # Actualizar reserva a 'Aprobada'
        cursor.execute("UPDATE reservas SET estado = 'Aprobada' WHERE id = ?", (reserva_id,))
        # Actualizar equipo a 'Prestado'
        cursor.execute("UPDATE equipos SET estado = 'Prestado' WHERE id = ?", (reserva['equipo_id'],))

        conn.commit()
        return True, "Reserva aprobada exitosamente. El equipo ha pasado a estado 'Prestado'."
    finally:
        if close_conn:
            conn.close()

def rechazar_reserva(reserva_id, motivo, conn=None):
    """
    HU-04: Al hacer clic en 'Rechazar', se debe exigir obligatoriamente un breve texto justificando el motivo.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        if not motivo or not motivo.strip():
            return False, "El motivo de justificación para rechazar la reserva es obligatorio."

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        reserva = cursor.fetchone()
        if not reserva:
            return False, "Reserva no encontrada."

        if reserva['estado'] != 'Pendiente':
            return False, f"La reserva ya no está pendiente (estado actual: {reserva['estado']})."

        # Actualizar reserva a 'Rechazada' con el motivo
        cursor.execute("""
            UPDATE reservas 
            SET estado = 'Rechazada', motivo_rechazo = ? 
            WHERE id = ?
        """, (motivo.strip(), reserva_id))

        conn.commit()
        return True, "Reserva rechazada correctamente."
    finally:
        if close_conn:
            conn.close()

def marcar_devolucion(reserva_id, fecha_hora_actual=None, conn=None):
    """
    HU-05: Devolución y Penalización Automática
    - El equipo cambia inmediatamente su estado a 'Disponible'.
    - Regla de negocio: Si fecha/hora actual > hora de fin acordada,
      el sistema cambia automáticamente el estado del estudiante a 'Penalizado'.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, u.nombre as estudiante_nombre, e.nombre as equipo_nombre
            FROM reservas r
            JOIN usuarios u ON r.usuario_id = u.id
            JOIN equipos e ON r.equipo_id = e.id
            WHERE r.id = ?
        """, (reserva_id,))
        reserva = cursor.fetchone()

        if not reserva:
            return False, "Reserva no encontrada.", None

        if reserva['estado'] != 'Aprobada':
            return False, f"Solo se pueden devolver reservas en estado 'Aprobada' (actual: {reserva['estado']}).", None

        # Determinar fecha y hora actual (permite inyectar para pruebas)
        ahora = fecha_hora_actual or datetime.now()
        fecha_devolucion_str = ahora.strftime("%Y-%m-%d %H:%M:%S")

        # Marcar reserva como devuelta
        cursor.execute("""
            UPDATE reservas 
            SET estado = 'Devuelta', fecha_devolucion = ? 
            WHERE id = ?
        """, (fecha_devolucion_str, reserva_id))

        # El equipo cambia inmediatamente su estado a 'Disponible'
        cursor.execute("UPDATE equipos SET estado = 'Disponible' WHERE id = ?", (reserva['equipo_id'],))

        # Verificar si la hora acordada ya expiró
        hora_acordada_str = f"{reserva['fecha']} {reserva['hora_fin']}"
        acordada_dt = datetime.strptime(hora_acordada_str, "%Y-%m-%d %H:%M")

        penalizado = False
        if ahora > acordada_dt:
            # Penalizar estudiante
            cursor.execute("UPDATE usuarios SET estado = 'Penalizado' WHERE id = ?", (reserva['usuario_id'],))
            penalizado = True
            mensaje = f"Devolución registrada con retraso. El estudiante '{reserva['estudiante_nombre']}' ha sido automáticamente PENALIZADO."
        else:
            mensaje = f"Devolución registrada a tiempo. El equipo '{reserva['equipo_nombre']}' vuelve a estar disponible."

        conn.commit()
        return True, mensaje, {"penalizado": penalizado, "equipo_id": reserva['equipo_id']}

    finally:
        if close_conn:
            conn.close()
