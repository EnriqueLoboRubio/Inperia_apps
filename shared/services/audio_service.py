from utils.inperiaudio_client import AudioApiError, InperiaAudioClient


class AudioService:
    def __init__(self, email, password, session_key, base_url=None, timeout=20):
        self._client = None
        self._error = None
        try:
            self._client = InperiaAudioClient(
                email=email,
                password=password,
                session_key=session_key,
                base_url=base_url,
                timeout=timeout,
            )
        except AudioApiError as exc:
            self._client = None
            self._error = str(exc)

    @property
    def available(self):
        return self._client is not None

    @property
    def error_message(self):
        return self._error

    def ensure_audio_local(self, id_respuesta):
        if not id_respuesta:
            raise AudioApiError("No hay respuesta asociada al audio.")
        if self._client is None:
            raise AudioApiError(self._error or "La API de audio no está disponible en esta sesión.")
        return self._client.ensure_audio_local(id_respuesta)

    def upload_audio(self, id_respuesta, file_path):
        if self._client is None:
            raise AudioApiError(self._error or "La API de audio no está disponible en esta sesión.")
        return self._client.upload_audio(id_respuesta, file_path)

    def cleanup(self):
        if self._client is not None:
            self._client.cleanup()
