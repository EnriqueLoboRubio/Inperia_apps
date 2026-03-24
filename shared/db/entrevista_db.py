from psycopg2 import IntegrityError

from db.conexion import obtener_conexion
from db.fecha_utils import normalizar_fecha


def crear_entrevista():
    return None


def agregar_entrevista(id_interno, id_solicitud, fecha):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        fecha = normalizar_fecha(fecha)
        cursor.execute(
            """
            INSERT INTO entrevistas (id_interno, id_solicitud, fecha)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (id_interno, id_solicitud, fecha),
        )
        id_entrevista = cursor.fetchone()[0]
    except (IntegrityError, ValueError) as e:
        print(f"Error: No se ha podido crear la entrevista. {e}")
        return False

    conexion.commit()
    conexion.close()
    return id_entrevista


def agregar_entrevista_y_respuestas(id_interno, id_solicitud, fecha, lista_respuestas):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        fecha = normalizar_fecha(fecha)
        cursor.execute(
            """
            INSERT INTO entrevistas (id_interno, id_solicitud, fecha)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (id_interno, id_solicitud, fecha),
        )
        id_entrevista = cursor.fetchone()[0]

        respuestas_creadas = []

        for i, pregunta in enumerate(lista_respuestas):
            id_pregunta = i + 1
            cursor.execute(
                """
                INSERT INTO respuestas (id_entrevista, id_pregunta, texto_respuesta)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (id_entrevista, id_pregunta, pregunta.respuesta),
            )
            id_respuesta = cursor.fetchone()[0]
            pregunta.id_respuesta = id_respuesta
            respuestas_creadas.append({
                "id_respuesta": id_respuesta,
                "id_pregunta": id_pregunta,
                "pregunta": pregunta,
            })
    except Exception as e:
        print(f"CRITICAL ERROR DB: {e}")
        return None

    conexion.commit()
    conexion.close()
    return {
        "id_entrevista": id_entrevista,
        "respuestas": respuestas_creadas,
    }


def eliminar_entrevista(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM entrevistas WHERE id=%s", (id,))
    conexion.commit()
    conexion.close()


def encontrar_entrevista_por_solicitud(id_solicitud):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM entrevistas WHERE id_solicitud=%s", (id_solicitud,))
    entrevista = cursor.fetchone()
    conexion.commit()
    conexion.close()
    return entrevista


def encontrar_entrevista_por_id(id_entrevista):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM entrevistas WHERE id=%s", (id_entrevista,))
    entrevista = cursor.fetchone()
    conexion.commit()
    conexion.close()
    return entrevista


def listar_ultimas_entrevistas_por_interno(id_interno, limite=5):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT
                e.id,
                e.id_solicitud,
                e.fecha,
                e.puntuacion_ia,
                s.tipo,
                COALESCE(cie.comentario_ia, ''),
                'IA'
            FROM entrevistas e
            LEFT JOIN solicitudes s ON s.id = e.id_solicitud
            LEFT JOIN comentarios_ia_ent cie ON cie.id_entrevista = e.id
            WHERE e.id_interno = %s
            ORDER BY e.fecha DESC, e.id DESC
            LIMIT %s
            """,
            (id_interno, limite),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def obtener_ultima_entrevista_interno_profesional(id_interno, id_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT e.id, e.fecha, e.puntuacion_ia
            FROM entrevistas e
            INNER JOIN solicitudes s ON s.id = e.id_solicitud
            WHERE e.id_interno = %s
              AND s.id_profesional = %s
            ORDER BY e.fecha DESC, e.id DESC
            LIMIT 1
            """,
            (id_interno, id_profesional),
        )
        return cursor.fetchone()
    finally:
        conexion.close()


def obtener_ultima_entrevista_interno(id_interno):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT e.id, e.fecha, e.puntuacion_ia
            FROM entrevistas e
            WHERE e.id_interno = %s
            ORDER BY e.fecha DESC, e.id DESC
            LIMIT 1
            """,
            (id_interno,),
        )
        return cursor.fetchone()
    finally:
        conexion.close()


def obtener_ultimas_entrevistas_interno(id_interno, limite=2):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT e.id, e.fecha, e.puntuacion_ia
            FROM entrevistas e
            WHERE e.id_interno = %s
            ORDER BY e.fecha DESC, e.id DESC
            LIMIT %s
            """,
            (id_interno, limite),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def borrar_entrevistas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DROP TABLE IF EXISTS entrevistas")
    conexion.commit()
    conexion.close()


def actualizar_puntuacion_entrevista(id, puntuacion_ia):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE entrevistas
            SET puntuacion_ia = %s
            WHERE id = %s
            """,
            (puntuacion_ia, id),
        )
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return False
    finally:
        conexion.close()


def actualizar_puntuacion_profesional_entrevista(id, puntuacion_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE entrevistas
            SET puntuacion_profesional = %s
            WHERE id = %s
            """,
            (puntuacion_profesional, id),
        )
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar puntuacion profesional: {e}")
        return False
    finally:
        conexion.close()


def actualizar_estado_evaluacion_ia_entrevista(id, estado_evaluacion_ia):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE entrevistas
            SET estado_evaluacion_ia = %s
            WHERE id = %s
            """,
            (estado_evaluacion_ia, id),
        )
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar estado de evaluacion IA: {e}")
        return False
    finally:
        conexion.close()
