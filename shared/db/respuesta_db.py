from psycopg2 import IntegrityError

from db.conexion import obtener_conexion


def _tabla_audios_disponible(cursor):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'audios'
        LIMIT 1
        """
    )
    return cursor.fetchone() is not None


def crear_respuesta():
    return None


def agregar_respuesta(id_entrevista, id_pregunta, texto_respuesta, *args):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO respuestas (id_entrevista, id_pregunta, texto_respuesta)
            VALUES (%s, %s, %s)
            """,
            (id_entrevista, id_pregunta, texto_respuesta),
        )
    except IntegrityError:
        print("Error: No se ha podido crear la respuesta")
        return False

    conexion.commit()
    conexion.close()
    return True


def actualizar_puntuacion_respuesta(id_entrevista, id_pregunta, *args):
    if len(args) == 1:
        nivel_ia = args[0]
    elif len(args) >= 2:
        nivel_ia = args[1]
    else:
        print("Error al actualizar: falta nivel_ia")
        return False

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE respuestas
            SET nivel_ia = %s
            WHERE id_entrevista = %s AND id_pregunta = %s
            """,
            (nivel_ia, id_entrevista, id_pregunta),
        )

        conexion.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return False
    finally:
        conexion.close()


def actualizar_analisis_ia_respuesta(id_entrevista, id_pregunta, nivel_ia, analisis_ia):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE respuestas
            SET nivel_ia = %s, analisis_ia = %s
            WHERE id_entrevista = %s AND id_pregunta = %s
            """,
            (nivel_ia, str(analisis_ia or "").strip(), id_entrevista, id_pregunta),
        )
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al actualizar analisis IA de respuesta: {e}")
        return False
    finally:
        conexion.close()


def actualizar_nivel_profesional_respuesta(id_entrevista, id_pregunta, nivel_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE respuestas
            SET nivel_profesional = %s
            WHERE id_entrevista = %s AND id_pregunta = %s
            """,
            (nivel_profesional, id_entrevista, id_pregunta),
        )
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar nivel profesional: {e}")
        return False
    finally:
        conexion.close()


def obtener_respuestas_por_entrevista(id_entrevista):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                id_pregunta,
                texto_respuesta,
                nivel_ia,
                analisis_ia,
                nivel_profesional
            FROM respuestas
            WHERE id_entrevista = %s
            ORDER BY id_pregunta
            """,
            (id_entrevista,),
        )

        filas = cursor.fetchall()
        lista_respuestas = []

        for fila in filas:
            datos = {
                "id_respuesta": fila[0],
                "id_pregunta": fila[1],
                "texto_respuesta": fila[2],
                "nivel_ia": fila[3],
                "analisis_ia": fila[4],
                "nivel_profesional": fila[5],
            }
            lista_respuestas.append(datos)

        return lista_respuestas

    except Exception as e:
        print(f"Error al obtener respuestas: {e}")
        return []
    finally:
        conexion.close()


def borrar_respuestas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DROP TABLE IF EXISTS respuestas")
    conexion.commit()
    conexion.close()
