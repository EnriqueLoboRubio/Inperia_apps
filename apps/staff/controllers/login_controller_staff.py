import re

from PyQt5.QtCore import QObject, pyqtSignal

from db.usuario_db import eliminar_usuario, encontrar_usuario_por_email, verificar_login
from models.usuario import Usuario


class LoginControllerStaff(QObject):
    signal_login_exitoso = pyqtSignal(object, str, str)
    signal_login_fallido = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.intentos_fallidos = 0

    @staticmethod
    def validar_formato_correo(correo):
        patron = r"^[\w\.-]+@[\w\.-]+\.\w{2,4}$"
        return re.match(patron, correo) is not None

    def procesar_login(self, correo, contrasena):
        if not correo or not contrasena:
            self.signal_login_fallido.emit("Por favor, complete todos los campos.")
            return
        if not self.validar_formato_correo(correo):
            self.signal_login_fallido.emit("Formato de correo inválido.")
            return

        datos_usuario = encontrar_usuario_por_email(correo)
        if not datos_usuario:
            self.intentos_fallidos = 0
            self.signal_login_fallido.emit("El usuario no existe.")
            return

        rol_detectado = verificar_login(correo, contrasena)
        if not rol_detectado:
            self.intentos_fallidos += 1
            intentos_restantes = 3 - self.intentos_fallidos
            if self.intentos_fallidos >= 3:
                eliminar_usuario(correo)
                self.signal_login_fallido.emit(
                    "CRITICO: Ha superado el numero máximo de intentos. La cuenta ha sido eliminada. Contacte con el administrador."
                )
                return
            self.signal_login_fallido.emit(
                f"Usuario o contraseña incorrectos. Le quedan {intentos_restantes} intentos."
            )
            return

        if rol_detectado not in {"profesional", "administrador"}:
            self.signal_login_fallido.emit("Este usuario debe acceder desde Inperia Cliente.")
            return

        self.intentos_fallidos = 0
        usuario = Usuario(
            id_usuario=datos_usuario[0],
            nombre=datos_usuario[1],
            email=datos_usuario[2],
            contrasena=datos_usuario[3],
            rol=datos_usuario[4],
        )
        self.signal_login_exitoso.emit(usuario, rol_detectado, contrasena)
