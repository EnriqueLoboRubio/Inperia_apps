from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.estilos import *


OPCIONES_COMBO_POR_TOP = {
    "por_evaluar": ["Todos", "Pendientes", "Iniciadas"],
    "completadas": ["Todos", "Aceptadas", "Canceladas", "Rechazadas"],
    "nuevas": ["Todos", "Pendientes", "Iniciadas"],
    None: ["Todos", "Nuevas", "Pendientes", "Completadas", "Aceptadas", "Rechazadas", "Canceladas"],
}

OPCIONES_COMBO_HISTORIAL = ["Todos", "Iniciadas", "Pendientes", "Aceptadas", "Rechazadas", "Canceladas"]


class TarjetaSolicitud(QFrame):
    ver_perfil_interno = pyqtSignal(object)
    ver_entrevista = pyqtSignal(object)
    ver_solicitud = pyqtSignal(object)
    asignar_solicitud = pyqtSignal(object)

    def __init__(self, solicitud, interno, parent=None):
        super().__init__(parent)
        self.solicitud = solicitud
        self.interno = interno
        self._iniciar_ui()

    def _iniciar_ui(self):
        self.setStyleSheet(
            """
            QFrame {
                background-color: #F5F5F5;
                border: 1px solid #C9C9C9;
                border-radius: 18px;
            }
            QLabel { border: none; color: black; background: transparent; }
            """
        )

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 14, 20, 10)
        layout_principal.setSpacing(10)

        cabecera = QHBoxLayout()
        cabecera.setSpacing(12)

        boton_perfil_avatar = QPushButton(self._iniciales_interno())
        boton_perfil_avatar.setCursor(Qt.PointingHandCursor)
        boton_perfil_avatar.setFixedSize(52, 52)
        boton_perfil_avatar.setStyleSheet(ESTILO_BOTON_PERFIL)
        boton_perfil_avatar.setToolTip("Ver perfil del interno")
        boton_perfil_avatar.clicked.connect(lambda _=False: self.ver_perfil_interno.emit(self.interno))
        cabecera.addWidget(boton_perfil_avatar, alignment=Qt.AlignTop)

        bloque_info = QVBoxLayout()
        bloque_info.setSpacing(4)

        fila_nombre = QHBoxLayout()
        fila_nombre.setSpacing(8)

        lbl_nombre = QLabel(self._nombre_interno())
        lbl_nombre.setStyleSheet(ESTILO_NOMBRE_INTERNO)
        lbl_nombre.setFixedWidth(300)
        fila_nombre.addWidget(lbl_nombre)

        estado_txt, estado_color = ESTADOS_SOLICITUD_COLOR.get(
            str(getattr(self.solicitud, "estado", "")).lower(),
            ("Pendiente", "#F4E29A"),
        )
        estado_txt_color = color_texto_contraste(estado_color)
        lbl_estado = QLabel(estado_txt)
        lbl_estado.setStyleSheet(
            f"""
            QLabel {{
                background-color: {estado_color};
                color: {estado_txt_color};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 10pt;
                font-weight: 500;
            }}
            """
        )
        fila_nombre.addWidget(lbl_estado, alignment=Qt.AlignVCenter)

        estado_ia_txt, estado_ia_color = self._estado_ia_visual()
        lbl_estado_ia = QLabel(f"IA: {estado_ia_txt}")
        lbl_estado_ia.setStyleSheet(f"QLabel {{ {estilo_chip_estado(estado_ia_color)} }}")
        fila_nombre.addWidget(lbl_estado_ia, alignment=Qt.AlignVCenter)
        fila_nombre.addStretch()
        bloque_info.addLayout(fila_nombre)

        lbl_num_rc = QLabel(f"RC-{self._num_rc_interno()}")
        lbl_num_rc.setStyleSheet(ESTILO_NUM_RC)
        bloque_info.addWidget(lbl_num_rc)

        fila_fecha = QHBoxLayout()
        fila_fecha.setSpacing(6)

        icono_reloj = QLabel()
        tam_icono = lbl_num_rc.fontMetrics().height()
        imagen = QPixmap("assets:reloj.png").scaled(
            tam_icono, tam_icono, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        icono_reloj.setPixmap(imagen)
        icono_reloj.setFixedSize(tam_icono, tam_icono)
        fila_fecha.addWidget(icono_reloj, alignment=Qt.AlignVCenter)

        lbl_fecha = QLabel(f"{self._fecha_creacion()}")
        lbl_fecha.setStyleSheet(ESTILO_NUM_RC)
        fila_fecha.addWidget(lbl_fecha, alignment=Qt.AlignVCenter)
        fila_fecha.addStretch()
        bloque_info.addLayout(fila_fecha)
        cabecera.addLayout(bloque_info, 1)

        botones_superior = QHBoxLayout()
        botones_superior.setSpacing(8)

        boton_entrevista = self._crear_boton_accion("Ver entrevista")
        tiene_entrevista = self._tiene_entrevista()
        boton_entrevista.setEnabled(tiene_entrevista)
        boton_entrevista.setToolTip(
            "Ver entrevista del interno" if tiene_entrevista else "Desactivado: esta solicitud aún no tiene entrevista."
        )
        if tiene_entrevista:
            boton_entrevista.clicked.connect(lambda _=False: self.ver_entrevista.emit(self.solicitud))
        botones_superior.addWidget(boton_entrevista)

        boton_solicitud = self._crear_boton_accion("Ver solicitud")
        boton_solicitud.clicked.connect(lambda _=False: self.ver_solicitud.emit(self.solicitud))
        botones_superior.addWidget(boton_solicitud)

        boton_perfil = self._crear_boton_accion("Ver perfil")
        boton_perfil.setToolTip("Ver perfil del interno")
        boton_perfil.clicked.connect(lambda _=False: self.ver_perfil_interno.emit(self.interno))
        botones_superior.addWidget(boton_perfil)
        cabecera.addLayout(botones_superior)
        layout_principal.addLayout(cabecera)

        conc_prof = self._texto_conclusion_profesional()
        if conc_prof:
            caja_eval = QFrame()
            caja_eval.setStyleSheet(
                "QFrame { background-color: #E5E5E5; border: none; border-radius: 14px; }"
            )
            eval_layout = QVBoxLayout(caja_eval)
            eval_layout.setContentsMargins(16, 12, 16, 12)
            eval_layout.setSpacing(8)

            lbl_titulo_prof = QLabel("Conclusiones del profesional:")
            lbl_titulo_prof.setStyleSheet("font-size: 12pt; font-weight: bold; color: #1A1A1A;")
            eval_layout.addWidget(lbl_titulo_prof)

            lbl_texto_prof = QLabel(conc_prof)
            lbl_texto_prof.setWordWrap(True)
            lbl_texto_prof.setStyleSheet("font-size: 11pt; color: #222222;")
            eval_layout.addWidget(lbl_texto_prof)
            layout_principal.addWidget(caja_eval)

        fila_inferior = QHBoxLayout()
        fila_inferior.addStretch()
        if self._sin_profesional_asignado():
            boton_asignar = self._crear_boton_accion("Asignar")
            boton_asignar.clicked.connect(lambda _=False: self.asignar_solicitud.emit(self.solicitud))
            fila_inferior.addWidget(boton_asignar)
        layout_principal.addLayout(fila_inferior)

    def _crear_boton_accion(self, texto):
        boton = QPushButton(texto)
        boton.setCursor(Qt.PointingHandCursor)
        boton.setFixedHeight(34)
        boton.setStyleSheet(
            ESTILO_BOTON_SOLICITUD
            + "\nQPushButton:disabled { background-color: #E0E0E0; opacity: 0.5; }"
        )
        return boton

    def _nombre_interno(self):
        return str(getattr(self.interno, "nombre", "Interno"))

    def _num_rc_interno(self):
        return str(getattr(self.interno, "num_RC", "----"))

    def _iniciales_interno(self):
        nombre = self._nombre_interno().strip()
        if not nombre:
            return "--"
        partes = [p for p in nombre.split() if p]
        if len(partes) == 1:
            return partes[0][:2].upper()
        return (partes[0][0] + partes[1][0]).upper()

    def _fecha_creacion(self):
        return str(getattr(self.solicitud, "fecha_creacion", ""))

    def _tiene_entrevista(self):
        estado = str(getattr(self.solicitud, "estado", "") or "").strip().lower()
        if estado == "iniciada":
            return False
        return getattr(self.solicitud, "entrevista", None) is not None

    def _sin_profesional_asignado(self):
        return getattr(self.solicitud, "id_profesional", None) is None

    def _texto_conclusion_profesional(self):
        return (getattr(self.solicitud, "conclusiones_profesional", "") or "").strip()

    def _estado_ia_visual(self):
        entrevista = getattr(self.solicitud, "entrevista", None)
        if entrevista is None:
            return obtener_estado_ia_visual("Sin evaluación")
        return obtener_estado_ia_visual(getattr(entrevista, "estado_evaluacion_ia", "Sin evaluación"))


class PantallaListaSolicitud(QWidget):
    ver_perfil_interno = pyqtSignal(object)
    ver_entrevista = pyqtSignal(object)
    ver_solicitud = pyqtSignal(object)
    asignar_solicitud = pyqtSignal(object)
    filtro_superior_cambiado = pyqtSignal(object)
    filtros_cambiados = pyqtSignal()
    solicitar_mas = pyqtSignal()
    volver = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._items_cargados = []
        self._botones_top = {}
        self._top_activo = None
        self._sincronizando_filtros = False
        self._modo_historial = False
        self._filtros_superiores_visibles = True
        self._tam_lote = 10
        self._offset_actual = 0
        self._total_disponible = 0
        self._cargando_mas = False
        self._estado_lista = "ok"
        self._mensaje_estado = ""
        self._ultima_consulta = {}

        self._debounce_busqueda = QTimer(self)
        self._debounce_busqueda.setSingleShot(True)
        self._debounce_busqueda.setInterval(250)
        self._debounce_busqueda.timeout.connect(self._emitir_cambio_filtros)

        self._iniciar_ui()

    def _iniciar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(35, 20, 60, 15)
        layout_principal.setSpacing(14)

        self.layout_filtros_superiores = self._crear_fila_estados_superior()
        layout_principal.addLayout(self.layout_filtros_superiores)
        layout_principal.addLayout(self._crear_fila_filtros())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(ESTILO_SCROLL)

        self.contenedor = QWidget()
        self.layout_lista = QVBoxLayout(self.contenedor)
        self.layout_lista.setContentsMargins(0, 0, 0, 0)
        self.layout_lista.setSpacing(10)
        self.layout_lista.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.contenedor)
        self.scroll.verticalScrollBar().valueChanged.connect(self._al_scroll_lista)
        layout_principal.addWidget(self.scroll, 1)

        fila_inferior = QHBoxLayout()
        self.boton_volver = QPushButton("Volver")
        self.boton_volver.setCursor(Qt.PointingHandCursor)
        self.boton_volver.setStyleSheet(ESTILO_BOTON_SIG_ATR)
        self.boton_volver.clicked.connect(self.volver.emit)
        self.boton_volver.hide()
        fila_inferior.addWidget(self.boton_volver)
        fila_inferior.addStretch()
        layout_principal.addLayout(fila_inferior)

    def _crear_fila_estados_superior(self):
        fila = QHBoxLayout()
        fila.setSpacing(8)

        self._botones_top = {
            "por_evaluar": self._crear_boton_estado_superior("Por evaluar", "por_evaluar"),
            "completadas": self._crear_boton_estado_superior("Completadas", "completadas"),
            "nuevas": self._crear_boton_estado_superior("Nuevas", "nuevas"),
        }
        for boton in self._botones_top.values():
            fila.addWidget(boton)

        fila.addStretch()
        self._aplicar_estado_botones_superiores(None)
        return fila

    def _crear_boton_estado_superior(self, texto, clave):
        boton = QPushButton(texto)
        boton.setCursor(Qt.PointingHandCursor)
        boton.setFixedSize(150, 40)
        boton.clicked.connect(lambda _, c=clave: self._al_cambiar_filtro_superior(c))
        return boton

    def _crear_fila_filtros(self):
        fila = QHBoxLayout()
        fila.setSpacing(8)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por nombre o número de recluso ...")
        self.input_busqueda.setFixedHeight(40)
        self.input_busqueda.setStyleSheet(
            """
            QLineEdit {
                background-color: #ECECEC;
                border: 1px solid #BEBEBE;
                border-radius: 20px;
                padding: 0 16px;
                font-size: 11pt;
            }
            """
        )
        tam_icono_busqueda = self.input_busqueda.fontMetrics().height() + 3
        icono_busqueda_svg = QIcon("assets:buscar.svg")
        icono_busqueda = QIcon(icono_busqueda_svg.pixmap(tam_icono_busqueda, tam_icono_busqueda))
        self.input_busqueda.addAction(icono_busqueda, QLineEdit.LeadingPosition)
        self.input_busqueda.textChanged.connect(self._al_cambiar_texto_busqueda)

        self.combo_estado = QComboBox()
        self.combo_estado.setFixedSize(210, 40)
        self.combo_estado.addItems(OPCIONES_COMBO_POR_TOP[None])
        self.combo_estado.setToolTip("Filtrar por estado")
        self.combo_estado.setStyleSheet(ESTILO_COMBOBOX)
        self.combo_estado.currentTextChanged.connect(self._al_cambiar_combo_estado)

        fila.addWidget(self.input_busqueda, 1)
        fila.addWidget(self.combo_estado)
        return fila

    def cargar_datos(self, solicitudes, internos):
        self.reemplazar_datos(solicitudes, len(solicitudes or []))

    def reemplazar_datos(self, solicitudes, total_disponible):
        self._items_cargados = list(solicitudes or [])
        self._total_disponible = int(total_disponible or 0)
        self._offset_actual = len(self._items_cargados)
        self._cargando_mas = False
        self._estado_lista = "ok"
        self._mensaje_estado = ""
        self.actualizar_estado_consulta()
        self._render_lista()

    def anadir_datos(self, solicitudes, total_disponible):
        self._items_cargados.extend(list(solicitudes or []))
        self._total_disponible = int(total_disponible or 0)
        self._offset_actual = len(self._items_cargados)
        self._cargando_mas = False
        self._estado_lista = "ok"
        self._mensaje_estado = ""
        self.actualizar_estado_consulta()
        self._render_lista()

    def mostrar_error_carga(self, mensaje="Error al cargar las solicitudes. Inténtelo de nuevo."):
        self._estado_lista = "error"
        self._mensaje_estado = mensaje
        self._items_cargados = []
        self._offset_actual = 0
        self._total_disponible = 0
        self._cargando_mas = False
        self._render_lista()

    def mostrar_sin_permiso(self, mensaje="No tienes permisos para ver esta lista."):
        self._estado_lista = "sin_permiso"
        self._mensaje_estado = mensaje
        self._items_cargados = []
        self._offset_actual = 0
        self._total_disponible = 0
        self._cargando_mas = False
        self._render_lista()

    def aplicar_filtro_inicial(
        self,
        top_activo=None,
        combo_texto="Todos",
        solo_sin_profesional=False,
        modo_historial=False,
        mostrar_filtros_superiores=True,
        mostrar_boton_volver=False,
    ):
        self._top_activo = top_activo
        self._modo_historial = modo_historial
        self.set_filtros_superiores_visibles(mostrar_filtros_superiores)
        self.boton_volver.setVisible(bool(mostrar_boton_volver))
        self._aplicar_estado_botones_superiores(self._top_activo)
        self._configurar_combo_para_top(self._top_activo, combo_texto)
        self.input_busqueda.clear()
        self._emitir_cambio_filtros()

    def set_filtros_superiores_visibles(self, visible):
        self._filtros_superiores_visibles = bool(visible)
        for boton in self._botones_top.values():
            boton.setVisible(self._filtros_superiores_visibles)

    def refrescar_tarjetas(self):
        if self._estado_lista != "ok":
            return
        self._render_lista()

    def _al_cambiar_filtro_superior(self, clave):
        self._top_activo = None if self._top_activo == clave else clave
        self._aplicar_estado_botones_superiores(self._top_activo)
        self._configurar_combo_para_top(self._top_activo, "Todos")
        self.filtro_superior_cambiado.emit(self._top_activo)

    def _al_cambiar_texto_busqueda(self, _texto):
        self._debounce_busqueda.start()

    def _al_cambiar_combo_estado(self, _texto):
        if self._sincronizando_filtros:
            return
        self._emitir_cambio_filtros()

    def _emitir_cambio_filtros(self):
        self._items_cargados = []
        self._offset_actual = 0
        self._total_disponible = 0
        self._cargando_mas = False
        self.actualizar_estado_consulta()
        self.filtros_cambiados.emit()

    def _configurar_combo_para_top(self, top_activo, seleccion="Todos"):
        if top_activo is None and self._modo_historial:
            opciones = OPCIONES_COMBO_HISTORIAL
        else:
            opciones = OPCIONES_COMBO_POR_TOP.get(top_activo, OPCIONES_COMBO_POR_TOP[None])
        self._sincronizando_filtros = True
        try:
            self.combo_estado.clear()
            self.combo_estado.addItems(opciones)
            if seleccion in opciones:
                self.combo_estado.setCurrentText(seleccion)
            else:
                self.combo_estado.setCurrentIndex(0)
        finally:
            self._sincronizando_filtros = False

    def _aplicar_estado_botones_superiores(self, activo):
        for clave, boton in self._botones_top.items():
            if clave == activo:
                boton.setStyleSheet(
                    """
                    QPushButton {
                        background-color: black;
                        color: white;
                        border: 1px solid black;
                        border-radius: 10px;
                        font-size: 11pt;
                        font-weight: 600;
                    }
                    """
                )
            else:
                boton.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #F5F5F5;
                        color: black;
                        border: 1px solid #8C8C8C;
                        border-radius: 10px;
                        font-size: 11pt;
                        font-weight: 500;
                    }
                    QPushButton:hover { background-color: #EDEDED; }
                    """
                )

    def _al_scroll_lista(self, valor):
        barra = self.scroll.verticalScrollBar()
        if valor < (barra.maximum() - 80):
            return
        if self._cargando_mas or self._offset_actual >= self._total_disponible:
            return
        self._cargando_mas = True
        self.solicitar_mas.emit()

    def _limpiar_lista(self):
        while self.layout_lista.count():
            item = self.layout_lista.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_lista(self):
        self._limpiar_lista()

        if self._estado_lista == "error":
            self._mostrar_mensaje_lista(self._mensaje_estado or "Error al cargar las solicitudes.")
            return
        if self._estado_lista == "sin_permiso":
            self._mostrar_mensaje_lista(self._mensaje_estado or "No tienes permisos para ver esta lista.")
            return

        if not self._items_cargados:
            if self._ultima_consulta.get("texto_busqueda"):
                self._mostrar_mensaje_lista("No hay resultados para la busqueda actual.")
            else:
                self._mostrar_mensaje_lista("No hay solicitudes con los filtros seleccionados.")
            return

        for solicitud in self._items_cargados:
            interno = getattr(solicitud, "interno", None)
            if interno is None:
                continue
            tarjeta = TarjetaSolicitud(solicitud, interno)
            tarjeta.ver_perfil_interno.connect(self.ver_perfil_interno.emit)
            tarjeta.ver_entrevista.connect(self.ver_entrevista.emit)
            tarjeta.ver_solicitud.connect(self.ver_solicitud.emit)
            tarjeta.asignar_solicitud.connect(self.asignar_solicitud.emit)
            self.layout_lista.addWidget(tarjeta)

        if self._offset_actual < self._total_disponible:
            lbl_mas = QLabel(
                f"Mostrando {self._offset_actual} de {self._total_disponible} solicitudes. "
                "Desplaza para cargar mas."
            )
            lbl_mas.setAlignment(Qt.AlignCenter)
            lbl_mas.setStyleSheet("font-size: 10pt; color: #7A7A7A;")
            self.layout_lista.addWidget(lbl_mas)

        self.layout_lista.addStretch()

    def _mostrar_mensaje_lista(self, texto):
        lbl_vacio = QLabel(texto)
        lbl_vacio.setAlignment(Qt.AlignCenter)
        lbl_vacio.setStyleSheet("font-size: 12pt; color: #7A7A7A;")
        self.layout_lista.addWidget(lbl_vacio)
        self.layout_lista.addStretch()

    def obtener_texto_busqueda(self):
        return self.input_busqueda.text().strip()

    def obtener_combo_estado(self):
        return self.combo_estado.currentText()

    def obtener_tam_lote(self):
        return self._tam_lote

    def obtener_offset_actual(self):
        return self._offset_actual

    def obtener_total_disponible(self):
        return self._total_disponible

    def esta_cargando_mas(self):
        return self._cargando_mas

    def actualizar_estado_consulta(self):
        self._ultima_consulta = {
            "texto_busqueda": self.obtener_texto_busqueda(),
            "combo_estado": self.obtener_combo_estado(),
            "top_activo": self._top_activo,
            "modo_historial": self._modo_historial,
        }

