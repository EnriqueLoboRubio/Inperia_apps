import csv
import os

from db.conexion import obtener_conexion

NULL_SENTINEL = "__NULL__"

TEXT_TYPES = {
    "text",
    "character varying",
    "character",
    "varchar",
    "char",
}

NUMERIC_AND_TEMPORAL_TYPES = {
    "smallint",
    "integer",
    "bigint",
    "numeric",
    "real",
    "double precision",
    "date",
    "time without time zone",
    "time with time zone",
    "timestamp without time zone",
    "timestamp with time zone",
}


IDENTITY_ALWAYS_TABLES = {
    "usuarios",
    "prompts",
    "solicitudes",
    "entrevistas",
    "respuestas",
    "comentarios_pre",
    "comentarios_ia_ent",
    "comentarios_entrevista_mensajes",
    "ponderaciones_riesgo",
}


def listar_tablas_exportables():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        return [fila[0] for fila in cursor.fetchall() if fila]
    finally:
        conexion.close()


def _obtener_columnas(cursor, tabla):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (tabla,),
    )
    return [fila[0] for fila in cursor.fetchall()]


def _obtener_metadata_columnas(cursor, tabla):
    cursor.execute(
        """
        SELECT column_name, is_nullable, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (tabla,),
    )
    return [
        {
            "nombre": fila[0],
            "nullable": str(fila[1]).strip().upper() == "YES",
            "tipo": str(fila[2]).strip().lower(),
        }
        for fila in cursor.fetchall()
    ]


def _obtener_columnas_identidad_always(cursor, tabla):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND is_identity = 'YES'
          AND identity_generation = 'ALWAYS'
        """,
        (tabla,),
    )
    return {fila[0] for fila in cursor.fetchall() if fila}


def _mapa_dependencias(cursor, tablas):
    dependencias = {tabla: set() for tabla in tablas}
    cursor.execute(
        """
        SELECT
            tc.table_name,
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.constraint_column_usage AS ccu
          ON tc.constraint_name = ccu.constraint_name
         AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        """
    )
    for tabla, tabla_referenciada in cursor.fetchall():
        if tabla in dependencias and tabla_referenciada in dependencias:
            dependencias[tabla].add(tabla_referenciada)
    return dependencias


def orden_topologico(tablas, dependencias):
    pendientes = {tabla: set(refs) for tabla, refs in dependencias.items()}
    resultado = []
    libres = sorted([tabla for tabla in tablas if not pendientes.get(tabla)])

    while libres:
        actual = libres.pop(0)
        resultado.append(actual)
        for tabla in tablas:
            refs = pendientes.get(tabla)
            if actual in refs:
                refs.remove(actual)
                if not refs and tabla not in resultado and tabla not in libres:
                    libres.append(tabla)
                    libres.sort()

    restantes = [tabla for tabla in tablas if tabla not in resultado]
    return resultado + sorted(restantes)


def obtener_tablas_en_orden_importacion():
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        tablas = listar_tablas_exportables()
        dependencias = _mapa_dependencias(cursor, tablas)
        return orden_topologico(tablas, dependencias)
    finally:
        conexion.close()


def exportar_base_datos_a_csv(carpeta_destino):
    if not carpeta_destino:
        raise ValueError("Debe indicar una carpeta de destino.")

    os.makedirs(carpeta_destino, exist_ok=True)
    conexion = obtener_conexion()
    resumen = []
    try:
        cursor = conexion.cursor()
        tablas = listar_tablas_exportables()
        for tabla in tablas:
            columnas = _obtener_columnas(cursor, tabla)
            ruta_csv = os.path.join(carpeta_destino, f"{tabla}.csv")
            cursor.execute(f"SELECT * FROM {tabla}")
            filas = cursor.fetchall()

            with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as archivo_csv:
                escritor = csv.writer(archivo_csv)
                escritor.writerow(columnas)
                for fila in filas:
                    escritor.writerow(
                        [NULL_SENTINEL if valor is None else valor for valor in fila]
                    )

            resumen.append({"tabla": tabla, "filas": len(filas), "ruta": ruta_csv})
        return resumen
    finally:
        conexion.close()


