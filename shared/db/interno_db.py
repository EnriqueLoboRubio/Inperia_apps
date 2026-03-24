from psycopg2 import IntegrityError

from db.conexion import obtener_conexion
from db.fecha_utils import normalizar_fecha


def crear_interno():
    return None


def agregar_interno(
    num_rc,
    id_usuario,
    situacion,
    delito,
    condena,
    fecha_nac,
    fecha_ingreso,
    modulo,
    lugar_nacimiento=None,
    nombre_contacto_emergencia=None,
    relacion_contacto_emergencia=None,
    numero_contacto_emergencia=None,
):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        fecha_nac = normalizar_fecha(fecha_nac)
        fecha_ingreso = normalizar_fecha(fecha_ingreso) if fecha_ingreso else None
        cursor.execute(
            """
            INSERT INTO internos (
                num_RC, id_usuario, situacion_legal, delito, condena,
                fecha_nac, fecha_ingreso, modulo, lugar_nacimiento,
                nombre_contacto_emergencia, relacion_contacto_emergencia, numero_contacto_emergencia
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                num_rc,
                id_usuario,
                situacion,
                delito,
                condena,
                fecha_nac,
                fecha_ingreso,
                modulo,
                lugar_nacimiento,
                nombre_contacto_emergencia,
                relacion_contacto_emergencia,
                numero_contacto_emergencia,
            ),
        )
        conexion.commit()
        exito = True
    except IntegrityError:
        exito = False
    finally:
        conexion.close()

    return exito


def eliminar_interno_por_id(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("DELETE FROM internos WHERE id_usuario=%s", (id_usuario,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conexion.close()


def encontrar_interno_por_id(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM internos WHERE id_usuario=%s", (id_usuario,))
    interno = cursor.fetchone()
    conexion.close()
    return interno


def encontrar_internos_por_num_rc(lista_num_rc):
    if not lista_num_rc:
        return []

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        placeholders = ",".join(["%s"] * len(lista_num_rc))
        query = f"""
            SELECT i.num_RC, i.id_usuario, i.situacion_legal, i.delito, i.condena,
                   i.fecha_nac, i.fecha_ingreso, i.modulo,
                   u.nombre, u.email, u.contrasena, u.rol,
                   i.lugar_nacimiento, i.nombre_contacto_emergencia,
                   i.relacion_contacto_emergencia, i.numero_contacto_emergencia
            FROM internos i
            INNER JOIN usuarios u ON u.id = i.id_usuario
            WHERE i.num_RC IN ({placeholders})
        """
        cursor.execute(query, tuple(lista_num_rc))
        return cursor.fetchall()
    finally:
        conexion.close()


def borrar_internos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DROP TABLE IF EXISTS internos")
    conexion.commit()
    conexion.close()
