import subprocess
import sys
import time
from urllib import error, request


class OllamaService:
    def __init__(self, base_url="http://127.0.0.1:11434", timeout=2, startup_timeout=15):
        self.base_url = str(base_url or "http://127.0.0.1:11434").rstrip("/")
        self.timeout = int(timeout or 2)
        self.startup_timeout = int(startup_timeout or 15)
        self._proceso = None
        self._iniciado_aqui = False
        self._error = None

    @property
    def error_message(self):
        return self._error

    def ensure_running(self):
        self._error = None
        if self.is_running():
            return True

        banderas_creacion = 0
        info_inicio = None
        if sys.platform == "win32":
            banderas_creacion = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            info_inicio = subprocess.STARTUPINFO()
            info_inicio.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            self._proceso = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=banderas_creacion,
                startupinfo=info_inicio,
            )
            self._iniciado_aqui = True
        except FileNotFoundError:
            self._error = "No se encontró el ejecutable de Ollama. Instálalo o añádelo al PATH."
            return False
        except Exception as exc:
            self._error = f"No se pudo iniciar Ollama: {exc}"
            return False

        limite = time.time() + self.startup_timeout
        while time.time() < limite:
            if self.is_running():
                return True
            if self._proceso is not None and self._proceso.poll() is not None:
                self._error = "Ollama se cerró justo después de intentar iniciarse."
                return False
            time.sleep(0.5)

        self._error = "Ollama no respondió a tiempo al iniciarse."
        return False

    def is_running(self):
        req = request.Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return 200 <= getattr(response, "status", 200) < 300
        except error.URLError:
            return False
        except Exception:
            return False

    def stop(self):
        if not self._iniciado_aqui or self._proceso is None:
            return
        if self._proceso.poll() is not None:
            return
        try:
            self._proceso.terminate()
            self._proceso.wait(timeout=5)
        except Exception:
            try:
                self._proceso.kill()
            except Exception:
                pass
        finally:
            self._proceso = None
            self._iniciado_aqui = False
