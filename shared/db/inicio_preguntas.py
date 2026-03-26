import json

from db.conexion import obtener_conexion
from utils.runtime_paths import shared_data_file


RUTA_PREGUNTAS_JSON = shared_data_file("preguntas.json")

def _cargar_preguntas_desde_json(ruta_json=RUTA_PREGUNTAS_JSON):
    with open(ruta_json, "r", encoding="utf-8") as archivo:
        data = json.load(archivo)

    preguntas = []
    for clave, contenido in data.items():
        if not str(clave).isdigit():
            continue
        id_pregunta = int(clave)
        titulo = str(contenido.get("titulo", f"Pregunta {id_pregunta}"))
        texto = str(contenido.get("texto", ""))
        ayuda = str(contenido.get("ayuda", ""))
        cantidad_niveles = int(contenido.get("cantidad_niveles", 0) or 0)
        preguntas.append((id_pregunta, titulo, texto, ayuda, cantidad_niveles))
    return preguntas


def iniciar_preguntas_seed(force=False):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM preguntas")
    total = cursor.fetchone()[0]

    if total > 0 and not force:
        conexion.close()
        return 0

    preguntas = _cargar_preguntas_desde_json()

    cursor.executemany(
        """
        INSERT INTO preguntas (id, titulo, texto, ayuda, cantidad_niveles)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT(id) DO UPDATE SET
            titulo = EXCLUDED.titulo,
            texto = EXCLUDED.texto,
            ayuda = EXCLUDED.ayuda,
            cantidad_niveles = EXCLUDED.cantidad_niveles
        """,
        preguntas,
    )

    conexion.commit()
    conexion.close()
    return len(preguntas)
