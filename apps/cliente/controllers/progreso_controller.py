import os

from PyQt5.QtCore import QObject, QStandardPaths, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

from db.solicitud_db import actualizar_estado_solicitud
from gui.mensajes import Mensajes
from utils.documentoPDF import DocumentoPDF


class ProgresoController(QObject):
    ver_entrevista_solicitud = pyqtSignal(int)
    realizar_entrevista_nueva = pyqtSignal()

    def __init__(self, vista_progreso, solicitud, interno):
        super().__init__()
        self.vista = vista_progreso
        self.solicitud = solicitud
        self.interno = interno
        self.msg = Mensajes(vista_progreso)

        self.cargar_datos()
        self.conectar_senales()

    def conectar_senales(self):
        self.vista.boton_solicitud.clicked.connect(self.descargar_solicitud)
        self.vista.boton_entrevista.clicked.connect(self.accion_boton_entrevista)
        self.vista.boton_cancelar.clicked.connect(self.cancelar_solicitud)

    def set_solicitud(self, solicitud):
        self.solicitud = solicitud
        self.cargar_datos()

    def accion_boton_entrevista(self):
        if not self.solicitud:
            return

        if self._puede_realizar_entrevista():
            self.realizar_entrevista()
            return

        self.ver_entrevista()

    def _puede_realizar_entrevista(self):
        return self.solicitud and self.solicitud.estado == "iniciada"

    def cargar_datos(self):
        self.vista.cargar_datos_solicitud(
            self.solicitud,
            self.interno.nombre,
            self.interno.num_RC,
        )
        self._actualizar_estado_botones()

    def _actualizar_estado_botones(self):
        if not self.solicitud:
            self._desactivar_botones_sin_solicitud()
            return

        self._configurar_boton_solicitud()
        self._configurar_boton_cancelar()
        self._configurar_boton_entrevista()

    def _desactivar_botones_sin_solicitud(self):
        self.vista.boton_solicitud.setEnabled(False)
        self.vista.boton_solicitud.setToolTip("Desactivado: no hay solicitud para descargar.")
        self.vista.boton_entrevista.setEnabled(False)
        self.vista.boton_entrevista.setToolTip("Desactivado: no hay solicitud asociada.")
        self.vista.boton_cancelar.setEnabled(False)
        self.vista.boton_cancelar.setToolTip("Desactivado: no hay solicitud asociada.")

    def _configurar_boton_solicitud(self):
        self.vista.boton_solicitud.setEnabled(True)
        self.vista.boton_solicitud.setToolTip("Descargar solicitud en PDF")

    def _configurar_boton_cancelar(self):
        cancelable = self.solicitud.estado not in ["aceptada", "rechazada", "cancelada"]
        self.vista.boton_cancelar.setEnabled(cancelable)
        if cancelable:
            self.vista.boton_cancelar.setToolTip("Cancelar solicitud")
            return
        self.vista.boton_cancelar.setToolTip(
            "Desactivado: la solicitud ya está finalizada y no puede cancelarse."
        )

    def _configurar_boton_entrevista(self):
        disponible = bool(self.solicitud.entrevista or self._puede_realizar_entrevista())
        self.vista.boton_entrevista.setEnabled(disponible)
        if not disponible:
            self.vista.boton_entrevista.setToolTip(
                "Desactivado: aun no hay entrevista disponible."
            )
            return

        if self._puede_realizar_entrevista():
            self.vista.boton_entrevista.setToolTip("Realizar entrevista")
            return

        self.vista.boton_entrevista.setToolTip("Ver entrevista")

    def ver_entrevista(self):
        if not self.solicitud:
            return

        if self.solicitud.entrevista and self.solicitud.entrevista.id_entrevista:
            self.ver_entrevista_solicitud.emit(self.solicitud.entrevista.id_entrevista)
            return

        self.msg.mostrar_advertencia(
            "Entrevista no disponible",
            "La entrevista aún no está disponible para visualización.",
        )

    def realizar_entrevista(self):
        if not self.solicitud:
            return
        self.realizar_entrevista_nueva.emit()

    def descargar_solicitud(self):
        if not self.solicitud:
            return

        try:
            ruta_guardado = self._solicitar_ruta_guardado_pdf()
            if not ruta_guardado:
                return

            DocumentoPDF.generar_pdf_solicitud(self.solicitud, ruta_guardado, self.interno)
            self.msg.mostrar_mensaje(
                "Descarga exitosa",
                f"La solicitud se ha guardado en:\n{ruta_guardado}",
            )
        except Exception as exc:
            self.msg.mostrar_advertencia(
                "Error al descargar",
                f"No se pudo guardar la solicitud:\n{str(exc)}",
            )

    def _solicitar_ruta_guardado_pdf(self):
        ruta_guardado, _ = QFileDialog.getSaveFileName(
            self.vista,
            "Guardar Solicitud",
            os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                f"Solicitud_{self.solicitud.id_solicitud}.pdf",
            ),
            "PDF Files (*.pdf)",
        )
        return ruta_guardado

    def cancelar_solicitud(self):
        if not self.solicitud:
            return

        confirmado = self.msg.mostrar_confirmacion(
            "Cancelar solicitud",
            "¿Desea cancelar esta solicitud?\n\nEsta acción cambiará su estado a cancelada.",
        )
        if not confirmado:
            return

        if not self._persistir_cancelacion():
            self.msg.mostrar_advertencia(
                "Actualización fallida",
                "No se pudo cancelar la solicitud en la base de datos.",
            )
            return

        self.solicitud.estado = "cancelada"
        self.cargar_datos()
        self.vista.boton_entrevista.setEnabled(False)
        self.vista.boton_entrevista.setToolTip(
            "Desactivado: la solicitud está cancelada."
        )
        self.msg.mostrar_mensaje(
            "Actualización exitosa",
            "La solicitud se ha cancelado correctamente",
        )

    def _persistir_cancelacion(self):
        return actualizar_estado_solicitud(self.solicitud.id_solicitud, "cancelada")
