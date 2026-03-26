from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt5.QtCore import QEvent, QTimer, Qt, QSize, pyqtSignal

from gui.estilos import *


class VentanaLoginCliente(QMainWindow):
    signal_solicitar_login = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setup_window()
        self.initUI()
        QTimer.singleShot(0, self._posicionar_texto_overlay)

    def setup_window(self):
        self.setWindowTitle("INPERIA CLIENTE")
        self.setWindowIcon(QIcon("assets:inperia.ico"))
        self.setMinimumSize(1200, 700)
        self.setWindowState(self.windowState() | Qt.WindowMaximized)

    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QHBoxLayout()
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        central.setLayout(layout_principal)

        self.izq = QLabel()
        self.izq.setPixmap(QPixmap("assets:inicio_interno.jpg"))
        self.izq.setAlignment(Qt.AlignCenter)
        self.izq.setScaledContents(True)
        self.izq.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.izq.installEventFilter(self)

        self.texto_over = QLabel("INPERIA\nCLIENTE", self.izq)
        self.texto_over.setFont(QFont("Arial", 25, QFont.Bold))
        self.texto_over.setAlignment(Qt.AlignCenter)
        self.texto_over.setFixedSize(440, 165)
        self.texto_over.setStyleSheet(
            """
            QLabel {
                color: white;
                background-color: rgba(78, 78, 78, 176);
                border: 1px solid rgba(255, 255, 255, 38);
                border-radius: 22px;
                padding: 16px 28px;
            }
            """
        )

        sombra = QGraphicsDropShadowEffect(self.texto_over)
        sombra.setBlurRadius(52)
        sombra.setOffset(0, 12)
        sombra.setColor(QColor(0, 0, 0, 130))
        self.texto_over.setGraphicsEffect(sombra)
        self._posicionar_texto_overlay()

        der = QWidget()
        layout_der = QVBoxLayout()
        layout_der.setContentsMargins(0, 0, 0, 0)
        layout_der.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        der.setLayout(layout_der)

        cabecera_icono = QWidget()
        cabecera_layout = QHBoxLayout(cabecera_icono)
        cabecera_layout.setContentsMargins(0, 0, 0, 0)
        cabecera_layout.addStretch()

        badge = QWidget()
        badge.setFixedSize(70, 70)
        badge.setStyleSheet("background-color: rgba(128, 128, 128, 0.35); border-radius: 14px;")
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(10, 10, 10, 10)
        badge_layout.setAlignment(Qt.AlignCenter)

        icono = QLabel()
        icono.setPixmap(QPixmap("assets:interno.png").scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icono.setAlignment(Qt.AlignCenter)
        badge_layout.addWidget(icono)

        cabecera_layout.addWidget(badge)
        cabecera_layout.addStretch()

        layout_der.addLayout(cabecera_layout)
        layout_der.addSpacing(200)
        layout_der.setContentsMargins(1, 1, 1, 1)

        self.input_correo = QLineEdit()
        self.input_correo.setPlaceholderText("correo@gmail.com")
        self.input_correo.setFixedHeight(40)
        self.input_correo.setStyleSheet(ESTILO_INPUT)
        self.input_correo.setFixedWidth(500)

        self.input_contrasena = QLineEdit()
        self.input_contrasena.setEchoMode(QLineEdit.Password)
        self.input_contrasena.setPlaceholderText("************")
        self.input_contrasena.setFixedHeight(40)
        self.input_contrasena.setStyleSheet(ESTILO_INPUT)
        self.input_contrasena.setFixedWidth(500)

        label_correo = QLabel("Correo")
        label_correo.setFont(QFont("Arial", 16))
        label_correo.setFixedWidth(500)
        label_contrasena = QLabel("Contraseña")
        label_contrasena.setFont(QFont("Arial", 16))
        label_contrasena.setFixedWidth(500)

        logo_inperia = QLabel()
        pixmap_logo = QPixmap("assets:inperiaNegro.png").scaled(
            220, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        logo_inperia.setPixmap(pixmap_logo)
        logo_inperia.setAlignment(Qt.AlignCenter)
        logo_inperia.setStyleSheet("background: transparent; border: none;")

        boton_entrar = QPushButton("Entrar")
        boton_entrar.setFixedHeight(50)
        boton_entrar.setFixedWidth(200)
        boton_entrar.setStyleSheet(ESTILO_BOTON_NEGRO)
        boton_entrar.setCursor(Qt.PointingHandCursor)
        boton_entrar.clicked.connect(self.click_entrar)

        formulario = QVBoxLayout()
        formulario.setSpacing(20)
        formulario.addWidget(logo_inperia, alignment=Qt.AlignCenter)
        formulario.addWidget(label_correo, alignment=Qt.AlignCenter)
        formulario.addWidget(self.input_correo, alignment=Qt.AlignCenter)
        formulario.addWidget(label_contrasena, alignment=Qt.AlignCenter)
        formulario.addWidget(self.input_contrasena, alignment=Qt.AlignCenter)
        formulario.addWidget(boton_entrar, alignment=Qt.AlignCenter)

        contenedor_formulario = QWidget()
        contenedor_formulario.setLayout(formulario)
        contenedor_formulario.setMaximumWidth(1100)
        contenedor_formulario.setMinimumWidth(1050)

        layout_der.addWidget(contenedor_formulario, alignment=Qt.AlignHCenter)
        layout_der.addStretch(1)

        layout_principal.addWidget(self.izq, 1)
        layout_principal.addWidget(der, 2)

    def _posicionar_texto_overlay(self):
        if not hasattr(self, "izq") or not hasattr(self, "texto_over"):
            return
        x = (self.izq.width() - self.texto_over.width()) // 2
        y = (self.izq.height() - self.texto_over.height()) // 2
        self.texto_over.move(max(0, x), max(0, y))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._posicionar_texto_overlay()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._posicionar_texto_overlay)
        QTimer.singleShot(60, self._posicionar_texto_overlay)

    def eventFilter(self, obj, event):
        if obj is self.izq and event.type() in (QEvent.Resize, QEvent.Show, QEvent.Move):
            QTimer.singleShot(0, self._posicionar_texto_overlay)
        return super().eventFilter(obj, event)

    def click_entrar(self):
        self.signal_solicitar_login.emit(
            self.input_correo.text().strip(),
            self.input_contrasena.text().strip(),
        )

    def mostrar_mensaje_error(self, mensaje):
        if "CRITICO" in mensaje:
            imagen = "assets:borrado.png"
            tit = "Cuenta eliminada"
            self.input_correo.clear()
            self.input_contrasena.clear()
        else:
            imagen = "assets:error.png"
            tit = "Atención"
            if "existe" in mensaje:
                self.input_correo.clear()
                self.input_contrasena.clear()

        dialogo = QDialog(self)
        dialogo.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialogo.setAttribute(Qt.WA_TranslucentBackground)

        layout_main = QVBoxLayout(dialogo)
        layout_main.setContentsMargins(0, 0, 0, 0)

        fondo = QFrame()
        fondo.setObjectName("FondoDialogo")
        fondo.setStyleSheet(ESTILO_DIALOGO_ERROR)

        layout_interno = QVBoxLayout(fondo)
        layout_interno.setContentsMargins(20, 20, 20, 20)
        layout_interno.setSpacing(5)

        layout_cabecera = QHBoxLayout()
        layout_cabecera.setSpacing(10)

        lbl_icono = QLabel()
        pixmap = QPixmap(imagen).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl_icono.setPixmap(pixmap)
        lbl_icono.setFixedSize(30, 30)
        lbl_icono.setStyleSheet("background: transparent; border: none;")

        titulo = QLabel(tit)
        titulo.setObjectName("TituloError")

        layout_cabecera.addWidget(lbl_icono)
        layout_cabecera.addWidget(titulo)
        layout_cabecera.addStretch()

        lbl_mensaje = QLabel(mensaje)
        lbl_mensaje.setObjectName("TextoError")
        lbl_mensaje.setWordWrap(True)
        lbl_mensaje.setMinimumWidth(300)

        boton = QPushButton("Ok")
        boton.setCursor(Qt.PointingHandCursor)
        boton.setStyleSheet(ESTILO_BOTON_ERROR)
        boton.clicked.connect(dialogo.accept)

        layout_boton = QHBoxLayout()
        layout_boton.addStretch()
        layout_boton.addWidget(boton)

        layout_interno.addLayout(layout_cabecera)
        layout_interno.addSpacing(5)
        layout_interno.addWidget(lbl_mensaje)
        layout_interno.addSpacing(15)
        layout_interno.addLayout(layout_boton)

        layout_main.addWidget(fondo)
        dialogo.exec_()

