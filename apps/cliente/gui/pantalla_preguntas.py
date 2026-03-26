from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QDialog, QFrame
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QTextCursor
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from datetime import datetime
import os

from utils.transcripcionVosk import HiloTranscripcion
from utils.runtime_paths import grabaciones_root, vosk_model_root
from utils.vosk_model_manager import obtener_gestor_modelo_vosk
from db.pregunta_db import obtener_preguntas_como_diccionario

from gui.estilos import *


def cargar_datos_preguntas():
    return obtener_preguntas_como_diccionario()


class PantallaPreguntas(QWidget):
    entrevista_finalizada = pyqtSignal(list, list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.PREGUNTAS_DATA = cargar_datos_preguntas()
        self.grabando = False
        self.hilo_grabacion = None
        self.texto_confirmado = ""
        self.texto_parcial = ""
        self.transcripcion_activa = False

        self.ruta_modelo_vosk = str(vosk_model_root("big"))
        self._gestor_modelo_vosk = obtener_gestor_modelo_vosk(self.ruta_modelo_vosk)
        self._gestor_modelo_vosk.estado_cambiado.connect(self._on_estado_modelo_vosk_cambiado)

        self.id_entrevista = 0
        self.carpeta_audios = str(grabaciones_root())
        os.makedirs(self.carpeta_audios, exist_ok=True)

        principal_layout = QVBoxLayout(self)
        principal_layout.setContentsMargins(0, 0, 60, 0)

        self.pregunta_widget = QWidget()
        self.pregunta_layout = QHBoxLayout(self.pregunta_widget)
        self.pregunta_layout.setAlignment(Qt.AlignCenter)

        self.boton_info = QPushButton()
        self.boton_info.setToolTip("Información sobre la pregunta")
        self.boton_info.setFixedSize(40, 40)
        self.boton_info.setIcon(QIcon("assets/info.png"))
        self.boton_info.setIconSize(QSize(30, 30))
        self.boton_info.setStyleSheet(
            """
            QPushButton { background: rgba(200, 200, 200, 0.6); border-radius: 15px; padding: 10px; }
            QPushButton:hover { background-color: rgba(128, 128, 128, 0.6); border-radius: 15px; }
            """
        )

        self.popup_ayuda = QLabel(self)
        self.popup_ayuda.setStyleSheet(
            """
            QLabel {
                background-color: #FFFFFF;
                color: #333333;
                border: 2px solid #333333;
                border-radius: 15px;
                padding: 20px;
                font-family: 'Arial';
                font-size: 20px;
                font-weight: normal;
            }
            """
        )
        self.popup_ayuda.setWordWrap(True)
        self.popup_ayuda.setFixedWidth(400)
        self.popup_ayuda.hide()
        self.boton_info.installEventFilter(self)

        self.numero_pregunta = 1

        self.titulo_pregunta = QLabel(f"Pregunta {self.numero_pregunta}:")
        self.titulo_pregunta.setFont(QFont("Arial", 18, QFont.Bold))
        self.titulo_pregunta.setAlignment(Qt.AlignLeft)

        self.pregunta_layout.addWidget(self.boton_info)
        self.pregunta_layout.setSpacing(10)
        self.pregunta_layout.addWidget(self.titulo_pregunta)

        self.lista_respuestas = [""] * len(self.PREGUNTAS_DATA)
        self.lista_audios = [""] * len(self.PREGUNTAS_DATA)

        self.texto_pregunta = QLabel()
        self.texto_pregunta.setFont(QFont("Arial", 14))
        self.texto_pregunta.setAlignment(Qt.AlignCenter)
        self.texto_pregunta.setWordWrap(True)

        self.txt_respuesta = QTextEdit()
        self.txt_respuesta.setFont(QFont("Arial", 12))
        self.txt_respuesta.setPlaceholderText("Escriba su respuesta aquí o use el micrófono...")
        self.txt_respuesta.setFixedHeight(350)
        self.txt_respuesta.setStyleSheet(
            """
            QTextEdit {
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 15px;
                background-color: #f7f7f7;
            }
            QTextEdit:hover { border: 1px solid #999; }
            QTextEdit:focus { border: 1px solid #0078d7; }
            """
        )

        self.lbl_estado_audio = QLabel("Pulse para grabar")
        self.lbl_estado_audio.setAlignment(Qt.AlignCenter)
        self.lbl_estado_audio.setFont(QFont("Arial", 10))
        self.lbl_estado_audio.setStyleSheet("color: #666;")

        self.lbl_transcripcion_parcial = QLabel("")
        self.lbl_transcripcion_parcial.setAlignment(Qt.AlignCenter)
        self.lbl_transcripcion_parcial.setFont(QFont("Arial", 10))
        self.lbl_transcripcion_parcial.setMinimumHeight(24)
        self.lbl_transcripcion_parcial.setStyleSheet("color: #666;")

        self.boton_grabar = QPushButton()
        self.boton_grabar.setFocusPolicy(Qt.NoFocus)
        self.boton_grabar.setToolTip("Grabar respuesta")
        self.boton_grabar.setFixedSize(60, 60)
        self.boton_grabar.setIcon(QIcon("assets/micro.png"))
        self.boton_grabar.setIconSize(QSize(30, 30))
        self.boton_grabar.setProperty("grabando", False)
        self.boton_grabar.setCursor(Qt.PointingHandCursor)
        self.boton_grabar.setStyleSheet(ESTILO_BOTON_GRABAR)

        self.botones_widget = QWidget()
        self.botones_layout = QHBoxLayout(self.botones_widget)
        self.botones_layout.addStretch(1)

        estilo_finalizar = ESTILO_BOTON_SIG_ATR.replace("black", "#792A24").replace(
            "rgba(71, 70, 70, 0.7)", "#C03930"
        )

        self.boton_atras = QPushButton("Atrás")
        self.boton_atras.setStyleSheet(ESTILO_BOTON_SIG_ATR)
        self.boton_atras.setFont(QFont("Arial", 12))
        self.boton_atras.setFixedSize(150, 50)
        self.boton_atras.setToolTip("Ir a la pregunta anterior")
        self.boton_atras.hide()

        self.boton_siguiente = QPushButton("Siguiente")
        self.boton_siguiente.setStyleSheet(ESTILO_BOTON_SIG_ATR)
        self.boton_siguiente.setFixedSize(150, 50)
        self.boton_siguiente.setToolTip("Ir a la siguiente pregunta")

        self.boton_finalizar = QPushButton("Finalizar")
        self.boton_finalizar.setStyleSheet(estilo_finalizar)
        self.boton_finalizar.setFont(QFont("Arial", 12))
        self.boton_finalizar.setFixedSize(150, 50)
        self.boton_finalizar.setToolTip("Finalizar entrevista")
        self.boton_finalizar.hide()

        self.botones_layout.addWidget(self.boton_atras)
        self.botones_layout.addStretch(1)
        self.botones_layout.addWidget(self.boton_siguiente)
        self.botones_layout.addWidget(self.boton_finalizar)
        self.botones_layout.addStretch(1)

        self.boton_grabar.clicked.connect(self.toggle_grabacion)

        principal_layout.addWidget(self.pregunta_widget)
        principal_layout.addSpacing(20)
        principal_layout.addWidget(self.texto_pregunta)
        principal_layout.addSpacing(10)
        principal_layout.addWidget(self.txt_respuesta)
        principal_layout.addSpacing(15)
        principal_layout.addWidget(self.lbl_estado_audio, alignment=Qt.AlignCenter)
        principal_layout.addWidget(self.lbl_transcripcion_parcial, alignment=Qt.AlignCenter)
        principal_layout.addWidget(self.boton_grabar, alignment=Qt.AlignCenter)
        principal_layout.addStretch(1)
        principal_layout.addWidget(self.botones_widget)
        principal_layout.addSpacing(20)

        self.cargar_pregunta(1)
        self._actualizar_estado_modelo_vosk()

    def _indice_actual(self):
        return self.numero_pregunta - 1

    def _iniciar_precarga_modelo(self):
        self._gestor_modelo_vosk.precargar_async()
        self._actualizar_estado_modelo_vosk()

    def _on_estado_modelo_vosk_cambiado(self, ruta_modelo):
        if os.path.abspath(str(ruta_modelo)) != os.path.abspath(self.ruta_modelo_vosk):
            return
        self._actualizar_estado_modelo_vosk()

    def _actualizar_estado_modelo_vosk(self):
        if self.grabando or self.transcripcion_activa:
            return

        if self._gestor_modelo_vosk.esta_cargando():
            self.boton_grabar.setEnabled(False)
            self.boton_grabar.setToolTip("Cargando reconocimiento de voz...")
            self.lbl_estado_audio.setText("Cargando reconocimiento de voz...")
            self.lbl_estado_audio.setStyleSheet("color: #1D4ED8; font-weight: bold;")
            return

        if self._gestor_modelo_vosk.esta_listo():
            self._aplicar_estado_idle("Reconocimiento de voz listo")
            self.lbl_estado_audio.setStyleSheet("color: #388E3C; font-weight: bold;")
            return

        error_modelo = self._gestor_modelo_vosk.ultimo_error()
        self.boton_grabar.setEnabled(True)
        self.boton_grabar.setProperty("grabando", False)
        self.boton_grabar.style().unpolish(self.boton_grabar)
        self.boton_grabar.style().polish(self.boton_grabar)
        self.boton_grabar.setIcon(QIcon("assets/micro.png"))
        self.boton_grabar.setIconSize(QSize(30, 30))
        self.boton_grabar.setToolTip("Reintentar carga del reconocimiento de voz")
        self.lbl_estado_audio.setText(
            "Error al preparar reconocimiento de voz. Pulse grabar para reintentar."
            if error_modelo
            else "Pulse para preparar reconocimiento de voz"
        )
        self.lbl_estado_audio.setStyleSheet("color: #B45309; font-weight: bold;")

    def _aplicar_estado_idle(self, mensaje="Pulse para grabar"):
        grabacion_disponible = self._gestor_modelo_vosk.esta_listo()
        self.boton_grabar.setEnabled(grabacion_disponible)
        self.boton_grabar.setProperty("grabando", False)
        self.boton_grabar.style().unpolish(self.boton_grabar)
        self.boton_grabar.style().polish(self.boton_grabar)
        self.boton_grabar.setIcon(QIcon("assets/micro.png"))
        self.boton_grabar.setIconSize(QSize(30, 30))
        self.boton_grabar.setToolTip(
            "Grabar respuesta" if grabacion_disponible else "Cargando reconocimiento de voz..."
        )

        self.boton_atras.setEnabled(True)
        self.boton_atras.setToolTip("Ir a la pregunta anterior")
        self.boton_siguiente.setEnabled(True)
        self.boton_siguiente.setToolTip("Ir a la siguiente pregunta")
        self.boton_finalizar.setEnabled(True)
        self.boton_finalizar.setToolTip("Finalizar entrevista")

        self.txt_respuesta.setReadOnly(False)
        self.txt_respuesta.setPlaceholderText("Escriba su respuesta aquí o use el micrófono...")
        self.texto_parcial = ""
        self.lbl_transcripcion_parcial.clear()
        self.lbl_estado_audio.setText(mensaje)
        self.lbl_estado_audio.setStyleSheet("color: #666;")

    def _aplicar_estado_grabando(self):
        self.boton_atras.setEnabled(False)
        self.boton_atras.setToolTip("Desactivado: no puede navegar mientras graba audio.")
        self.boton_siguiente.setEnabled(False)
        self.boton_siguiente.setToolTip("Desactivado: no puede navegar mientras graba audio.")
        self.boton_finalizar.setEnabled(False)
        self.boton_finalizar.setToolTip("Desactivado: no puede finalizar mientras graba audio.")

        self.boton_grabar.setEnabled(True)
        self.boton_grabar.setProperty("grabando", True)
        self.boton_grabar.style().unpolish(self.boton_grabar)
        self.boton_grabar.style().polish(self.boton_grabar)
        self.boton_grabar.setIcon(QIcon("assets/pausa.png"))
        self.boton_grabar.setIconSize(QSize(20, 20))

        self.txt_respuesta.setReadOnly(True)
        self.txt_respuesta.setPlaceholderText("Escuchando...")
        self.lbl_estado_audio.setText("Grabando...")
        self.lbl_estado_audio.setStyleSheet("color: #D32F2F; font-weight: bold;")
        self.lbl_transcripcion_parcial.clear()

    def _refrescar_texto_transcripcion(self):
        self.txt_respuesta.setPlainText(self.texto_confirmado)
        cursor = self.txt_respuesta.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.txt_respuesta.setTextCursor(cursor)

    def _crear_ruta_audio_pregunta(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return os.path.join(self.carpeta_audios, f"pregunta_{self.numero_pregunta}_{timestamp}.wav")

    def _iniciar_grabacion(self):
        if self.hilo_grabacion and self.hilo_grabacion.isRunning():
            return

        if not self._gestor_modelo_vosk.esta_listo():
            self._iniciar_precarga_modelo()
            return

        indice = self._indice_actual()
        ruta_existente = (self.lista_audios[indice] or "").strip()
        if ruta_existente and os.path.exists(ruta_existente):
            try:
                os.remove(ruta_existente)
            except Exception:
                pass

        ruta_audio_salida = self._crear_ruta_audio_pregunta()
        self.lista_audios[indice] = ruta_audio_salida
        self.lista_respuestas[indice] = ""

        self.texto_confirmado = ""
        self.texto_parcial = ""
        self.grabando = True
        self.transcripcion_activa = True

        self.txt_respuesta.clear()
        self.hilo_grabacion = HiloTranscripcion(self.ruta_modelo_vosk, ruta_audio_salida)
        self.hilo_grabacion.texto_signal.connect(self.actualizar_texto_final)
        self.hilo_grabacion.parcial_signal.connect(self.actualizar_texto_parcial)
        self.hilo_grabacion.error_signal.connect(self.mostrar_error_transcripcion)
        self.hilo_grabacion.start()

        self._aplicar_estado_grabando()

    def _detener_grabacion(self):
        estaba_activa = self.grabando or self.transcripcion_activa or (
            self.hilo_grabacion and self.hilo_grabacion.isRunning()
        )
        if not estaba_activa:
            return False

        self.grabando = False
        self.transcripcion_activa = False
        self.texto_parcial = ""
        self.lbl_transcripcion_parcial.clear()
        self.detener_hilo_grabacion()
        return True

    def _finalizar_grabacion_ui(self, audio_listo: bool):
        if audio_listo:
            self._aplicar_estado_idle("Audio listo")
            self.lbl_estado_audio.setStyleSheet("color: #388E3C; font-weight: bold;")
            return
        self._actualizar_estado_modelo_vosk()

    def toggle_grabacion(self):
        if not self.grabando:
            self._iniciar_grabacion()
            return

        self._detener_grabacion()
        self._finalizar_grabacion_ui(audio_listo=True)

    def actualizar_texto_final(self, texto):
        if not self.transcripcion_activa:
            return

        texto = str(texto or "").strip()
        if not texto:
            return

        if self.texto_confirmado:
            self.texto_confirmado = f"{self.texto_confirmado} {texto}".strip()
        else:
            self.texto_confirmado = texto

        self.lista_respuestas[self._indice_actual()] = self.texto_confirmado
        self._refrescar_texto_transcripcion()

    def actualizar_texto_parcial(self, parcial):
        if not self.transcripcion_activa:
            return

        parcial = str(parcial or "").strip()
        if len(parcial) > 60:
            parcial = "..." + parcial[-60:]

        self.texto_parcial = parcial
        self.lbl_transcripcion_parcial.setText(f"👂 {parcial}" if parcial else "")

    def detener_hilo_grabacion(self):
        if not self.hilo_grabacion:
            return

        hilo = self.hilo_grabacion
        try:
            hilo.detener()
            hilo.wait(250)
        except Exception:
            pass
        finally:
            if not hilo.isRunning():
                self.hilo_grabacion = None

    def detener_grabacion(self):
        self._detener_grabacion()
        self._finalizar_grabacion_ui(audio_listo=False)

    def mostrar_error_transcripcion(self, error):
        ruta_audio = self.lista_audios[self._indice_actual()]
        if ruta_audio and os.path.exists(ruta_audio):
            try:
                os.remove(ruta_audio)
            except Exception:
                pass
        self.lista_audios[self._indice_actual()] = ""
        self.lista_respuestas[self._indice_actual()] = ""
        self.texto_confirmado = ""
        self._detener_grabacion()
        self._finalizar_grabacion_ui(audio_listo=False)
        self.mostrar_validacion_error(f"Error de audio: {error}")

    def cargar_pregunta(self, numero):
        if self.grabando:
            self._detener_grabacion()
            self._finalizar_grabacion_ui(audio_listo=False)

        self.numero_pregunta = numero
        self._actualizar_estado_modelo_vosk()
        self.texto_confirmado = ""
        self.texto_parcial = ""

        datos = self.PREGUNTAS_DATA.get(
            str(numero),
            {
                "titulo": "Error",
                "texto": f"Pregunta {numero} no encontrada en el JSON.",
                "ayuda": "No hay información disponible",
            },
        )

        self.titulo_pregunta.setText(f"Pregunta {numero}")
        self.texto_pregunta.setText(datos["texto"])

        texto_ayuda = datos.get("ayuda", "Sin información adicional.")
        self.popup_ayuda.setText(texto_ayuda)
        self.popup_ayuda.adjustSize()

        respuesta_actual = self.lista_respuestas[numero - 1]
        self.txt_respuesta.setPlainText(respuesta_actual if respuesta_actual else "")

        if self.numero_pregunta > 1:
            self.boton_atras.show()
        else:
            self.boton_atras.hide()

        if self.numero_pregunta == 10:
            self.boton_siguiente.hide()
            self.boton_finalizar.show()
        else:
            self.boton_siguiente.show()
            self.boton_finalizar.hide()

    def ir_pregunta_atras(self):
        self.lista_respuestas[self._indice_actual()] = self.txt_respuesta.toPlainText()
        self.numero_pregunta -= 1
        self.restaurar_respuesta()

    def ir_pregunta_siguiente(self):
        self.lista_respuestas[self._indice_actual()] = self.txt_respuesta.toPlainText()
        self.numero_pregunta += 1
        self.restaurar_respuesta()

    def restaurar_respuesta(self):
        self.cargar_pregunta(self.numero_pregunta)

    def finalizar_entrevista(self):
        if self.grabando:
            self._detener_grabacion()
            self._finalizar_grabacion_ui(audio_listo=True)

        self.lista_respuestas[self._indice_actual()] = self.txt_respuesta.toPlainText()

        preguntas_sin_contestar = []
        for i, respuesta in enumerate(self.lista_respuestas):
            if not respuesta or respuesta.strip() == "":
                preguntas_sin_contestar.append(str(i + 1))

        if preguntas_sin_contestar:
            mensaje = (
                f"Aún faltan por contestar las siguientes preguntas: {', '.join(preguntas_sin_contestar)}.\n\n"
                "Por favor, complete todas las respuestas antes de finalizar."
            )
            self.mostrar_validacion_error(mensaje)
            return

        self.entrevista_finalizada.emit(self.lista_respuestas, self.lista_audios)

    def showEvent(self, event):
        super().showEvent(event)
        self._iniciar_precarga_modelo()

    def eventFilter(self, obj, event):
        if obj == self.boton_info:
            if event.type() == 10:
                pos = self.boton_info.mapTo(self, self.boton_info.rect().bottomRight())
                self.popup_ayuda.move(pos.x(), pos.y())
                self.popup_ayuda.raise_()
                self.popup_ayuda.show()
                return True
            if event.type() == 11:
                self.popup_ayuda.hide()
                return True
        return super().eventFilter(obj, event)

    def mostrar_validacion_error(self, mensaje):
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
        pixmap = QPixmap("assets/error.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl_icono.setPixmap(pixmap)
        lbl_icono.setFixedSize(30, 30)
        lbl_icono.setStyleSheet("background: transparent; border: none;")

        titulo = QLabel("Atención")
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
        boton.setStyleSheet(
            """
            QPushButton {
                background-color: black;
                color: white;
                border-radius: 10px;
                padding: 8px 20px;
                font-family: 'Arial';
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover { background-color: #333; }
            """
        )
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.grabando:
                self._detener_grabacion()
                self._finalizar_grabacion_ui(audio_listo=True)
            return
        super().keyPressEvent(event)
