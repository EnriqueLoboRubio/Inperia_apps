from psycopg2 import IntegrityError
from psycopg2.extras import RealDictCursor

from db.conexion import obtener_conexion
from db.fecha_utils import normalizar_fecha


def crear_solicitud():
    return None


def agregar_solicitud(
    id_interno,
    tipo,
    motivo,
    descripcion,
    urgencia,
    fecha_creacion,
    fecha_inicio,
    fecha_fin,
    hora_salida,
    hora_llegada,
    destino,
    provincia,
    direccion,
    cod_pos,
    nombre_cp,
    telf_cp,
    relacion_cp,
    direccion_cp,
    nombre_cs,
    telf_cs,
    relacion_cs,
    docs,
    compromiso,
    observaciones,
    estado,
    id_profesional=None,
    conclusiones_profesional=None,
):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        fecha_creacion = normalizar_fecha(fecha_creacion)
        fecha_inicio = normalizar_fecha(fecha_inicio)
        fecha_fin = normalizar_fecha(fecha_fin)
        cursor.execute(
            """
            INSERT INTO solicitudes (
                id_interno, tipo, motivo, descripcion, urgencia, fecha_creacion, fecha_inicio, fecha_fin,
                hora_salida, hora_llegada, destino, provincia, direccion, cod_pos, nombre_cp, telf_cp,
                relacion_cp, direccion_cp, nombre_cs, telf_cs, relacion_cs, docs, compromiso,
                observaciones, conclusiones_profesional, estado, id_profesional
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                id_interno,
                tipo,
                motivo,
                descripcion,
                urgencia,
                fecha_creacion,
                fecha_inicio,
                fecha_fin,
                hora_salida,
                hora_llegada,
                destino,
                provincia,
                direccion,
                cod_pos,
                nombre_cp,
                telf_cp,
                relacion_cp,
                direccion_cp,
                nombre_cs,
                telf_cs,
                relacion_cs,
                docs,
                compromiso,
                observaciones,
                conclusiones_profesional,
                estado,
                id_profesional,
            ),
        )
        nuevo_id = cursor.fetchone()[0]
        conexion.commit()
    except (IntegrityError, ValueError) as e:
        print(f"Error: No se ha podido crear la solicitud. {e}")
        return None
    finally:
        conexion.close()

    return nuevo_id


def eliminar_solicitud(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM solicitudes WHERE id=%s", (id,))
    conexion.commit()
    conexion.close()


def encontrar_solicitud_por_id(id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM solicitudes WHERE id=%s", (id,))
    solicitud = cursor.fetchone()
    conexion.close()
    return solicitud


def encontrar_solicitud_pendiente_por_interno(id_interno):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM solicitudes WHERE id_interno=%s AND estado IN ('pendiente', 'iniciada')",
        (id_interno,),
    )
    solicitud = cursor.fetchone()
    conexion.close()
    return solicitud


def encontrar_ultima_solicitud_por_interno(id_interno):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM solicitudes WHERE id_interno = %s ORDER BY fecha_creacion DESC, id DESC LIMIT 1",
        (id_interno,),
    )
    solicitud = cursor.fetchone()
    conexion.close()
    return solicitud


def contar_solicitudes_por_profesional_y_estados(id_profesional, estados):
    if not estados:
        return 0

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        placeholders = ",".join(["%s"] * len(estados))
        query = f"""
            SELECT COUNT(*)
            FROM solicitudes
            WHERE id_profesional = %s
              AND estado IN ({placeholders})
        """
        cursor.execute(query, (id_profesional, *estados))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    finally:
        conexion.close()


def contar_solicitudes_por_profesional(id_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM solicitudes
            WHERE id_profesional = %s
            """,
            (id_profesional,),
        )
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    finally:
        conexion.close()


