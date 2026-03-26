import os
import json
import wave
import threading
import pyaudio
from vosk import Model, KaldiRecognizer
from PyQt5.QtCore import QThread, pyqtSignal

class HiloTranscripcion(QThread):
    SAMPLE_RATE = 16000
    FRAMES_PER_BUFFER = 1024
    _MODELOS_CACHE = {}
    _MODELOS_LOADING = {}
    _CACHE_LOCK = threading.Lock()

    texto_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    parcial_signal = pyqtSignal(str)

    def __init__(self, ruta_modelo, archivo_salida=None):
        super().__init__()
        self.ruta_modelo = ruta_modelo
        self.archivo_salida = archivo_salida
        self.corriendo = False
        self.stream = None
        self.p = None
        self.wf = None
        self.reconocedor = None
        self._segmentos_finales = []

    @classmethod
    def obtener_modelo(cls, ruta_modelo):
        ruta_normalizada = os.path.abspath(str(ruta_modelo))
        with cls._CACHE_LOCK:
            modelo = cls._MODELOS_CACHE.get(ruta_normalizada)
            if modelo is not None:
                return modelo

            evento_carga = cls._MODELOS_LOADING.get(ruta_normalizada)
            if evento_carga is None:
                evento_carga = threading.Event()
                cls._MODELOS_LOADING[ruta_normalizada] = evento_carga
                es_cargador = True
            else:
                es_cargador = False

        if es_cargador:
            try:
                modelo = Model(ruta_normalizada)
                with cls._CACHE_LOCK:
                    cls._MODELOS_CACHE[ruta_normalizada] = modelo
                return modelo
            finally:
                with cls._CACHE_LOCK:
                    evento = cls._MODELOS_LOADING.pop(ruta_normalizada, None)
                if evento is not None:
                    evento.set()

        evento_carga.wait()
        with cls._CACHE_LOCK:
            return cls._MODELOS_CACHE.get(ruta_normalizada)

    @classmethod
    def modelo_en_cache(cls, ruta_modelo):
        ruta_normalizada = os.path.abspath(str(ruta_modelo))
        with cls._CACHE_LOCK:
            return ruta_normalizada in cls._MODELOS_CACHE

    def _registrar_segmento(self, texto):
        texto = str(texto or "").strip()
        if not texto:
            return

        if not self._segmentos_finales:
            self._segmentos_finales.append(texto)
            self.texto_signal.emit(texto)
            return

        ultimo = self._segmentos_finales[-1]
        if texto == ultimo or ultimo.startswith(texto):
            return

        if texto.startswith(ultimo):
            resto = texto[len(ultimo):].strip()
            self._segmentos_finales[-1] = texto
            if resto:
                self.texto_signal.emit(resto)
            return

        self._segmentos_finales.append(texto)
        self.texto_signal.emit(texto)

    def run(self):

        if not os.path.exists(self.ruta_modelo):
            self.error_signal.emit(f"No se encuentra el modelo en {self.ruta_modelo}")
            return

        try:
            modelo = self.obtener_modelo(self.ruta_modelo)
            self.reconocedor = KaldiRecognizer(modelo, self.SAMPLE_RATE)
            self._segmentos_finales = []

            self.p = pyaudio.PyAudio()

            if self.archivo_salida:
                # Aseguramos que se crea correctamente
                try:
                    self.wf = wave.open(self.archivo_salida, "wb")
                    self.wf.setnchannels(1)
                    self.wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                    self.wf.setframerate(self.SAMPLE_RATE)
                except Exception as e:
                    self.error_signal.emit(f"Error al crear archivo de audio: {e}")
                    return

            self.corriendo = True

            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.FRAMES_PER_BUFFER
            )

            self.stream.start_stream()

            while self.corriendo:
                try:
                    in_data = self.stream.read(self.FRAMES_PER_BUFFER, exception_on_overflow=False)
                except Exception as e:
                    self.error_signal.emit(f"Error al capturar audio: {e}")
                    break

                if not in_data:
                    continue

                if self.wf is not None:
                    try:
                        self.wf.writeframes(in_data)
                    except Exception:
                        pass

                if self.reconocedor.AcceptWaveform(in_data):
                    resultado = json.loads(self.reconocedor.Result())
                    texto = resultado.get("text", "")
                    if texto:
                        self._registrar_segmento(texto)
                else:
                    parcial = json.loads(self.reconocedor.PartialResult())
                    texto_parcial = parcial.get("partial", "")
                    if texto_parcial:
                        self.parcial_signal.emit(texto_parcial)

            if self.reconocedor:
                final_json = json.loads(self.reconocedor.FinalResult())
                texto_final = final_json.get("text", "")
                self._registrar_segmento(texto_final)

        except Exception as e:
            self.error_signal.emit(f"Error crítico: {str(e)}")

        finally:
            self.limpiar()

    def detener(self):
        self.corriendo = False

    def limpiar(self):

        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if self.wf:
            try:
                self.wf.close()
            except Exception:
                pass
            self.wf = None

        if self.p:
            try:
                self.p.terminate()
            except Exception:
                pass
            self.p = None
