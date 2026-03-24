import os
import shutil
from datetime import date
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QDialog

from controllers.progreso_controller import ProgresoController
from controllers.solicitud_controller import SolicitudController
from db.entrevista_db import agregar_entrevista_y_respuestas, encontrar_entrevista_por_solicitud
from db.interno_db import encontrar_interno_por_id
from db.respuesta_db import obtener_respuestas_por_entrevista
from db.solicitud_db import actualizar_estado_solicitud, encontrar_ultima_solicitud_por_interno
from db.usuario_db import actualizar_usuario
from gui.interno_inicio import VentanaInterno
from gui.mensajes import Mensajes
from gui.ventana_detalle_edit_pregunta_interno import VentanaDetallePreguntaEdit
from gui.ventana_detalle_pregunta_interno import VentanaDetallePregunta
from models.entrevista import Entrevista
from models.interno import Interno
from models.respuesta import Respuesta
from models.solicitud import Solicitud
from services.audio_service import AudioService
from utils.enums import Tipo_estado_solicitud
from utils.inperiaudio_client import AudioApiError


class InternoController(QObject):
    logout_signal = pyqtSignal()

    def __init__(self, usuario, contrasena_plana):
        super().__init__()
        self.usuario = usuario
        self._audio_client = None
        self._audio_client_error = None
        self.msg = None
        self.pregunta_mostrar = None

        self.ventana_interno = VentanaInterno()
        self._inicializar_audio_api(contrasena_plana)

        self.interno = self.cargar_interno()
        self.solicitud_actual = self.cargar_ultima_solicitud()

        self._cargar_estado_inicial_en_vista()
        self.solicitud_controller = SolicitudController(
            self.ventana_interno.pantalla_solicitud,
            self.interno.num_RC,
        )
        self.progreso_controller = ProgresoController(
            self.ventana_interno.pantalla_progreso,
            self.solicitud_actual,
            self.interno,
        )

        self._actualizar_estado_inicio()
        self.msg = Mensajes(self.ventana_interno)

        self.conectar_senales()
        self._aplicar_estado_audio_api()

    def cargar_interno(self):
        datos_interno = encontrar_interno_por_id(self.usuario.id_usuario)
        if not datos_interno:
            return None
        return self._crear_modelo_interno(datos_interno)

    def cargar_ultima_solicitud(self):
        if not self.interno:
            return None

        datos_solicitud = encontrar_ultima_solicitud_por_interno(self.interno.num_RC)
        if not datos_solicitud:
            return None

        solicitud = self._crear_modelo_solicitud(datos_solicitud)
        solicitud.entrevista = self.cargar_entrevista_solicitud(solicitud.id_solicitud)
        return solicitud

    def cargar_entrevista_solicitud(self, id_solicitud):
        datos_entrevista = encontrar_entrevista_por_solicitud(id_solicitud)
        if not datos_entrevista:
            return None

        entrevista = self._crear_modelo_entrevista(datos_entrevista)
        respuestas = obtener_respuestas_por_entrevista(entrevista.id_entrevista)
        for dato in respuestas:
            entrevista.add_respuestas(self._crear_modelo_pregunta(dato))
        return entrevista

    def _crear_modelo_interno(self, datos_interno):
        return Interno(
            id_usuario=self.usuario.id_usuario,
            nombre=self.usuario.nombre,
            email=self.usuario.email,
            contrasena=self.usuario.contrasena,
            rol=self.usuario.rol,
            num_RC=datos_interno[0],
            situacion_legal=datos_interno[2],
            delito=datos_interno[3],
            fecha_nac=datos_interno[5],
            condena=datos_interno[4],
            fecha_ingreso=datos_interno[6],
            modulo=datos_interno[7],
        )

    @staticmethod
    def _crear_modelo_solicitud(datos_solicitud):
        solicitud = Solicitud()
        solicitud.id_solicitud = datos_solicitud[0]
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

    @staticmethod
    def _crear_modelo_entrevista(datos_entrevista):
        entrevista = Entrevista(
            id_entrevista=datos_entrevista[0],
            id_interno=datos_entrevista[1],
            fecha=datos_entrevista[3],
        )
        entrevista.puntuacion_ia = datos_entrevista[4]
        entrevista.puntuacion_profesional = (
            datos_entrevista[5] if len(datos_entrevista) > 5 else -1
        )
        entrevista.estado_evaluacion_ia = (
            datos_entrevista[6] if len(datos_entrevista) > 6 else "sin evaluacion"
        )
        return entrevista

    @staticmethod
    def _crear_modelo_pregunta(datos_respuesta):
        pregunta = Respuesta(
            id_pregunta=datos_respuesta["id_pregunta"],
            respuesta=datos_respuesta["texto_respuesta"],
        )
        pregunta.id_respuesta = datos_respuesta.get("id_respuesta")
        pregunta.nivel_ia = datos_respuesta.get("nivel_ia", -1)
        pregunta.valoracion_ia = datos_respuesta.get("analisis_ia") or ""
        pregunta.nivel_profesional = datos_respuesta.get("nivel_profesional", -1)
        return pregunta

    def _cargar_estado_inicial_en_vista(self):
        if not self.interno:
            return

        self.ventana_interno.cargar_datos_interno(self.interno)
        if self.solicitud_actual is not None:
            self.interno.add_solicitud(self.solicitud_actual)

    def _actualizar_estado_inicio(self):
        self.tiene_solicitud = self.solicitud_actual is not None
        self.tiene_entrevista = bool(
            self.tiene_solicitud
            and self.solicitud_actual.estado == Tipo_estado_solicitud.PENDIENTE.value
        )
        estado_solicitud = self.solicitud_actual.estado if self.solicitud_actual else None
        self.ventana_interno.pantalla_bienvenida.actualizar_interfaz(
            self.tiene_solicitud,
            self.tiene_entrevista,
            estado_solicitud,
        )

    def conectar_senales(self):
        self.ventana_interno.boton_preguntas.clicked.connect(self.verificar_acceso_preguntas)
        self.ventana_interno.boton_progreso.clicked.connect(self.verificar_ver_progreso)
        self.ventana_interno.boton_solicitud.clicked.connect(self.verificar_creacion_solicitud)
        self.ventana_interno.boton_usuario.clicked.connect(self.iniciar_perfil)
        self.ventana_interno.boton_perfil_menu.clicked.connect(self.iniciar_perfil)
        self.ventana_interno.boton_cerrar_sesion.clicked.connect(self.cerrar_sesion)

        boton_inicio = self.ventana_interno.pantalla_bienvenida.boton_iniciar
        try:
            boton_inicio.clicked.disconnect()
        except Exception:
            pass

        estado_solicitud = self.solicitud_actual.estado if self.solicitud_actual else None
        if self.tiene_solicitud is False:
            boton_inicio.clicked.connect(self.iniciar_nueva_solicitud)
        elif estado_solicitud in [Tipo_estado_solicitud.INICIADA.value]:
            boton_inicio.clicked.connect(self.iniciar_entrevista)
        elif estado_solicitud in [Tipo_estado_solicitud.CANCELADA.value]:
            boton_inicio.clicked.connect(self.iniciar_nueva_solicitud)
        else:
            boton_inicio.clicked.connect(self.iniciar_progreso)

        self.ventana_interno.pantalla_preguntas.boton_atras.clicked.connect(self.pregunta_atras)
        self.ventana_interno.pantalla_preguntas.boton_siguiente.clicked.connect(
            self.siguiente_pregunta
        )
        self.ventana_interno.pantalla_preguntas.boton_finalizar.clicked.connect(
            self.ventana_interno.pantalla_preguntas.finalizar_entrevista
        )
        self.ventana_interno.pantalla_preguntas.entrevista_finalizada.connect(
            self.finalizar_entrevista
        )

        self.ventana_interno.pantalla_resumen_edit.boton_atras.clicked.connect(
            self.pantalla_resumen_atras
        )
        self.ventana_interno.pantalla_resumen_edit.grupo_botones_entrar.idClicked.connect(
            self.mostrar_detalle_pregunta_edit
        )
        self.ventana_interno.pantalla_resumen_edit.boton_enviar.clicked.connect(
            self.almacenar_entrevista
        )

        self.solicitud_controller.solicitud_finalizada.connect(self.solicitud_finalizada)

        self.progreso_controller.ver_entrevista_solicitud.connect(
            self.mostrar_resumen_entrevista
        )
        self.progreso_controller.realizar_entrevista_nueva.connect(self.iniciar_entrevista)

        self.ventana_interno.pantalla_resumen.grupo_botones_entrar.idClicked.connect(
            self.mostrar_detalle_pregunta
        )
        self.ventana_interno.pantalla_resumen.boton_atras.clicked.connect(
            self.iniciar_progreso
        )

        self.ventana_interno.pantalla_perfil.guardar_cambios.connect(
            self.guardar_cambios_perfil
        )

    def iniciar_entrevista(self):
        self.ventana_interno.mostrar_pantalla_preguntas()

    def iniciar_nueva_solicitud(self):
        self.ventana_interno.mostrar_pantalla_solicitud()

    def iniciar_progreso(self):
        self.ventana_interno.mostrar_pantalla_progreso()

    def iniciar_perfil(self):
        if self.interno:
            self.ventana_interno.pantalla_perfil.set_datos_usuario(self.interno)
        self.ventana_interno.mostrar_pantalla_perfil()

    def pregunta_atras(self):
        self.ventana_interno.pantalla_preguntas.ir_pregunta_atras()

    def siguiente_pregunta(self):
        self.ventana_interno.pantalla_preguntas.ir_pregunta_siguiente()

    def finalizar_entrevista(self, lista_respuestas, lista_audios):
        nueva_entrevista = Entrevista(
            id_entrevista=None,
            id_interno=self.interno.num_RC,
            fecha=date.today().strftime("%d/%m/%Y"),
        )

        for id_pregunta, (texto_res, ruta_audio) in enumerate(
            zip(lista_respuestas, lista_audios),
            start=1,
        ):
            obj_pregunta = Respuesta(id_pregunta, texto_res)
            if ruta_audio:
                obj_pregunta.set_archivo_audio(ruta_audio)
            nueva_entrevista.add_respuestas(obj_pregunta)

        if self.solicitud_actual:
            self.solicitud_actual.entrevista = nueva_entrevista

        self.ventana_interno.mostrar_pantalla_resumen_edit()
        self.ventana_interno.pantalla_resumen_edit.cargar_datos_respuestas(nueva_entrevista)

    def mostrar_resumen_entrevista(self):
        if not self.solicitud_actual:
            return

        entrevista = self.cargar_entrevista_solicitud(self.solicitud_actual.id_solicitud)
        if not entrevista:
            return

        self.solicitud_actual.entrevista = entrevista
        self.ventana_interno.pantalla_resumen.cargar_datos_respuestas(entrevista)
        self.ventana_interno.mostrar_pantalla_resumen()

    def mostrar_detalle_pregunta_edit(self, id_pregunta):
        entrevista_actual = getattr(self.solicitud_actual, "entrevista", None)
        self.pregunta_mostrar = self._buscar_pregunta_en_entrevista(entrevista_actual, id_pregunta)
        if not self.pregunta_mostrar:
            return

        ventana_detalle = VentanaDetallePreguntaEdit(self.pregunta_mostrar, id_pregunta)
        resultado = ventana_detalle.exec_()
        if resultado != QDialog.Accepted:
            return

        datos = ventana_detalle.get_datos()
        self.pregunta_mostrar.respuesta = datos["texto"]
        self.pregunta_mostrar.archivo_audio = datos["ruta_audio"]

        self.ventana_interno.pantalla_resumen_edit.cargar_datos_respuestas(entrevista_actual)
        self.msg.mostrar_mensaje(
            "Guardado",
            f"La pregunta {id_pregunta} se ha actualizado correctamente.",
        )

    def mostrar_detalle_pregunta(self, id_pregunta):
        entrevista_actual = getattr(self.solicitud_actual, "entrevista", None)
        self.pregunta_mostrar = self._buscar_pregunta_en_entrevista(entrevista_actual, id_pregunta)
        if not self.pregunta_mostrar:
            return

        ventana_detalle = VentanaDetallePregunta(
            self.pregunta_mostrar,
            id_pregunta,
            audio_loader=self.resolver_audio_respuesta if self._audio_client is not None else None,
        )
        ventana_detalle.exec_()

    @staticmethod
    def _buscar_pregunta_en_entrevista(entrevista, id_pregunta):
        if not entrevista:
            return None

        for pregunta in entrevista.respuestas:
            if pregunta.id_pregunta == id_pregunta:
                return pregunta
        return None

    def almacenar_entrevista(self):
        if not self.solicitud_actual or not self.solicitud_actual.entrevista:
            self.msg.mostrar_advertencia(
                "Entrevista no disponible",
                "No hay entrevista preparada para enviar.",
            )
            return

        confirmacion = self.msg.mostrar_confirmacion(
            "Enviar entrevista",
            "¿Desea enviar la entrevista?\n\nPróximamente será evaluado por un profesional",
        )
        if not confirmacion:
            return

        resultado_guardado = agregar_entrevista_y_respuestas(
            self.interno.num_RC,
            self.solicitud_actual.id_solicitud,
            self.solicitud_actual.entrevista.fecha,
            self.solicitud_actual.entrevista.respuestas,
        )
        if not isinstance(resultado_guardado, dict):
            self.msg.mostrar_mensaje(
                "Error en entrevista",
                "No ha podido realizarse el envio de la entrevista.\n\nContacte con un administrador.",
            )
            return

        id_entrevista = resultado_guardado.get("id_entrevista")
        self.solicitud_actual.entrevista.id_entrevista = id_entrevista
        self.solicitud_actual.estado = Tipo_estado_solicitud.PENDIENTE.value

        if not self._persistir_estado_solicitud_pendiente():
            self.msg.mostrar_advertencia(
                "Error BD",
                "Error en la actualización del estado de la solicitud.",
            )

        self.progreso_controller.set_solicitud(self.solicitud_actual)

        if not id_entrevista:
            self.msg.mostrar_mensaje(
                "Error en entrevista",
                "No ha podido realizarse el envio de la entrevista.\n\nContacte con un administrador.",
            )
            return

        self.ventana_interno.mostrar_espera_envio_audios(True)
        QApplication.processEvents()
        try:
            advertencia_audio = self._subir_audios_entrevista(
                resultado_guardado.get("respuestas", [])
            )
        finally:
            self.ventana_interno.mostrar_espera_envio_audios(False)

        mensaje = "La entrevista ha sido enviada correctamente"
        if advertencia_audio:
            mensaje = f"{mensaje}\n\n{advertencia_audio}"
        self.msg.mostrar_mensaje("Entrevista enviada", mensaje)
        self.iniciar_progreso()
        self.tiene_entrevista = True

    def _persistir_estado_solicitud_pendiente(self):
        return actualizar_estado_solicitud(
            self.solicitud_actual.id_solicitud,
            Tipo_estado_solicitud.PENDIENTE.value,
        )

    def pantalla_resumen_atras(self):
        self.ventana_interno.abrir_pregunta(10)

    def verificar_acceso_preguntas(self):
        if self.tiene_solicitud is False:
            self.ventana_interno.mostrar_advertencia(
                "Sin Solicitud",
                "No tiene una solicitud de evaluación iniciada o pendiente.",
            )
            return

        if self.solicitud_actual.estado != Tipo_estado_solicitud.INICIADA.value:
            self.ventana_interno.mostrar_advertencia(
                "Entrevista en proceso",
                "Ya ha realizado la entrevista para esta solicitud, espere a finalizar.",
            )
            return

        if self.tiene_entrevista is True:
            self.ventana_interno.mostrar_advertencia(
                "Entrevista ya realizada",
                "Ya ha completado la entrevista para esta solicitud.",
            )
            return

        self.ventana_interno.movimiento_submenu_preguntas()

    def verificar_ver_progreso(self):
        if self.solicitud_actual is None:
            self.ventana_interno.mostrar_advertencia(
                "Sin solicitud",
                "No tiene una solicitud de evaluación iniciada o pendiente.",
            )
            return

        self.progreso_controller.set_solicitud(self.solicitud_actual)
        self.iniciar_progreso()

    def verificar_creacion_solicitud(self):
        if self.solicitud_actual and self.solicitud_actual.estado in ["iniciada", "pendiente"]:
            self.ventana_interno.mostrar_advertencia(
                "Solicitud iniciada o pendiente",
                "Tiene una solicitud iniciada o pendiente, no puede crear otra",
            )
            return

        self.iniciar_nueva_solicitud()

    def cerrar_sesion(self):
        confirmado = self.ventana_interno.mostrar_confirmacion_logout()
        if not confirmado:
            return

        self.ventana_interno.close()
        self.logout_signal.emit()

    def cerrar_recursos(self):
        if self._audio_client is not None:
            self._audio_client.cleanup()

        carpeta_grabaciones = Path(__file__).resolve().parents[3] / "data" / "grabaciones"
        if os.path.exists(carpeta_grabaciones):
            shutil.rmtree(carpeta_grabaciones, ignore_errors=True)

    def _aplicar_estado_audio_api(self):
        if self._audio_client is not None or self.msg is None:
            return

        self.msg.mostrar_advertencia(
            "Audio no disponible",
            self._audio_client_error
            or "La API de audio no está disponible. Las funciones de audio se han desactivado.",
        )
        boton_grabar = self.ventana_interno.pantalla_preguntas.boton_grabar
        boton_grabar.setEnabled(False)
        boton_grabar.setToolTip("Desactivado: la API de audio no está disponible.")

    def solicitud_finalizada(self):
        self.solicitud_actual = self.cargar_ultima_solicitud()
        self.tiene_solicitud = self.solicitud_actual is not None
        self.tiene_entrevista = False
        self._actualizar_estado_inicio()

        self.progreso_controller.set_solicitud(self.solicitud_actual)
        self.ventana_interno.mostrar_pantalla_progreso()

    def guardar_cambios_perfil(self):
        if not self.interno:
            return

        datos = self.ventana_interno.pantalla_perfil.get_datos_edicion()
        nombre_nuevo = datos["nombre"]
        nombre_original = datos["nombre_original"]
        password = datos["password"]
        password_confirm = datos["password_confirm"]

        validacion_error = self._validar_edicion_perfil(
            nombre_nuevo,
            nombre_original,
            password,
            password_confirm,
        )
        if validacion_error:
            self.msg.mostrar_advertencia("Atención", validacion_error)
            return

        cambio_nombre = nombre_nuevo != nombre_original
        cambio_password = bool(password)
        ok = actualizar_usuario(
            self.interno.id_usuario,
            nombre=nombre_nuevo if cambio_nombre else None,
            contrasena=password if cambio_password else None,
        )
        if not ok:
            self.msg.mostrar_advertencia("Atención", "No se pudo actualizar el perfil.")
            return

        self._aplicar_cambios_perfil(nombre_nuevo)
        self.msg.mostrar_mensaje("Perfil actualizado", "Cambios guardados correctamente.")

    @staticmethod
    def _validar_edicion_perfil(nombre_nuevo, nombre_original, password, password_confirm):
        if not nombre_nuevo:
            return "El nombre no puede estar vacio."
        if password or password_confirm:
            if password != password_confirm:
                return "Las contraseñas no coinciden."
        if nombre_nuevo == nombre_original and not password:
            return "No hay cambios para guardar."
        return None

    def _aplicar_cambios_perfil(self, nombre_nuevo):
        self.interno.nombre = nombre_nuevo
        self.usuario.nombre = nombre_nuevo
        self.ventana_interno.pantalla_bienvenida.set_interno(self.interno)

    def _inicializar_audio_api(self, contrasena_plana):
        service = AudioService(
            email=self.usuario.email,
            password=contrasena_plana,
            session_key=f"interno_{self.usuario.id_usuario}",
        )
        if service.available:
            self._audio_client = service
            self._audio_client_error = None
            return

        self._audio_client = None
        self._audio_client_error = service.error_message

    def resolver_audio_respuesta(self, id_respuesta):
        if not id_respuesta:
            raise AudioApiError("No hay respuesta asociada al audio.")
        if self._audio_client is None:
            raise AudioApiError(
                self._audio_client_error or "La API de audio no esta disponible en esta sesion."
            )
        return self._audio_client.ensure_audio_local(id_respuesta)

    def _subir_audios_entrevista(self, respuestas_creadas):
        if not respuestas_creadas:
            return ""
        if self._audio_client is None:
            return (
                self._audio_client_error
                or "No se pudo conectar con la API de audio. Los audios no se han subido."
            )

        errores = []
        for respuesta_creada in respuestas_creadas:
            pregunta = respuesta_creada.get("pregunta")
            ruta_audio = getattr(pregunta, "archivo_audio", None)
            id_respuesta = respuesta_creada.get("id_respuesta")
            if not ruta_audio or not os.path.exists(ruta_audio) or not id_respuesta:
                continue
            try:
                self._audio_client.upload_audio(id_respuesta, ruta_audio)
            except AudioApiError as exc:
                errores.append(f"Pregunta {respuesta_creada.get('id_pregunta')}: {exc}")

        if not errores:
            return ""
        if len(errores) == 1:
            return f"El audio de una respuesta no se pudo subir. {errores[0]}"

        resumen = "\n".join(errores[:3])
        if len(errores) > 3:
            resumen += f"\nY {len(errores) - 3} mas."
        return f"Algunos audios no se pudieron subir:\n{resumen}"