def contar_solicitudes_por_evaluar_profesional(id_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM solicitudes
            WHERE id_profesional = %s
              AND estado IN ('iniciada', 'pendiente')
              AND TRIM(COALESCE(conclusiones_profesional, '')) = ''
            """,
            (id_profesional,),
        )
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    finally:
        conexion.close()


def listar_solicitudes_nuevas_sin_profesional():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT *
            FROM solicitudes
            WHERE id_profesional IS NULL
            ORDER BY fecha_creacion DESC, id_interno ASC, id DESC
            """
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def listar_solicitudes_pendientes_profesional(id_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT s.*
            FROM solicitudes s
            WHERE s.id_profesional = %s
              AND s.estado = 'pendiente'
              AND EXISTS (
                  SELECT 1
                  FROM entrevistas e
                  WHERE e.id_solicitud = s.id
              )
            ORDER BY s.fecha_creacion DESC, s.id_interno ASC, s.id DESC
            """,
            (id_profesional,),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def listar_solicitudes_profesional(id_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT *
            FROM solicitudes
            WHERE id_profesional = %s
            ORDER BY fecha_creacion DESC, id_interno ASC, id DESC
            """,
            (id_profesional,),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def listar_solicitudes_por_interno(id_interno):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT *
            FROM solicitudes
            WHERE id_interno = %s
            ORDER BY fecha_creacion DESC, id DESC
            """,
            (id_interno,),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def _query_resumen_staff_base(modo, incluir_order_by=True, incluir_paginacion=True):
    condiciones = []
    parametros = []

    if modo == "nuevas":
        condiciones.extend([
            "s.id_profesional IS NULL",
            "s.estado IN ('iniciada', 'pendiente')",
        ])
    elif modo == "por_evaluar":
        condiciones.extend([
            "s.id_profesional = %s",
            "s.estado IN ('iniciada', 'pendiente')",
            "TRIM(COALESCE(s.conclusiones_profesional, '')) = ''",
        ])
    elif modo == "completadas":
        condiciones.extend([
            "s.id_profesional = %s",
            "s.estado IN ('aceptada', 'rechazada', 'cancelada')",
        ])
    elif modo in {"historial", "profesional_todas"}:
        condiciones.append("s.id_profesional = %s")
    else:
        raise ValueError(f"Modo de listado no soportado: {modo}")

    return condiciones, parametros


def _aplicar_parametros_modo(condiciones, parametros, modo, id_profesional):
    if modo in {"por_evaluar", "completadas", "historial", "profesional_todas"}:
        parametros = [id_profesional, *parametros]

    where_sql = " AND ".join(condiciones) if condiciones else "TRUE"
    return where_sql, parametros


def _normalizar_estado_combo(estado):
    valor = str(estado or "").strip().lower()
    mapa = {
        "todos": None,
        "nuevas": "iniciada",
        "iniciadas": "iniciada",
        "pendientes": "pendiente",
        "aceptada": "aceptada",
        "aceptadas": "aceptada",
        "rechazada": "rechazada",
        "rechazadas": "rechazada",
        "cancelada": "cancelada",
        "canceladas": "cancelada",
        "completadas": "completadas",
    }
    return mapa.get(valor)


def listar_solicitudes_resumen_staff(
    modo,
    id_profesional=None,
    busqueda=None,
    estado=None,
    limit=10,
    offset=0,
):
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    try:
        condiciones, parametros = _query_resumen_staff_base(modo)

        estado_normalizado = _normalizar_estado_combo(estado)
        if estado_normalizado == "completadas":
            condiciones.append("s.estado IN ('aceptada', 'rechazada', 'cancelada')")
        elif estado_normalizado:
            condiciones.append("s.estado = %s")
            parametros.append(estado_normalizado)

        texto_busqueda = str(busqueda or "").strip().lower()
        if texto_busqueda:
            patron = f"%{texto_busqueda}%"
            condiciones.append("(LOWER(u.nombre) LIKE %s OR CAST(i.num_rc AS TEXT) LIKE %s)")
            parametros.extend([patron, patron])

        where_sql, parametros = _aplicar_parametros_modo(condiciones, parametros, modo, id_profesional)

        cursor.execute(
            f"""
            SELECT
                s.id AS solicitud_id,
                s.id_interno,
                s.tipo,
                s.motivo,
                s.descripcion,
                s.urgencia,
                s.fecha_creacion,
                s.fecha_inicio,
                s.fecha_fin,
                s.hora_salida,
                s.hora_llegada,
                s.destino,
                s.provincia,
                s.direccion,
                s.cod_pos,
                s.nombre_cp,
                s.telf_cp,
                s.relacion_cp,
                s.direccion_cp,
                s.nombre_cs,
                s.telf_cs,
                s.relacion_cs,
                s.docs,
                s.compromiso,
                s.observaciones,
                s.conclusiones_profesional,
                s.id_profesional,
                s.estado,
                i.num_rc,
                u.id AS interno_usuario_id,
                u.nombre AS interno_nombre,
                u.email AS interno_email,
                u.contrasena AS interno_contrasena,
                u.rol AS interno_rol,
                i.situacion_legal,
                i.delito,
                i.condena,
                i.fecha_nac,
                i.fecha_ingreso,
                i.modulo,
                i.lugar_nacimiento,
                i.nombre_contacto_emergencia,
                i.relacion_contacto_emergencia,
                i.numero_contacto_emergencia,
                e.id AS entrevista_id,
                e.fecha AS entrevista_fecha,
                e.puntuacion_ia AS entrevista_puntuacion_ia,
                e.puntuacion_profesional AS entrevista_puntuacion_profesional,
                e.estado_evaluacion_ia AS entrevista_estado_evaluacion_ia
            FROM solicitudes s
            LEFT JOIN internos i ON i.num_rc = s.id_interno
            LEFT JOIN usuarios u ON u.id = i.id_usuario
            LEFT JOIN (
                SELECT DISTINCT ON (id_solicitud)
                    id,
                    id_solicitud,
                    fecha,
                    puntuacion_ia,
                    puntuacion_profesional,
                    estado_evaluacion_ia
                FROM entrevistas
                ORDER BY id_solicitud, id DESC
            ) e ON e.id_solicitud = s.id
            WHERE {where_sql}
            ORDER BY s.fecha_creacion DESC, s.id_interno ASC, s.id DESC
            LIMIT %s OFFSET %s
            """,
            (*parametros, int(limit or 10), int(offset or 0)),
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def contar_solicitudes_resumen_staff(modo, id_profesional=None, busqueda=None, estado=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        condiciones, parametros = _query_resumen_staff_base(modo)

        estado_normalizado = _normalizar_estado_combo(estado)
        if estado_normalizado == "completadas":
            condiciones.append("s.estado IN ('aceptada', 'rechazada', 'cancelada')")
        elif estado_normalizado:
            condiciones.append("s.estado = %s")
            parametros.append(estado_normalizado)

        texto_busqueda = str(busqueda or "").strip().lower()
        if texto_busqueda:
            patron = f"%{texto_busqueda}%"
            condiciones.append("(LOWER(u.nombre) LIKE %s OR CAST(i.num_rc AS TEXT) LIKE %s)")
            parametros.extend([patron, patron])

        where_sql, parametros = _aplicar_parametros_modo(condiciones, parametros, modo, id_profesional)

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM solicitudes s
            LEFT JOIN internos i ON i.num_rc = s.id_interno
            LEFT JOIN usuarios u ON u.id = i.id_usuario
            WHERE {where_sql}
            """,
            tuple(parametros),
        )
        resultado = cursor.fetchone()
        return resultado[0] if resultado else 0
    finally:
        conexion.close()


def borrar_solicitudes():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DROP TABLE IF EXISTS solicitudes")
    conexion.commit()
    conexion.close()


def actualizar_estado_solicitud(id_solicitud, estado):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE solicitudes
            SET estado = %s
            WHERE id = %s
            """,
            (estado, id_solicitud),
        )
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error: No se ha podido crear la solicitud. {e}")
        return False
    finally:
        conexion.close()


def actualizar_estado_y_conclusiones_solicitud(id_solicitud, estado, conclusiones_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE solicitudes
            SET estado = %s, conclusiones_profesional = %s
            WHERE id = %s
            """,
            (estado, conclusiones_profesional, id_solicitud),
        )
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error: No se ha podido actualizar la solicitud. {e}")
        return False
    finally:
        conexion.close()


def asignar_profesional_a_solicitud(id_solicitud, id_profesional):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE solicitudes
            SET id_profesional = %s
            WHERE id = %s
              AND id_profesional IS NULL
            """,
            (id_profesional, id_solicitud),
        )
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al asignar profesional a solicitud: {e}")
        return False
    finally:
        conexion.close()


def obtener_estado_solicitud(id_solicitud):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT estado
            FROM solicitudes
            WHERE id = %s
            """,
            (id_solicitud,),
        )
        estado = cursor.fetchone()
        conexion.commit()
        return estado
    except Exception:
        return None
    finally:
        conexion.close()
