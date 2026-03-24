from datetime import datetime

from db.conexion import obtener_conexion


def crear_tabla_comentarios_entrevista_mensajes():
    return None


def listar_comentarios_entrevista(id_entrevista):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT id, id_entrevista, id_profesional, comentario, fecha_creacion
            FROM comentarios_entrevista_mensajes
            WHERE id_entrevista = %s
            ORDER BY fecha_creacion ASC, id ASC
            """,
            (id_entrevista,),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def agregar_comentario_entrevista(id_entrevista, id_profesional, comentario, fecha_creacion=None):
    texto = str(comentario or "").strip()
    if not texto:
        return None

    fecha = fecha_creacion or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO comentarios_entrevista_mensajes
            (id_entrevista, id_profesional, comentario, fecha_creacion)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (id_entrevista, id_profesional, texto, fecha),
        )
        nuevo_id = cursor.fetchone()[0]
        conexion.commit()
        return nuevo_id
    finally:
        conexion.close()


def eliminar_comentario_entrevista(id_comentario, id_profesional=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        if id_profesional is None:
            cursor.execute(
                "DELETE FROM comentarios_entrevista_mensajes WHERE id = %s",
                (id_comentario,),
            )
        else:
            cursor.execute(
                """
                DELETE FROM comentarios_entrevista_mensajes
                WHERE id = %s AND id_profesional = %s
                """,
                (id_comentario, id_profesional),
            )
        conexion.commit()
        return cursor.rowcount > 0
    finally:
        conexion.close()


def reemplazar_comentarios_entrevista(id_entrevista, comentarios):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM comentarios_entrevista_mensajes
            WHERE id_entrevista = %s
            """,
            (id_entrevista,),
        )

        for comentario in list(comentarios or []):
            texto = str(comentario.get("comentario", "") or "").strip()
            if not texto:
                continue
            cursor.execute(
                """
                INSERT INTO comentarios_entrevista_mensajes
                (id_entrevista, id_profesional, comentario, fecha_creacion)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    id_entrevista,
                    comentario.get("id_profesional"),
                    texto,
                    str(comentario.get("fecha", "") or comentario.get("fecha_creacion", "") or "").strip(),
                ),
            )

        conexion.commit()
        return True
    finally:
        conexion.close()
