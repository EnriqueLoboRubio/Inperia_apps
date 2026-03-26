import json

from db.conexion import obtener_conexion
from utils.runtime_paths import shared_data_file


def crear_pregunta():
    return None


def insertar_o_actualizar_pregunta(id_pregunta, titulo, texto, ayuda="", cantidad_niveles=0):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO preguntas (id, titulo, texto, ayuda, cantidad_niveles)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT(id) DO UPDATE SET
            titulo = EXCLUDED.titulo,
            texto = EXCLUDED.texto,
            ayuda = EXCLUDED.ayuda,
            cantidad_niveles = EXCLUDED.cantidad_niveles
        """,
        (id_pregunta, titulo, texto, ayuda, int(cantidad_niveles or 0)),
    )
    conexion.commit()
    conexion.close()


def actualizar_cantidad_niveles_pregunta(id_pregunta, cantidad_niveles):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        UPDATE preguntas
        SET cantidad_niveles = %s
        WHERE id = %s
        """,
        (int(cantidad_niveles or 0), int(id_pregunta)),
    )
    conexion.commit()
    actualizado = cursor.rowcount > 0
    conexion.close()
    return actualizado


def obtener_preguntas_como_diccionario():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, titulo, texto, ayuda, cantidad_niveles FROM preguntas ORDER BY id")
    filas = cursor.fetchall()
    conexion.close()

    if not filas:
        cargar_preguntas_desde_json()
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, titulo, texto, ayuda, cantidad_niveles FROM preguntas ORDER BY id")
        filas = cursor.fetchall()
        conexion.close()

    if not filas:
        return {"1": {"titulo": "Error", "texto": "No hay preguntas en base de datos.", "ayuda": "", "cantidad_niveles": 0}}

    preguntas = {}
    for fila in filas:
        preguntas[str(fila[0])] = {
            "titulo": fila[1],
            "texto": fila[2],
            "ayuda": fila[3] or "",
            "cantidad_niveles": int(fila[4] or 0),
        }
    return preguntas


def cargar_preguntas_desde_json(ruta_json=None):
    if ruta_json is None:
        ruta_json = shared_data_file("preguntas.json")

    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error cargando preguntas.json: {e}")
        return False

    for clave, contenido in data.items():
        try:
            id_pregunta = int(clave)
        except ValueError:
            continue

        titulo = str(contenido.get("titulo", f"Pregunta {id_pregunta}"))
        texto = str(contenido.get("texto", ""))
        ayuda = str(contenido.get("ayuda", ""))
        cantidad_niveles = int(contenido.get("cantidad_niveles", 0) or 0)
        insertar_o_actualizar_pregunta(id_pregunta, titulo, texto, ayuda, cantidad_niveles)

    return True
