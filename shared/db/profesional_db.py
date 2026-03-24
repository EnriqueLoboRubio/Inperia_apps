from psycopg2 import IntegrityError

from db.conexion import obtener_conexion


def crear_profesional():
    return None


def agregar_profesional(id_usuario, num_colegiado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO profesionales (id_usuario, num_colegiado)
            VALUES (%s, %s)
            """,
            (id_usuario, num_colegiado),
        )
        conexion.commit()
        exito = True
    except IntegrityError:
        exito = False
    finally:
        conexion.close()

    return exito


def encontrar_profesional_por_id(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT num_colegiado FROM profesionales WHERE id_usuario=%s",
        (id_usuario,),
    )
    resultado = cursor.fetchone()
    conexion.close()
    return resultado


def eliminar_profesional():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DROP TABLE IF EXISTS profesionales")
    conexion.commit()
    conexion.close()
