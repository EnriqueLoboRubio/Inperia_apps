from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout, QWidget


class SpinnerCarga(QWidget):
    def __init__(self, parent=None, tam=30, puntos=8, color="#111111"):
        super().__init__(parent)
        self._paso = 0
        self._puntos = max(8, int(puntos))
        self._color = QColor(color)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._avanzar)
        self.setFixedSize(int(tam), int(tam))
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.hide()

    def start(self):
        if not self._timer.isActive():
            self._timer.start(85)
        self.show()
        self.update()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _avanzar(self):
        self._paso = (self._paso + 1) % self._puntos
        self.update()

    def paintEvent(self, _event):
        lado = min(self.width(), self.height())
        radio_orbita = (lado / 2) - 5
        radio_punto = max(2.2, lado * 0.09)
        centro = self.rect().center()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        for i in range(self._puntos):
            color = QColor(self._color)
            alpha = int(255 * ((i + 1) / self._puntos))
            color.setAlpha(alpha)

            painter.save()
            painter.translate(centro)
            painter.rotate((360 / self._puntos) * ((i + self._paso) % self._puntos))
            painter.setBrush(color)
            painter.drawEllipse(
                QRectF(
                    -radio_punto,
                    -radio_orbita - radio_punto,
                    radio_punto * 2,
                    radio_punto * 2,
                )
            )
            painter.restore()


class DialogoCarga(QDialog):
    def __init__(self, texto, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout_main = QVBoxLayout(self)
        layout_main.setContentsMargins(0, 0, 0, 0)

        tarjeta = QWidget()
        tarjeta.setStyleSheet(
            """
            QWidget {
                background-color: rgba(255, 255, 255, 245);
                border: 1px solid #d5d5d5;
                border-radius: 18px;
            }
            """
        )

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(26, 24, 26, 24)
        layout_tarjeta.setSpacing(12)

        self.spinner = SpinnerCarga(parent=tarjeta, tam=42, color="#111111")
        self.spinner.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        lbl_texto = QLabel(str(texto or "").strip())
        lbl_texto.setAlignment(Qt.AlignCenter)
        lbl_texto.setWordWrap(True)
        lbl_texto.setStyleSheet(
            """
            QLabel {
                color: #111111;
                font-family: 'Arial';
                font-size: 10pt;
                font-weight: 600;
                background: transparent;
                border: none;
            }
            """
        )

        layout_tarjeta.addWidget(self.spinner, alignment=Qt.AlignCenter)
        layout_tarjeta.addWidget(lbl_texto)
        layout_main.addWidget(tarjeta)

        self.setFixedSize(280, 150)
        self.spinner.start()

    def showEvent(self, event):
        super().showEvent(event)
        self._centrar()

    def closeEvent(self, event):
        self.spinner.stop()
        super().closeEvent(event)

    def _centrar(self):
        parent = self.parentWidget()
        if parent is not None and parent.isVisible():
            origen = parent.frameGeometry().center()
            self.move(origen.x() - self.width() // 2, origen.y() - self.height() // 2)
            return

        pantalla = QApplication.primaryScreen()
        if pantalla is None:
            return
        area = pantalla.availableGeometry()
        self.move(
            area.x() + (area.width() - self.width()) // 2,
            area.y() + (area.height() - self.height()) // 2,
        )
