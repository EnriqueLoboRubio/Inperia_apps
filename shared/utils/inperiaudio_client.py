import json
import mimetypes
import os
import shutil
import socket
from pathlib import Path
from urllib import error, parse, request
from uuid import uuid4

from utils.runtime_paths import app_config_candidates, audio_cache_root


class AudioApiError(RuntimeError):
    pass


class InperiaAudioClient:
    def __init__(self, email, password, session_key, base_url=None, timeout=20):
        self.base_url = self._resolve_base_url(base_url)
        self.timeout = int(timeout)
        self._token = None
        self._audio_paths = {}
        self.cache_dir = audio_cache_root() / str(session_key)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.login(email, password)

    def login(self, email, password):
        payload = parse.urlencode({
            "username": email,
            "password": password,
        }).encode("utf-8")
        data = self._request_json(
            "/auth/login",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            use_auth=False,
        )
        token = str(data.get("access_token") or "").strip()
        if not token:
            raise AudioApiError("La API de audio no devolvio un token valido.")
        self._token = token

    def get_audio_info(self, respuesta_id):
        return self._request_json(f"/audios/respuesta/{int(respuesta_id)}/info")

    def ensure_audio_local(self, respuesta_id):
        respuesta_id = int(respuesta_id)
        ruta_existente = self._audio_paths.get(respuesta_id)
        if ruta_existente and Path(ruta_existente).exists():
            return ruta_existente

        info = self.get_audio_info(respuesta_id)
        nombre_archivo = str(info.get("nombre_archivo") or "").strip()
        tipo_mime = str(info.get("tipo_mime") or "").strip()
        suffix = Path(nombre_archivo).suffix or mimetypes.guess_extension(tipo_mime) or ".bin"
        destino = self.cache_dir / f"respuesta_{respuesta_id}{suffix}"

        self._download(
            f"/audios/respuesta/{respuesta_id}/stream",
            destino,
        )
        self._audio_paths[respuesta_id] = str(destino)
        return str(destino)

    def upload_audio(self, respuesta_id, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            raise AudioApiError(f"No se encontro el archivo de audio local: {file_path}")

        boundary = f"----InperiaAudioBoundary{uuid4().hex}"
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        payload = self._build_multipart_payload(boundary, int(respuesta_id), file_path, mime_type)
        return self._request_json(
            "/audios/upload",
            data=payload,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    def cleanup(self):
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)
        self._audio_paths.clear()

    def _request_json(self, endpoint, data=None, headers=None, use_auth=True):
        respuesta = self._open(endpoint, data=data, headers=headers, use_auth=use_auth)
        try:
            body = respuesta.read().decode("utf-8")
        finally:
            respuesta.close()

        if not body:
            return {}

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise AudioApiError("La API de audio devolvio una respuesta JSON invalida.") from exc

    def _download(self, endpoint, destino):
        destino.parent.mkdir(parents=True, exist_ok=True)
        respuesta = self._open(endpoint)
        try:
            with destino.open("wb") as output_file:
                shutil.copyfileobj(respuesta, output_file)
        finally:
            respuesta.close()

    def _open(self, endpoint, data=None, headers=None, use_auth=True):
        req_headers = dict(headers or {})
        if use_auth:
            if not self._token:
                raise AudioApiError("No hay sesion autenticada en la API de audio.")
            req_headers["Authorization"] = f"Bearer {self._token}"

        req = request.Request(f"{self.base_url}{endpoint}", data=data, headers=req_headers)
        try:
            return request.urlopen(req, timeout=self.timeout)
        except error.HTTPError as exc:
            detalle = self._extract_error_detail(exc)
            raise AudioApiError(detalle) from exc
        except TimeoutError as exc:
            raise AudioApiError(
                "La API de audio ha tardado demasiado en responder. Intente de nuevo mas tarde."
            ) from exc
        except socket.timeout as exc:
            raise AudioApiError(
                "La API de audio ha tardado demasiado en responder. Intente de nuevo mas tarde."
            ) from exc
        except error.URLError as exc:
            raise AudioApiError(
                "No se pudo conectar con la API de audio. Verifique URL, puerto y que el servicio este iniciado."
            ) from exc

    @staticmethod
    def _build_multipart_payload(boundary, respuesta_id, file_path, mime_type):
        boundary_bytes = boundary.encode("utf-8")
        salto = b"\r\n"
        partes = [
            b"--" + boundary_bytes,
            b'Content-Disposition: form-data; name="respuesta_id"',
            b"",
            str(respuesta_id).encode("utf-8"),
            b"--" + boundary_bytes,
            (
                f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"'
            ).encode("utf-8"),
            f"Content-Type: {mime_type}".encode("utf-8"),
            b"",
            file_path.read_bytes(),
            b"--" + boundary_bytes + b"--",
            b"",
        ]
        return salto.join(partes)

    @staticmethod
    def _extract_error_detail(exc):
        try:
            body = exc.read().decode("utf-8")
            if body:
                data = json.loads(body)
                detail = data.get("detail")
                if detail:
                    return str(detail)
        except Exception:
            pass
        return f"Error HTTP {getattr(exc, 'code', 'desconocido')} al acceder a la API de audio."

    @staticmethod
    def _resolve_base_url(explicit_base_url=None):
        if explicit_base_url:
            return str(explicit_base_url).rstrip("/")

        for config_path in app_config_candidates():
            if config_path is None:
                continue
            config_path = Path(config_path)
            if not config_path.exists():
                continue
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                base_url = str(data.get("inperiaudio_api_url") or "").strip()
                if base_url:
                    return base_url.rstrip("/")
            except Exception:
                pass

        return str(os.getenv("INPERAUDIO_API_URL", "http://localhost:8000/api")).rstrip("/")
