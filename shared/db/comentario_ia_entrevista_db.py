from db.conexion import obtener_conexion
from db.fecha_utils import normalizar_fecha


NOMBRE_TABLA = "comentarios_ia_ent"


def crear_tabla_comentarios_ia_entrevista():
    return None


def _asegurar_fila(cursor, id_entrevista):
    cursor.execute(
        f"""
        INSERT INTO {NOMBRE_TABLA} (id_entrevista)
        VALUES (%s)
        ON CONFLICT (id_entrevista) DO NOTHING
        """,
        (id_entrevista,),
    )


def agregar_comentario_ia(id_entrevista, comentario_ia, fecha_ia):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        fecha_norm = normalizar_fecha(fecha_ia)
        _asegurar_fila(cursor, id_entrevista)
        cursor.execute(
            f"""
            UPDATE {NOMBRE_TABLA}
            SET comentario_ia = %s, fecha_ia = %s
            WHERE id_entrevista = %s
            """,
            (comentario_ia, fecha_norm, id_entrevista),
        )
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al guardar comentario IA de entrevista: {e}")
        return False
    finally:
        conexion.close()


def obtener_comentario_ia(id_entrevista):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            f"""
            SELECT id, id_entrevista, comentario_ia, fecha_ia
            FROM {NOMBRE_TABLA}
            WHERE id_entrevista = %s
            """,
            (id_entrevista,),
        )
        return cursor.fetchone()
    finally:
        conexion.close()
