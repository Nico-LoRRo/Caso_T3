from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from .services.auth_service import autenticar_usuario
from .services.catalogo_service import listar_equipos, MENSAJE_CATALOGO_VACIO
from .services.reserva_service import (
    crear_reserva, listar_reservas_estudiante, listar_solicitudes_pendientes,
    listar_prestamos_activos, aprobar_reserva, rechazar_reserva, marcar_devolucion
)

main_bp = Blueprint('main', __name__)

def login_required(rol=None):
    """Decorador para proteger rutas por autenticación y rol"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            usuario = session.get('user')
            if not usuario:
                flash("Debe iniciar sesión para acceder al sistema.", "warning")
                return redirect(url_for('main.login'))
            
            if rol and usuario.get('rol') != rol:
                flash("No tiene permisos para acceder a esta sección.", "danger")
                if usuario.get('rol') == 'estudiante':
                    return redirect(url_for('main.catalogo'))
                else:
                    return redirect(url_for('main.admin_panel'))
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@main_bp.route('/')
def index():
    usuario = session.get('user')
    if usuario:
        if usuario.get('rol') == 'encargado':
            return redirect(url_for('main.admin_panel'))
        return redirect(url_for('main.catalogo'))
    return redirect(url_for('main.login'))

# ============================================================
# HU-01: Autenticación Segura
# ============================================================
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        password = request.form.get('password', '')

        if not codigo or not password:
            flash("Por favor ingrese su código y contraseña.", "warning")
            return render_template('login.html', codigo=codigo)

        exito, mensaje, usuario = autenticar_usuario(codigo, password)

        if not exito:
            flash(mensaje, "danger")
            return render_template('login.html', codigo=codigo)

        # Login correcto
        session['user'] = usuario
        flash(f"¡Bienvenido, {usuario['nombre']}!", "success")

        if usuario['rol'] == 'encargado':
            return redirect(url_for('main.admin_panel'))
        return redirect(url_for('main.catalogo'))

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash("Ha cerrado sesión correctamente.", "info")
    return redirect(url_for('main.login'))

# ============================================================
# HU-02: Catálogo y Filtrado de Equipos
# HU-03: Reserva de Equipos (Estudiante)
# ============================================================
@main_bp.route('/catalogo', methods=['GET'])
@login_required(rol='estudiante')
def catalogo():
    categoria = request.args.get('categoria')
    equipos, cat_filtrada = listar_equipos(categoria)
    
    mensaje_vacio = None
    if not equipos:
        mensaje_vacio = MENSAJE_CATALOGO_VACIO

    usuario_id = session['user']['id']
    mis_reservas = listar_reservas_estudiante(usuario_id)

    return render_template(
        'catalogo.html',
        equipos=equipos,
        categoria_actual=cat_filtrada,
        mensaje_vacio=mensaje_vacio,
        mis_reservas=mis_reservas,
        usuario=session['user']
    )

@main_bp.route('/reservar', methods=['POST'])
@login_required(rol='estudiante')
def reservar():
    usuario_id = session['user']['id']
    equipo_id = request.form.get('equipo_id', type=int)
    fecha = request.form.get('fecha', '').strip()
    hora_inicio = request.form.get('hora_inicio', '').strip()
    hora_fin = request.form.get('hora_fin', '').strip()

    exito, mensaje, reserva_id = crear_reserva(
        usuario_id=usuario_id,
        equipo_id=equipo_id,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin
    )

    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")

    return redirect(url_for('main.catalogo'))

# ============================================================
# HU-04: Gestión de Solicitudes (Aprobar / Rechazar)
# HU-05: Devolución y Penalización Automática
# ============================================================
@main_bp.route('/admin', methods=['GET'])
@login_required(rol='encargado')
def admin_panel():
    solicitudes = listar_solicitudes_pendientes()
    prestamos = listar_prestamos_activos()
    return render_template(
        'admin.html',
        solicitudes=solicitudes,
        prestamos=prestamos,
        usuario=session['user']
    )

@main_bp.route('/admin/aprobar/<int:reserva_id>', methods=['POST'])
@login_required(rol='encargado')
def admin_aprobar(reserva_id):
    exito, mensaje = aprobar_reserva(reserva_id)
    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/rechazar/<int:reserva_id>', methods=['POST'])
@login_required(rol='encargado')
def admin_rechazar(reserva_id):
    motivo = request.form.get('motivo', '').strip()
    exito, mensaje = rechazar_reserva(reserva_id, motivo)
    if exito:
        flash(mensaje, "info")
    else:
        flash(mensaje, "danger")
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/devolver/<int:reserva_id>', methods=['POST'])
@login_required(rol='encargado')
def admin_devolver(reserva_id):
    # Permite opcionalmente simular fecha/hora para pruebas docentes o manuales
    hora_simulada_str = request.form.get('fecha_hora_simulada', '').strip()
    dt_actual = None
    if hora_simulada_str:
        try:
            dt_actual = datetime.strptime(hora_simulada_str, "%Y-%m-%d %H:%M")
        except ValueError:
            dt_actual = None

    exito, mensaje, info = marcar_devolucion(reserva_id, fecha_hora_actual=dt_actual)
    if exito:
        if info and info.get('penalizado'):
            flash(mensaje, "warning")
        else:
            flash(mensaje, "success")
    else:
        flash(mensaje, "danger")

    return redirect(url_for('main.admin_panel'))
