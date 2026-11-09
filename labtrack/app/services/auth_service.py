from werkzeug.security import check_password_hash
from ..database import get_db

def autenticar_usuario(codigo, password, conn=None):
    """
    HU-01: Autenticación Segura
    - Valida credenciales contra la BD.
    - Error 'Credenciales inválidas' si no coincide.
    - Bloqueo temporal y alerta de seguridad al 3.er intento consecutivo.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE codigo = ?", (codigo.strip(),))
        user = cursor.fetchone()

        if not user:
            return False, "Credenciales inválidas", None

        # Verificar si la cuenta ya está bloqueada
        if user['estado'] == 'Bloqueado':
            return False, "Alerta de seguridad: Esta cuenta se encuentra bloqueada por múltiples intentos fallidos.", None

        # Validar contraseña
        if not check_password_hash(user['password_hash'], password):
            nuevos_intentos = user['intentos_fallidos'] + 1
            if nuevos_intentos >= 3:
                cursor.execute(
                    "UPDATE usuarios SET intentos_fallidos = ?, estado = 'Bloqueado' WHERE id = ?",
                    (nuevos_intentos, user['id'])
                )
                conn.commit()
                return False, "Alerta de seguridad: Cuenta bloqueada tras 3 intentos fallidos consecutivos.", None
            else:
                cursor.execute(
                    "UPDATE usuarios SET intentos_fallidos = ? WHERE id = ?",
                    (nuevos_intentos, user['id'])
                )
                conn.commit()
                return False, "Credenciales inválidas", None

        # Credenciales correctas: reiniciar contador de fallos
        cursor.execute("UPDATE usuarios SET intentos_fallidos = 0 WHERE id = ?", (user['id'],))
        conn.commit()

        # Recargar usuario actualizado
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user['id'],))
        usuario_actualizado = dict(cursor.fetchone())
        # No propagar el hash en sesión por seguridad
        usuario_actualizado.pop('password_hash', None)

        return True, "Inicio de sesión exitoso", usuario_actualizado

    finally:
        if close_conn:
            conn.close()
