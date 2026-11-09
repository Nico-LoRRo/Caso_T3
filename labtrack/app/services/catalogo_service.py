from ..database import get_db

CATEGORIAS_VALIDAS = ['Cómputo', 'Electrónica', 'Redes']
MENSAJE_CATALOGO_VACIO = "No hay equipos disponibles en esta categoría"

def listar_equipos(categoria=None, conn=None):
    """
    HU-02: Catálogo y Filtrado de Equipos
    - Retorna nombre, codigo_inventario, categoria, estado.
    - Filtros exactos por 'Cómputo', 'Electrónica' y 'Redes'.
    """
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        categoria_filtrada = None
        if categoria and categoria in CATEGORIAS_VALIDAS:
            categoria_filtrada = categoria
            cursor.execute(
                "SELECT id, codigo_inventario, nombre, categoria, estado FROM equipos WHERE categoria = ? ORDER BY id ASC",
                (categoria,)
            )
        else:
            cursor.execute(
                "SELECT id, codigo_inventario, nombre, categoria, estado FROM equipos ORDER BY id ASC"
            )

        equipos = [dict(row) for row in cursor.fetchall()]
        return equipos, categoria_filtrada
    finally:
        if close_conn:
            conn.close()

def obtener_equipo_por_id(equipo_id, conn=None):
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipos WHERE id = ?", (equipo_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        if close_conn:
            conn.close()
