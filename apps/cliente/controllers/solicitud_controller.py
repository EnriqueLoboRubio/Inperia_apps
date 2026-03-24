from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QDialog

from db.solicitud_db import agregar_solicitud
from gui.mensajes import Mensajes
from models.solicitud import Solicitud


class SolicitudController(QObject):
    solicitud_finalizada = pyqtSignal()
    paso_cambiado = pyqtSignal(int)

    def __init__(self, vista_solicitud, num_RC):
        super().__init__()
        self.vista = vista_solicitud
        self.num_RC = num_RC
        self.solicitud = Solicitud()
        self.paso_actual = 1
        self.total_pasos = 4
        self.msg = Mensajes(self.vista)
        self._capturadores_por_paso = {
            1: self.capturar_datos_paso1,
            2: self.capturar_datos_paso2,
            3: self.capturar_datos_paso3,
            4: self.capturar_datos_paso4,
        }
        self._validadores_por_paso = {
            1: self.solicitud.valida_paso1,
            2: self.solicitud.valida_paso2,
            3: self.solicitud.valida_paso3,
            4: self.solicitud.valida_paso4,
        }
        self.conectar_senales()

    def conectar_senales(self):
        self.vista.boton_siguiente.clicked.connect(self.siguiente_paso)
        self.vista.boton_anterior.clicked.connect(self.paso_anterior)

    def siguiente_paso(self):
        self.capturar_datos_paso(self.paso_actual)

        es_valido, error_mensaje = self.validar_paso_actual()
        if not es_valido:
            self.msg.mostrar_advertencia("Atención", error_mensaje)
            return False

        if self.paso_actual < self.total_pasos:
            return self._avanzar_paso()

        return self._confirmar_y_guardar_solicitud()

    def _avanzar_paso(self):
        self.paso_actual += 1
        self.vista.actualizar_ui(self.paso_actual)
        self.paso_cambiado.emit(self.paso_actual)
        return True

    def _confirmar_y_guardar_solicitud(self):
        datos = self.solicitud.get_resumen()
        confirmado = self.msg.mostrar_confirmacion_solicitud(datos)
        if confirmado != QDialog.Accepted:
            return False
        return self.guardar_solicitud()

    def paso_anterior(self):
        if self.paso_actual <= 1:
            return False

        self.paso_actual -= 1
        self.vista.actualizar_ui(self.paso_actual)
        self.paso_cambiado.emit(self.paso_actual)
        return True

    def validar_paso_actual(self):
        validacion = self._validadores_por_paso.get(self.paso_actual)
        if not validacion:
            return True, ""
        return validacion()

    def capturar_datos_paso(self, paso):
        capturador = self._capturadores_por_paso.get(paso)
        if capturador:
            capturador()

    def capturar_datos_paso1(self):
        paso_widget = self.vista.paso1
        tarjetas = [
            ("familiar", paso_widget.tarjeta_familiar),
            ("educativo", paso_widget.tarjeta_educativo),
            ("defuncion", paso_widget.tarjeta_defuncion),
            ("medico", paso_widget.tarjeta_medico),
            ("laboral", paso_widget.tarjeta_laboral),
            ("juridico", paso_widget.tarjeta_juridico),
        ]

        self.solicitud.tipo = next(
            (tipo for tipo, tarjeta in tarjetas if tarjeta.seleccionado),
            None,
        )
        self.solicitud.descripcion = paso_widget.desc_texto.toPlainText()
        self.solicitud.motivo = paso_widget.motivo_texto.text()

        if paso_widget.boton_normal.isChecked():
            self.solicitud.urgencia = "normal"
        elif paso_widget.boton_importante.isChecked():
            self.solicitud.urgencia = "importante"
        elif paso_widget.boton_urgente.isChecked():
            self.solicitud.urgencia = "urgente"
        else:
            self.solicitud.urgencia = None

    def capturar_datos_paso2(self):
        paso_widget = self.vista.paso2
        self.solicitud.fecha_inicio = paso_widget.fecha_inicio.date().toString("dd/MM/yyyy")
        self.solicitud.fecha_fin = paso_widget.fecha_fin.date().toString("dd/MM/yyyy")
        self.solicitud.hora_salida = paso_widget.hora_salida.time().toString("HH:mm")
        self.solicitud.hora_llegada = paso_widget.hora_llegada.time().toString("HH:mm")
        self.solicitud.destino = paso_widget.destino_texto.text().strip()
        self.solicitud.provincia = paso_widget.provincia_texto.text()
        self.solicitud.direccion = paso_widget.direccion_texto.text()
        self.solicitud.cod_pos = paso_widget.codigo_texto.text()

    def capturar_datos_paso3(self):
        paso_widget = self.vista.paso3
        self.solicitud.nombre_cp = paso_widget.nombre_prin_texto.text()
        self.solicitud.telf_cp = paso_widget.telefono_prin_texto.text()
        self.solicitud.relacion_cp = paso_widget.relacion_prin_combo.currentText()
        self.solicitud.direccion_cp = paso_widget.direccion_prin_texto.text()
        self.solicitud.nombre_cs = paso_widget.nombre_secun_texto.text()
        self.solicitud.telf_cs = paso_widget.telefono_secun_texto.text()
        self.solicitud.relacion_cs = paso_widget.relacion_secun_combo.currentText()

    def capturar_datos_paso4(self):
        paso_widget = self.vista.paso4
        documentos = [
            paso_widget.doc_identidad,
            paso_widget.doc_relacion,
            paso_widget.doc_invitacion,
        ]
        compromisos = [
            paso_widget.comp1,
            paso_widget.comp2,
            paso_widget.comp3,
            paso_widget.comp4,
            paso_widget.comp5,
            paso_widget.comp6,
        ]

        self.solicitud.docs = self._calcular_valor_checkboxes(documentos)
        self.solicitud.compromisos = self._calcular_valor_checkboxes(compromisos)
        self.solicitud.observaciones = paso_widget.observaciones_texto.toPlainText()

    @staticmethod
    def _calcular_valor_checkboxes(checkboxes):
        valor = 0
        for indice, checkbox in enumerate(checkboxes):
            if checkbox.isChecked():
                valor += 1 << indice
        return valor

    def ver_resumen(self):
        resumen = self.solicitud.get_resumen()
        self.vista.ver_resumen(resumen)

    def guardar_solicitud(self):
        nuevo_id = agregar_solicitud(
            id_interno=self.num_RC,
            tipo=self.solicitud.tipo,
            motivo=self.solicitud.motivo,
            descripcion=self.solicitud.descripcion,
            urgencia=self.solicitud.urgencia,
            fecha_creacion=self.solicitud.fecha_creacion,
            fecha_inicio=self.solicitud.fecha_inicio,
            fecha_fin=self.solicitud.fecha_fin,
            hora_salida=self.solicitud.hora_salida,
            hora_llegada=self.solicitud.hora_llegada,
            destino=self.solicitud.destino,
            provincia=self.solicitud.provincia,
            direccion=self.solicitud.direccion,
            cod_pos=self.solicitud.cod_pos,
            nombre_cp=self.solicitud.nombre_cp,
            telf_cp=self.solicitud.telf_cp,
            relacion_cp=self.solicitud.relacion_cp,
            direccion_cp=self.solicitud.direccion_cp,
            nombre_cs=self.solicitud.nombre_cs,
            telf_cs=self.solicitud.telf_cs,
            relacion_cs=self.solicitud.relacion_cs,
            docs=self.solicitud.docs,
            compromiso=self.solicitud.compromisos,
            observaciones=self.solicitud.observaciones,
            estado="iniciada",
        )

        if not nuevo_id:
            self.msg.mostrar_advertencia(
                "Atención",
                "No se pudo guardar la solicitud en la base de datos.",
            )
            return False

        self.solicitud.id_solicitud = nuevo_id
        self.msg.mostrar_mensaje(
            "Solicitud Creada",
            "La solicitud se ha guardado correctamente y está lista para ser procesada.",
        )
        self.solicitud_finalizada.emit()
        return True
