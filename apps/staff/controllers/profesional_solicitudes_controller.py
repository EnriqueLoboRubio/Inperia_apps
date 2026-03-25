import os

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import QDialog, QFileDialog

from db.solicitud_db import (
    actualizar_estado_y_conclusiones_solicitud,
    asignar_profesional_a_solicitud,
    contar_solicitudes_resumen_staff,
    listar_solicitudes_resumen_staff,
)
from gui.ventana_finalizar_solicitud_profesional import VentanaFinalizarSolicitudProfesional
from models.entrevista import Entrevista
from models.interno import Interno
from models.solicitud import Solicitud
from utils.documentoPDF import DocumentoPDF
from utils.enums import Tipo_estado_solicitud


class ProfesionalSolicitudesController:
    """
    Controlador para la gestion de las solicitudes.
    """

    def __init__(self, controlador):
        self.controlador = controlador

    def mostrar_lista_nuevas(self):
        self.controlador._modo_lista_actual = "nuevas"
        self._mostrar_lista_solicitudes("nuevas", "Todos", True)

    def mostrar_lista_pendientes(self):
        if not self.controlador.profesional:
            return

        self.controlador._modo_lista_actual = "pendientes"
        self._mostrar_lista_solicitudes("por_evaluar", "Todos", False)

    def mostrar_lista_historial(self):
        if not self.controlador.profesional:
            return

        self.controlador._modo_lista_actual = "historial"
        self._mostrar_lista_solicitudes(None, "Todos", False)

    def mostrar_lista_completadas(self):
        if not self.controlador.profesional:
            return

        self.controlador._modo_lista_actual = "completadas"
        self._mostrar_lista_solicitudes("completadas", "Todos", False)

    def gestionar_filtro_superior_lista(self, top_activo):
        if top_activo == "nuevas":
            self.mostrar_lista_nuevas()
        elif top_activo == "por_evaluar":
            self.mostrar_lista_pendientes()
        elif top_activo == "completadas":
            self.mostrar_lista_completadas()
        else:
            self._recargar_desde_estado_pantalla()

    def on_filtros_lista_cambiados(self):
        self._recargar_desde_estado_pantalla()

    def on_solicitar_mas_lista(self):
        self._cargar_pagina_solicitudes(reiniciar=False)

    def asignar_solicitud_a_profesional(self, solicitud):
        if not self.controlador.profesional or not solicitud:
            return

        id_solicitud = getattr(solicitud, "id_solicitud", None)
        if id_solicitud is None:
            self.controlador.msg.mostrar_advertencia("Atencion", "No se pudo identificar la solicitud.")
            return

        ok = asignar_profesional_a_solicitud(id_solicitud, self.controlador.profesional.id_usuario)
        if not ok:
            self.controlador.msg.mostrar_advertencia("Atencion", "No se pudo asignar la solicitud.")
            return

        self.controlador.msg.mostrar_mensaje("Solicitud asignada", "Solicitud asignada correctamente")
        self.controlador.actualizar_inicio_profesional()
        self.recargar_lista_actual()

    def recargar_lista_actual(self):
        self._recargar_desde_estado_pantalla()

    def _mostrar_lista_solicitudes(self, top_activo, combo_texto, solo_sin_profesional):
        pantalla = self.controlador.ventana_profesional.pantalla_lista_solicitud
        pantalla.aplicar_filtro_inicial(
            top_activo=top_activo,
            combo_texto=combo_texto,
            solo_sin_profesional=solo_sin_profesional,
            modo_historial=(self.controlador._modo_lista_actual == "historial"),
        )
        self.controlador.ventana_profesional.stacked_widget.setCurrentWidget(pantalla)
        self._cargar_pagina_solicitudes(reiniciar=True)
        titulos_modo = {
            "nuevas": "Nuevas solicitudes",
            "pendientes": "Solicitudes por evaluar",
            "completadas": "Solicitudes completadas",
            "historial": "Historial de solicitudes",
        }
        self.controlador.ventana_profesional.establecer_titulo_pantalla(
            titulos_modo.get(self.controlador._modo_lista_actual, "Solicitudes")
        )

    def _recargar_desde_estado_pantalla(self):
        pantalla = self.controlador.ventana_profesional.pantalla_lista_solicitud
        if self.controlador.ventana_profesional.stacked_widget.currentWidget() != pantalla:
            return
        self._cargar_pagina_solicitudes(reiniciar=True)

    def _cargar_pagina_solicitudes(self, reiniciar):
        pantalla = self.controlador.ventana_profesional.pantalla_lista_solicitud
        if reiniciar and pantalla.esta_cargando_mas():
            return

        parametros = self._obtener_parametros_consulta_desde_estado_ui(pantalla)
        if parametros is None:
            return

        offset = 0 if reiniciar else pantalla.obtener_offset_actual()
        limit = pantalla.obtener_tam_lote()
        try:
            if reiniciar:
                total = contar_solicitudes_resumen_staff(
                    modo=parametros["modo_db"],
                    id_profesional=parametros["id_profesional"],
                    busqueda=parametros["busqueda"],
                    estado=parametros["estado"],
                )
            else:
                total = pantalla.obtener_total_disponible()

            filas = listar_solicitudes_resumen_staff(
                modo=parametros["modo_db"],
                id_profesional=parametros["id_profesional"],
                busqueda=parametros["busqueda"],
                estado=parametros["estado"],
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            pantalla.mostrar_error_carga(f"Error al cargar las solicitudes. {e}")
            return

        solicitudes = [self._construir_solicitud_resumen_desde_fila_listado(fila) for fila in filas]
        if reiniciar:
            pantalla.reemplazar_datos(solicitudes, total)
        else:
            pantalla.anadir_datos(solicitudes, total)

    def _obtener_parametros_consulta_desde_estado_ui(self, pantalla):
        modo_actual = self.controlador._modo_lista_actual
        modo_db = {
            "nuevas": "nuevas",
            "pendientes": "por_evaluar",
            "completadas": "completadas",
            "historial": "historial",
        }.get(modo_actual)
        if modo_db is None:
            return None

        return {
            "modo_db": modo_db,
            "id_profesional": getattr(getattr(self.controlador, "profesional", None), "id_usuario", None),
            "busqueda": pantalla.obtener_texto_busqueda(),
            "estado": pantalla.obtener_combo_estado(),
        }

    @staticmethod
    def _construir_solicitud_resumen_desde_fila_listado(fila):
        solicitud = Solicitud()
        solicitud.id_solicitud = fila["solicitud_id"]
        solicitud.id_interno = fila["id_interno"]
        solicitud.tipo = fila["tipo"]
        solicitud.motivo = fila["motivo"]
        solicitud.descripcion = fila["descripcion"]
        solicitud.urgencia = fila["urgencia"]
        solicitud.fecha_creacion = fila["fecha_creacion"]
        solicitud.fecha_inicio = fila["fecha_inicio"]
        solicitud.fecha_fin = fila["fecha_fin"]
        solicitud.hora_salida = fila["hora_salida"]
        solicitud.hora_llegada = fila["hora_llegada"]
        solicitud.destino = fila["destino"]
        solicitud.provincia = fila["provincia"]
        solicitud.direccion = fila["direccion"]
        solicitud.cod_pos = fila["cod_pos"]
        solicitud.nombre_cp = fila["nombre_cp"]
        solicitud.telf_cp = fila["telf_cp"]
        solicitud.relacion_cp = fila["relacion_cp"]
        solicitud.direccion_cp = fila["direccion_cp"]
        solicitud.nombre_cs = fila["nombre_cs"]
        solicitud.telf_cs = fila["telf_cs"]
        solicitud.relacion_cs = fila["relacion_cs"]
        solicitud.docs = fila["docs"]
        solicitud.compromisos = fila["compromiso"]
        solicitud.observaciones = fila["observaciones"]
        solicitud.conclusiones_profesional = fila["conclusiones_profesional"]
        solicitud.id_profesional = fila["id_profesional"]
        solicitud.estado = fila["estado"]
        solicitud.interno = Interno(
            id_usuario=fila["interno_usuario_id"],
            nombre=fila["interno_nombre"],
            email=fila["interno_email"],
            contrasena=fila["interno_contrasena"],
            rol=fila["interno_rol"],
            num_RC=fila["num_rc"],
            situacion_legal=fila["situacion_legal"],
            delito=fila["delito"],
            fecha_nac=fila["fecha_nac"],
            condena=fila["condena"],
            fecha_ingreso=fila["fecha_ingreso"],
            modulo=fila["modulo"],
            lugar_nacimiento=fila["lugar_nacimiento"],
            nombre_contacto_emergencia=fila["nombre_contacto_emergencia"],
            relacion_contacto_emergencia=fila["relacion_contacto_emergencia"],
            numero_contacto_emergencia=fila["numero_contacto_emergencia"],
        )

        entrevista_id = fila["entrevista_id"]
        if entrevista_id is not None:
            entrevista = Entrevista(
                id_entrevista=entrevista_id,
                id_interno=fila["id_interno"],
                fecha=fila["entrevista_fecha"],
            )
            entrevista.puntuacion_ia = fila["entrevista_puntuacion_ia"]
            entrevista.puntuacion_profesional = fila["entrevista_puntuacion_profesional"]
            entrevista.estado_evaluacion_ia = fila["entrevista_estado_evaluacion_ia"] or "sin evaluacion"
            solicitud.entrevista = entrevista

        return solicitud

    def mostrar_detalle_solicitud(self, solicitud):
        return self._mostrar_detalle_solicitud(solicitud, solo_lectura=False)

    def mostrar_solicitud_desde_perfil_interno(self, id_solicitud):
        pantalla_perfil = self.controlador.ventana_profesional.pantalla_perfil_interno
        solicitudes = list(getattr(pantalla_perfil, "_solicitudes_actuales", []) or [])
        solicitud = None
        for fila in solicitudes:
            try:
                if int(fila[0]) == int(id_solicitud):
                    solicitud = self._construir_solicitud_desde_fila(fila)
                    break
            except (TypeError, ValueError, IndexError):
                continue

        if solicitud is None:
            self.controlador.msg.mostrar_advertencia("Atención", "No se pudo cargar la solicitud seleccionada.")
            return

        return self._mostrar_detalle_solicitud(solicitud, solo_lectura=True)

    def _mostrar_detalle_solicitud(self, solicitud, solo_lectura=False):
        if solicitud is None:
            return

        self.controlador._vista_origen_detalle_solicitud = self.controlador.ventana_profesional.stacked_widget.currentWidget()
        self.controlador._titulo_origen_detalle_solicitud = self.controlador.ventana_profesional.titulo_pantalla.text()
        self.controlador._detalle_solicitud_solo_lectura = bool(solo_lectura)

        interno = self.controlador.internos._obtener_interno_de_solicitud(solicitud)
        if interno is None:
            self.controlador.msg.mostrar_advertencia("Atención", "No se encontró la información del interno.")
            return

        pantalla = self.controlador.ventana_profesional.pantalla_detalle_solicitud
        pantalla.cargar_datos(solicitud, interno)
        self._configurar_acciones_detalle(pantalla, solicitud)
        pantalla.set_modo_solo_lectura(solo_lectura)
        self.controlador.ventana_profesional.stacked_widget.setCurrentWidget(pantalla)
        self.controlador.ventana_profesional.establecer_titulo_pantalla("Solicitud")

    def finalizar_solicitud_desde_detalle(self):
        pantalla = self.controlador.ventana_profesional.pantalla_detalle_solicitud
        solicitud = getattr(pantalla, "_solicitud", None)
        interno = getattr(pantalla, "_interno", None)
        if solicitud is None:
            self.controlador.msg.mostrar_advertencia("Atención", "No hay solicitud cargada para finalizar.")
            return

        puede_finalizar, motivo = self._puede_finalizar_o_descargar(solicitud)
        if not puede_finalizar:
            self.controlador.msg.mostrar_advertencia("Atención", motivo)
            return

        ventana = VentanaFinalizarSolicitudProfesional(
            solicitud=solicitud,
            parent=self.controlador.ventana_profesional,
        )
        if ventana.exec_() != QDialog.Accepted:
            return

        datos = ventana.get_datos() or {}
        estado_nuevo = str(datos.get("estado", "") or "").strip().lower()
        conclusiones = str(datos.get("conclusiones_profesional", "") or "").strip()
        if not conclusiones:
            self.controlador.msg.mostrar_advertencia("Atención", "Debe indicar una conclusión para finalizar la solicitud.")
            return

        if not self.controlador.entrevistas._tiene_evaluacion_ia(solicitud):
            confirmar = self.controlador.msg.mostrar_confirmacion(
                "Sin evaluación automática",
                "La entrevista asociada no tiene evaluación de IA.\n"
                "¿Está seguro de concluir la solicitud?\n"
                "Esta decisión es definitiva.",
            )
            if not confirmar:
                return

        ok = actualizar_estado_y_conclusiones_solicitud(
            getattr(solicitud, "id_solicitud", None),
            estado_nuevo,
            conclusiones,
        )
        if not ok:
            self.controlador.msg.mostrar_advertencia("Error BD", "No se pudo actualizar la solicitud en base de datos.")
            return

        solicitud.estado = estado_nuevo
        solicitud.conclusiones_profesional = conclusiones
        self.controlador._recargar_lista_al_salir_detalle = True
        if interno is not None:
            pantalla.cargar_datos(solicitud, interno)
            self._configurar_acciones_detalle(pantalla, solicitud)

        self.controlador.actualizar_inicio_profesional()
        self.controlador.msg.mostrar_mensaje("Verificación", "La solicitud se ha finalizado y guardado correctamente.")

    def descargar_solicitud_desde_detalle(self):
        pantalla = self.controlador.ventana_profesional.pantalla_detalle_solicitud
        solicitud = getattr(pantalla, "_solicitud", None)
        interno = getattr(pantalla, "_interno", None)
        if solicitud is None:
            self.controlador.msg.mostrar_advertencia("Atención", "No hay solicitud cargada para descargar.")
            return

        puede_descargar, motivo = self._puede_finalizar_o_descargar(solicitud)
        if not puede_descargar:
            self.controlador.msg.mostrar_advertencia("Atención", motivo)
            return

        incluir_detalles_entrevista = self.controlador.msg.mostrar_confirmacion(
            "Incluir entrevista",
            "¿Desea incluir detalles de la entrevista en el PDF?\n\n"
            "Si selecciona 'No', se generará el mismo PDF estándar del interno.",
        )

        try:
            ruta_guardado, _ = QFileDialog.getSaveFileName(
                self.controlador.ventana_profesional,
                "Guardar Solicitud",
                os.path.join(
                    QStandardPaths.writableLocation(QStandardPaths.DesktopLocation),
                    f"Solicitud_{getattr(solicitud, 'id_solicitud', '')}.pdf",
                ),
                "PDF Files (*.pdf)",
            )
            if not ruta_guardado:
                return

            DocumentoPDF.generar_pdf_solicitud(
                solicitud,
                ruta_guardado,
                interno,
                incluir_detalles_entrevista=incluir_detalles_entrevista,
            )
            self.controlador.msg.mostrar_mensaje(
                "Descarga exitosa",
                f"La solicitud se ha guardado en:\n{ruta_guardado}",
            )
        except Exception as e:
            self.controlador.msg.mostrar_advertencia(
                "Error al descargar",
                f"No se pudo guardar la solicitud:\n{str(e)}",
            )

    def volver_desde_detalle_solicitud(self):
        self.controlador._detalle_solicitud_solo_lectura = False
        if self.controlador._recargar_lista_al_salir_detalle:
            self.controlador._recargar_lista_al_salir_detalle = False
            self.recargar_lista_actual()
            return

        if self.controlador._vista_origen_detalle_solicitud is not None:
            self.controlador.ventana_profesional.stacked_widget.setCurrentWidget(self.controlador._vista_origen_detalle_solicitud)
            self.controlador.ventana_profesional.establecer_titulo_pantalla(self.controlador._titulo_origen_detalle_solicitud)
            return
        self.recargar_lista_actual()

    def _configurar_acciones_detalle(self, pantalla, solicitud):
        if self.controlador._detalle_solicitud_solo_lectura:
            pantalla.boton_finalizar.setEnabled(False)
            pantalla.boton_descargar_solicitud.setEnabled(False)
            pantalla.boton_finalizar.setToolTip("Desactivado: solicitud abierta en modo lectura.")
            pantalla.boton_descargar_solicitud.setToolTip("Desactivado: solicitud abierta en modo lectura.")
            return

        puede_operar, motivo = self._puede_finalizar_o_descargar(solicitud)
        tooltip_bloqueo = f"Desactivado: {motivo[0].lower()}{motivo[1:]}" if motivo else ""

        pantalla.boton_finalizar.setEnabled(puede_operar)
        pantalla.boton_descargar_solicitud.setEnabled(puede_operar)

        if puede_operar:
            pantalla.boton_finalizar.setToolTip("Finalizar solicitud")
            pantalla.boton_descargar_solicitud.setToolTip("Descargar solicitud")
        else:
            pantalla.boton_finalizar.setToolTip(tooltip_bloqueo)
            pantalla.boton_descargar_solicitud.setToolTip(tooltip_bloqueo)

    def _puede_finalizar_o_descargar(self, solicitud):
        id_prof_solicitud = getattr(solicitud, "id_profesional", None)
        id_prof_actual = getattr(self.controlador.profesional, "id_usuario", None)

        estado = str(getattr(solicitud, "estado", "") or "").strip().lower()
        conclusiones = str(getattr(solicitud, "conclusiones_profesional", "") or "").strip()
        estados_finales = {
            Tipo_estado_solicitud.ACEPTADA.value,
            Tipo_estado_solicitud.RECHAZADA.value,
            Tipo_estado_solicitud.CANCELADA.value,
        }
        solicitud_finalizada = estado in estados_finales and bool(conclusiones)

        if id_prof_solicitud is None:
            return False, "La solicitud y su entrevista no están asignadas a ningún profesional."

        if id_prof_solicitud != id_prof_actual:
            return False, "La solicitud y su entrevista están asignadas a otro profesional."

        if solicitud_finalizada:
            return False, "La solicitud ya ha sido finalizada."

        return True, ""

    @staticmethod
    def _construir_solicitud_desde_fila(datos_solicitud):
        solicitud = Solicitud()
        solicitud.id_solicitud = datos_solicitud[0]
        solicitud.id_interno = datos_solicitud[1]
        solicitud.tipo = datos_solicitud[2]
        solicitud.motivo = datos_solicitud[3]
        solicitud.descripcion = datos_solicitud[4]
        solicitud.urgencia = datos_solicitud[5]
        solicitud.fecha_creacion = datos_solicitud[6]
        solicitud.fecha_inicio = datos_solicitud[7]
        solicitud.fecha_fin = datos_solicitud[8]
        solicitud.hora_salida = datos_solicitud[9]
        solicitud.hora_llegada = datos_solicitud[10]
        solicitud.destino = datos_solicitud[11]
        solicitud.provincia = datos_solicitud[12]
        solicitud.direccion = datos_solicitud[13]
        solicitud.cod_pos = datos_solicitud[14]
        solicitud.nombre_cp = datos_solicitud[15]
        solicitud.telf_cp = datos_solicitud[16]
        solicitud.relacion_cp = datos_solicitud[17]
        solicitud.direccion_cp = datos_solicitud[18]
        solicitud.nombre_cs = datos_solicitud[19]
        solicitud.telf_cs = datos_solicitud[20]
        solicitud.relacion_cs = datos_solicitud[21]
        solicitud.docs = datos_solicitud[22]
        solicitud.compromisos = datos_solicitud[23]
        solicitud.observaciones = datos_solicitud[24]
        solicitud.conclusiones_profesional = datos_solicitud[25]
        solicitud.id_profesional = datos_solicitud[26]
        solicitud.estado = datos_solicitud[27]
        return solicitud
