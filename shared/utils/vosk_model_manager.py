import os
import threading

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from utils.transcripcionVosk import HiloTranscripcion


class _HiloPrecargaModeloVosk(QThread):
    precarga_ok = pyqtSignal(str)
    precarga_error = pyqtSignal(str, str)

    def __init__(self, ruta_modelo, parent=None):
        super().__init__(parent)
        self.ruta_modelo = os.path.abspath(str(ruta_modelo))

    def run(self):
        try:
            if not os.path.exists(self.ruta_modelo):
                raise FileNotFoundError(f"No se encuentra el modelo en {self.ruta_modelo}")

            modelo = HiloTranscripcion.obtener_modelo(self.ruta_modelo)
            if modelo is None:
                raise RuntimeError("No se pudo cargar el modelo de reconocimiento.")

            self.precarga_ok.emit(self.ruta_modelo)
        except Exception as exc:
            self.precarga_error.emit(self.ruta_modelo, str(exc))


class GestorModeloVosk(QObject):
    estado_cambiado = pyqtSignal(str)

    def __init__(self, ruta_modelo):
        super().__init__()
        self.ruta_modelo = os.path.abspath(str(ruta_modelo))
        self._lock = threading.Lock()
        self._listo = False
        self._cargando = False
        self._ultimo_error = ""
        self._hilo_precarga = None
        self._sincronizar_con_cache()

    def _sincronizar_con_cache(self):
        if HiloTranscripcion.modelo_en_cache(self.ruta_modelo):
            self._listo = True
            self._cargando = False
            self._ultimo_error = ""

    def esta_listo(self):
        with self._lock:
            self._sincronizar_con_cache()
            return self._listo

    def esta_cargando(self):
        with self._lock:
            self._sincronizar_con_cache()
            return self._cargando

    def ultimo_error(self):
        with self._lock:
            self._sincronizar_con_cache()
            return self._ultimo_error

    def precargar_async(self):
        with self._lock:
            self._sincronizar_con_cache()
            if self._listo or self._cargando:
                return False

            self._cargando = True
            self._ultimo_error = ""

            self._hilo_precarga = _HiloPrecargaModeloVosk(self.ruta_modelo, self)
            self._hilo_precarga.precarga_ok.connect(self._on_precarga_ok)
            self._hilo_precarga.precarga_error.connect(self._on_precarga_error)
            self._hilo_precarga.finished.connect(self._on_precarga_finished)
            hilo = self._hilo_precarga

        self.estado_cambiado.emit(self.ruta_modelo)
        hilo.start()
        return True

    def _on_precarga_ok(self, ruta_modelo):
        with self._lock:
            if ruta_modelo != self.ruta_modelo:
                return
            self._listo = True
            self._cargando = False
            self._ultimo_error = ""

        self.estado_cambiado.emit(self.ruta_modelo)

    def _on_precarga_error(self, ruta_modelo, mensaje):
        with self._lock:
            if ruta_modelo != self.ruta_modelo:
                return
            self._listo = False
            self._cargando = False
            self._ultimo_error = str(mensaje or "Error desconocido al cargar el modelo.")

        self.estado_cambiado.emit(self.ruta_modelo)

    def _on_precarga_finished(self):
        with self._lock:
            if self._hilo_precarga is not None and not self._hilo_precarga.isRunning():
                self._hilo_precarga = None


_GESTORES_MODELO_VOSK = {}
_GESTORES_LOCK = threading.Lock()


def obtener_gestor_modelo_vosk(ruta_modelo):
    ruta_normalizada = os.path.abspath(str(ruta_modelo))
    with _GESTORES_LOCK:
        gestor = _GESTORES_MODELO_VOSK.get(ruta_normalizada)
        if gestor is None:
            gestor = GestorModeloVosk(ruta_normalizada)
            _GESTORES_MODELO_VOSK[ruta_normalizada] = gestor
        return gestor
