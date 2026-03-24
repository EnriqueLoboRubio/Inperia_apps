import ctypes
import sys
from pathlib import Path

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from controllers.administrador_controller import AdministradorController
from controllers.login_controller_staff import LoginControllerStaff
from controllers.profesional_controller import ProfesionalController
from db.data_seeding import ejecutar_data_seeding_inicial
from gui.login import VentanaLoginStaff
from ollama_service import OllamaService


class StaffMainController:
    def __init__(self):
        ejecutar_data_seeding_inicial()

        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Inperia.Staff")

        self.app = QApplication(sys.argv)
        self.app.aboutToQuit.connect(self._limpiar_recursos_sesion)
        self.app.setApplicationName("Inperia Staff")
        self.app.setWindowIcon(QIcon(str(self._asset_path("inperia.ico"))))

        self.splash_widget = None
        self.splash_animacion = None
        self.login_controller = None
        self.ventana_login = None
        self.controlador_profesional = None
        self.controlador_administrador = None
        self._ollama_service = OllamaService()

        self.mostrar_splash_inicio()

    @staticmethod
    def _runtime_root():
        return (
            Path(sys.executable).resolve().parent / "shared"
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parents[3] / "shared"
        )

    @classmethod
    def _asset_path(cls, filename):
        return cls._runtime_root() / "assets" / filename

    def mostrar_splash_inicio(self):
        self.splash_widget = QWidget()
        self.splash_widget.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen
        )
        self.splash_widget.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self.splash_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        etiqueta_imagen = QLabel()
        etiqueta_imagen.setPixmap(QPixmap(str(self._asset_path("inperiaBlanco.png"))))
        etiqueta_imagen.setAlignment(Qt.AlignCenter)
        layout.addWidget(etiqueta_imagen)

        self.splash_widget.setWindowOpacity(0.0)
        self.splash_widget.adjustSize()
        pantalla = QApplication.primaryScreen()
        if pantalla:
            rect_pantalla = pantalla.availableGeometry()
            x = rect_pantalla.x() + (rect_pantalla.width() - self.splash_widget.width()) // 2
            y = rect_pantalla.y() + (rect_pantalla.height() - self.splash_widget.height()) // 2
            self.splash_widget.move(x, y)
        self.splash_widget.show()

        self.splash_animacion = QPropertyAnimation(self.splash_widget, b"windowOpacity")
        self.splash_animacion.setDuration(900)
        self.splash_animacion.setStartValue(0.0)
        self.splash_animacion.setEndValue(1.0)
        self.splash_animacion.setEasingCurve(QEasingCurve.InOutQuad)
        self.splash_animacion.finished.connect(self.cerrar_splash_y_mostrar_login)
        self.splash_animacion.start()

    def cerrar_splash_y_mostrar_login(self):
        if self.splash_widget:
            self.splash_widget.close()
            self.splash_widget = None
        self.splash_animacion = None
        self.mostrar_login()

    def mostrar_login(self):
        self.login_controller = LoginControllerStaff()
        self.ventana_login = VentanaLoginStaff()
        self._aplicar_icono_ventana(self.ventana_login)
        self.ventana_login.signal_solicitar_login.connect(self.login_controller.procesar_login)
        self.login_controller.signal_login_fallido.connect(self.ventana_login.mostrar_mensaje_error)
        self.login_controller.signal_login_exitoso.connect(self.manejar_login_exitoso)
        self.ventana_login.show()

    def manejar_login_exitoso(self, usuario, rol, contrasena_plana):
        self.ventana_login.close()
        self.login_controller = None
        if rol == "profesional":
            ollama_ok = self._ollama_service.ensure_running()
            self.controlador_profesional = ProfesionalController(usuario, contrasena_plana)
            self._aplicar_icono_ventana(self.controlador_profesional.ventana_profesional)
            self.controlador_profesional.logout_signal.connect(self.regresar_login)
            if not ollama_ok:
                self.controlador_profesional.msg.mostrar_advertencia(
                    "Ollama no disponible",
                    self._ollama_service.error_message
                    or "No se pudo iniciar Ollama. Las funciones de analisis IA pueden fallar.",
                )
            return
        self.controlador_administrador = AdministradorController(usuario, contrasena_plana)
        self._aplicar_icono_ventana(self.controlador_administrador.ventana_administrador)
        self.controlador_administrador.logout_signal.connect(self.regresar_login)

    def regresar_login(self):
        if self.controlador_profesional:
            try:
                self.controlador_profesional.cerrar_recursos()
                self.controlador_profesional.logout_signal.disconnect()
                self.controlador_profesional.ventana_profesional.close()
            except Exception:
                pass
            self.controlador_profesional = None
            self._ollama_service.stop()

        if self.controlador_administrador:
            try:
                self.controlador_administrador.cerrar_recursos()
                self.controlador_administrador.logout_signal.disconnect()
                self.controlador_administrador.ventana_administrador.close()
            except Exception:
                pass
            self.controlador_administrador = None

        self.mostrar_login()

    def _limpiar_recursos_sesion(self):
        if self.controlador_profesional:
            try:
                self.controlador_profesional.cerrar_recursos()
            except Exception:
                pass
        self._ollama_service.stop()
        if self.controlador_administrador:
            try:
                self.controlador_administrador.cerrar_recursos()
            except Exception:
                pass

    def _aplicar_icono_ventana(self, ventana):
        if ventana is None:
            return
        icono = self.app.windowIcon()
        if icono.isNull():
            icono = QIcon(str(self._asset_path("inperia.ico")))
        ventana.setWindowIcon(icono)

    def ejecutar(self):
        sys.exit(self.app.exec_())



