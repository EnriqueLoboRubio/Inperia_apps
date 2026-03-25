import re

from PyQt5.QtCore import QObject, pyqtSignal

from db.usuario_db import eliminar_usuario, encontrar_usuario_por_email, verificar_login
from models.usuario import Usuario


class LoginControllerCliente(QObject):
    signal_login_exitoso = pyqtSignal(object, str, str)
    signal_login_fallido = pyqtSignal(str)

    MAX_INTENTOS_FALLIDOS = 3

    def __init__(self):
        super().__init__()
        self.intentos_fallidos = 0

    @staticmethod
    def validar_formato_correo(correo):
        patron = r"^[\w\.-]+@[\w\.-]+\.\w{2,4}$"
        return re.match(patron, correo) is not None

    def procesar_login(self, correo, contrasena):
        correo_normalizado = self._normalizar_correo(correo)
        validacion_error = self._validar_credenciales_entrada(correo_normalizado, contrasena)
        if validacion_error:
            self.signal_login_fallido.emit(validacion_error)
            return

        datos_usuario = encontrar_usuario_por_email(correo_normalizado)
        if not datos_usuario:
            self._reiniciar_intentos()
            self.signal_login_fallido.emit("El usuario no existe.")
            return

        resultado_login = self._autenticar_usuario(correo_normalizado, contrasena, datos_usuario)
        if resultado_login["ok"] is False:
            self.signal_login_fallido.emit(resultado_login["mensaje"])
            return

        usuario_sesion = self._crear_usuario_sesion(datos_usuario)
        rol_detectado = resultado_login["rol"]
        self.signal_login_exitoso.emit(usuario_sesion, rol_detectado, contrasena)

    @staticmethod
    def _normalizar_correo(correo):
        return str(correo or "").strip().lower()

    def _validar_credenciales_entrada(self, correo, contrasena):
        if not correo or not contrasena:
            return "Por favor, complete todos los campos."
        if not self.validar_formato_correo(correo):
            return "Formato de correo inválido."
        return None

    def _autenticar_usuario(self, correo, contrasena, datos_usuario):
        rol_detectado = verificar_login(correo, contrasena)
        if not rol_detectado:
            return self._gestionar_login_invalido(correo)

        if rol_detectado != "interno":
            return {
                "ok": False,
                "mensaje": "Este usuario debe acceder desde Inperia Staff.",
            }

        rol_usuario = str(datos_usuario[4] or "").strip().lower()
        if rol_usuario != "interno":
            return {
                "ok": False,
                "mensaje": "La cuenta no pertenece a un interno.",
            }

        self._reiniciar_intentos()
        return {
            "ok": True,
            "rol": rol_detectado,
        }

    def _gestionar_login_invalido(self, correo):
        self.intentos_fallidos += 1
        intentos_restantes = self.MAX_INTENTOS_FALLIDOS - self.intentos_fallidos

        if self.intentos_fallidos >= self.MAX_INTENTOS_FALLIDOS:
            eliminar_usuario(correo)
            return {
                "ok": False,
                "mensaje": (
                    "CRITICO: Ha superado el número máximo de intentos. "
                    "La cuenta ha sido eliminada. Contacte con el administrador."
                ),
            }

        return {
            "ok": False,
            "mensaje": (
                f"Usuario o contrasena incorrectos. "
                f"Le quedan {intentos_restantes} intentos."
            ),
        }

    def _reiniciar_intentos(self):
        self.intentos_fallidos = 0

    @staticmethod
    def _crear_usuario_sesion(datos_usuario):
        return Usuario(
            id_usuario=datos_usuario[0],
            nombre=datos_usuario[1],
            email=datos_usuario[2],
            contrasena=datos_usuario[3],
            rol=datos_usuario[4],
        )
