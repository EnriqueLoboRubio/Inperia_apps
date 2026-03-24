from datetime import datetime

from db.conexion import obtener_conexion


def crear_comentario_pre():
    return None


def listar_comentarios_respuesta(id_respuesta):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT id, id_respuesta, id_profesional, comentario, fecha
            FROM comentarios_pre
            WHERE id_respuesta = %s
            ORDER BY fecha ASC, id ASC
            """,
            (id_respuesta,),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def agregar_comentario_respuesta(id_respuesta, id_profesional, comentario, fecha=None):
    texto = str(comentario or "").strip()
    if not texto:
        return None
    fecha_txt = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO comentarios_pre (id_respuesta, id_profesional, comentario, fecha)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (id_respuesta, id_profesional, texto, fecha_txt),
        )
        nuevo_id = cursor.fetchone()[0]
        conexion.commit()
        return nuevo_id
    finally:
        conexion.close()


def eliminar_comentario_respuesta(id_comentario, id_profesional=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        if id_profesional is None:
            cursor.execute(
                "DELETE FROM comentarios_pre WHERE id = %s",
                (id_comentario,),
            )
        else:
            cursor.execute(
                """
                DELETE FROM comentarios_pre
                WHERE id = %s AND id_profesional = %s
                """,
                (id_comentario, id_profesional),
            )
        conexion.commit()
        return cursor.rowcount > 0
    finally:
        conexion.close()


def reemplazar_comentarios_respuesta(id_respuesta, comentarios):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM comentarios_pre
            WHERE id_respuesta = %s
            """,
            (id_respuesta,),
        )

        for comentario in list(comentarios or []):
            texto = str(comentario.get("comentario", "") or "").strip()
            if not texto:
                continue
            cursor.execute(
                """
                INSERT INTO comentarios_pre (id_respuesta, id_profesional, comentario, fecha)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    id_respuesta,
                    comentario.get("id_profesional"),
                    texto,
                    str(comentario.get("fecha", "") or "").strip(),
                ),
            )

        conexion.commit()
        return True
    finally:
        conexion.close()
