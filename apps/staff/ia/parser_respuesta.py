import json
import re


def _extraer_json(texto):
    contenido = str(texto or "").strip()
    if not contenido:
        raise ValueError("La respuesta de la IA está vacía.")

    if contenido.startswith("```"):
        lineas = contenido.splitlines()
        if len(lineas) >= 3:
            contenido = "\n".join(lineas[1:-1]).strip()

    inicio = contenido.find("{")
    fin = contenido.rfind("}")
    if inicio >= 0 and fin > inicio:
        candidato = contenido[inicio : fin + 1]
    else:
        candidato = contenido

    try:
        return json.loads(candidato)
    except json.JSONDecodeError:
        candidato = (
            candidato.replace("ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ", '"')
            .replace("ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â", '"')
            .replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢", "'")
            .replace("Ã¢â‚¬Å“", '"')
            .replace("Ã¢â‚¬Â", '"')
            .replace("Ã¢â‚¬â„¢", "'")
        )
        candidato = re.sub(r",\s*}", "}", candidato)
        return json.loads(candidato)


def parsear_respuesta_ia(texto):
    data = _extraer_json(texto)

    if "nivel" not in data:
        raise ValueError("La IA no devolvió el campo 'nivel'.")

    try:
        nivel = int(data.get("nivel"))
    except (TypeError, ValueError) as exc:
        raise ValueError("El nivel devuelto por la IA no es válido.") from exc

    justificacion = str(
        data.get("justificacion", data.get("analisis", data.get("conclusion", ""))) or ""
    ).strip()
    if not justificacion:
        raise ValueError("La IA no devolvio justificación o análisis.")

    return {
        "nivel": nivel,
        "justificacion": justificacion,
    }


def parsear_causas_principales_ia(texto):
    data = _extraer_json(texto)
    causas = data.get("causas")
    if not isinstance(causas, list):
        raise ValueError("La IA no devolvió la lista 'causas'.")

    causas_limpias = []
    for causa in causas:
        texto_causa = str(causa or "").strip()
        if texto_causa:
            causas_limpias.append(texto_causa)

    if len(causas_limpias) < 2:
        raise ValueError("La IA no devolvió suficientes causas principales.")

    return {"causas": causas_limpias[:4]}