def importar_base_datos_desde_csv(carpeta_origen):
    if not carpeta_origen or not os.path.isdir(carpeta_origen):
        raise ValueError("La carpeta de importacion no es valida.")

    conexion = obtener_conexion()
    resumen = []
    try:
        cursor = conexion.cursor()
        tablas = obtener_tablas_en_orden_importacion()

        datos_por_tabla = {}
        for tabla in tablas:
            ruta_csv = os.path.join(carpeta_origen, f"{tabla}.csv")
            if not os.path.exists(ruta_csv):
                continue

            with open(ruta_csv, "r", newline="", encoding="utf-8-sig") as archivo_csv:
                lector = csv.reader(archivo_csv)
                try:
                    cabecera = next(lector)
                except StopIteration:
                    cabecera = []
                    filas = []
                else:
                    filas = [fila for fila in lector]

            columnas_reales = _obtener_columnas(cursor, tabla)
            if cabecera != columnas_reales:
                raise ValueError(
                    f"El CSV de la tabla '{tabla}' no coincide con la estructura actual."
                )

            datos_por_tabla[tabla] = {"columnas": cabecera, "filas": filas, "ruta": ruta_csv}

        if not datos_por_tabla:
            raise ValueError("No se ha encontrado ningun CSV valido para importar.")

        for tabla in reversed(tablas):
            if tabla in datos_por_tabla:
                cursor.execute(f'TRUNCATE TABLE "{tabla}" RESTART IDENTITY CASCADE')

        for tabla in tablas:
            if tabla not in datos_por_tabla:
                continue

            info = datos_por_tabla[tabla]
            columnas = info["columnas"]
            filas = info["filas"]
            columnas_identidad_always = _obtener_columnas_identidad_always(cursor, tabla)
            if filas:
                metadata = _obtener_metadata_columnas(cursor, tabla)
                filas_normalizadas = [
                    _normalizar_fila_csv(fila, metadata)
                    for fila in filas
                ]
                placeholders = ", ".join(["%s"] * len(columnas))
                columnas_sql = ", ".join(columnas)
                overriding = ""
                if columnas_identidad_always.intersection(columnas):
                    overriding = " OVERRIDING SYSTEM VALUE"
                cursor.executemany(
                    f"INSERT INTO {tabla} ({columnas_sql}){overriding} VALUES ({placeholders})",
                    filas_normalizadas,
                )

            for columna_identidad in columnas_identidad_always:
                cursor.execute(
                    "SELECT pg_get_serial_sequence(%s, %s)",
                    (tabla, columna_identidad),
                )
                fila_secuencia = cursor.fetchone()
                nombre_secuencia = fila_secuencia[0] if fila_secuencia else None
                if not nombre_secuencia:
                    continue

                cursor.execute(
                    f'SELECT COALESCE(MAX("{columna_identidad}"), 0) FROM "{tabla}"'
                )
                maximo_actual = cursor.fetchone()[0] or 0
                if maximo_actual > 0:
                    cursor.execute(
                        "SELECT setval(%s, %s, true)",
                        (nombre_secuencia, maximo_actual),
                    )

            resumen.append({"tabla": tabla, "filas": len(filas), "ruta": info["ruta"]})

        conexion.commit()
        return resumen
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def obtener_resumen_csv():
    from utils.app_config import get_database_settings

    database = get_database_settings()
    return {
        "base_datos": database["dbname"],
        "host": database["host"],
        "tablas": listar_tablas_exportables(),
    }


def _normalizar_fila_csv(fila, metadata):
    fila_normalizada = []
    for valor, meta in zip(fila, metadata):
        if valor == NULL_SENTINEL:
            fila_normalizada.append(None)
            continue

        if valor == "" and meta["nullable"] and meta["tipo"] in NUMERIC_AND_TEMPORAL_TYPES:
            fila_normalizada.append(None)
            continue

        fila_normalizada.append(valor)

    return fila_normalizada
