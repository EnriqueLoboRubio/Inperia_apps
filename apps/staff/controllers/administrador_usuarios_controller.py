import re

from PyQt5.QtWidgets import QDialog

from db.solicitud_db import contar_solicitudes_resumen_staff, listar_solicitudes_resumen_staff
from db.usuario_db import (
    actualizar_usuario_admin,
    agregar_usuario_admin,
    anonimizar_usuario_admin,
    contar_administradores,
    eliminar_usuario_admin,
    listar_usuarios_admin,
)
from gui.ventana_usuario_administrador import VentanaUsuarioAdministrador
from models.entrevista import Entrevista
from models.interno import Interno
from models.solicitud import Solicitud
from utils.opciones_formulario import RELACIONES_FAMILIARES
from utils.enums import Tipo_situacion_legal


class AdministradorUsuariosController:
    """
    Controlador para la gestión de usuarios del administrador.
    """

    RELACIONES_CONTACTO = RELACIONES_FAMILIARES

    def __init__(self, controlador):
        self.controlador = controlador

    def mostrar_lista_usuarios(self):
        self.recargar_lista()
        pantalla = self.controlador.ventana_administrador.pantalla_lista_usuarios
        self.controlador.ventana_administrador.stacked_widget.setCurrentWidget(pantalla)
        self.controlador.ventana_administrador.establecer_titulo_pantalla("Usuarios")

    def recargar_lista(self):
        pantalla = self.controlador.ventana_administrador.pantalla_lista_usuarios
        filtros = pantalla.obtener_filtros()
        filas = listar_usuarios_admin(
            filtro_rol=filtros.get("rol"),
            texto_busqueda=filtros.get("texto"),
        )
        usuarios = [self._fila_a_dict(fila) for fila in filas]
        pantalla.cargar_datos(usuarios)

    def abrir_creacion_usuario(self):
        ventana = VentanaUsuarioAdministrador(
            parent=self.controlador.ventana_administrador,
            situacion_legal_opciones=self._obtener_situaciones_legales(),
            relacion_contacto_opciones=self.RELACIONES_CONTACTO,
            permitir_eliminacion=False,
        )
        if ventana.exec_() != QDialog.Accepted:
            return

        datos = ventana.get_datos()
        if not self._validar_datos(datos, es_edicion=False):
            return

        try:
            agregar_usuario_admin(
                nombre=datos["nombre"],
                email=datos["email"],
                contrasena=datos["password"],
                rol=datos["rol"],
                num_colegiado=int(datos["num_colegiado"]) if datos["rol"] == "profesional" else None,
                num_rc=int(datos["num_rc"]) if datos["rol"] == "interno" else None,
                fecha_nac=datos["fecha_nac"] if datos["rol"] == "interno" else None,
                situacion_legal=datos["situacion_legal"] if datos["rol"] == "interno" else None,
                delito=datos["delito"] if datos["rol"] == "interno" else None,
                condena=datos["condena"] if datos["rol"] == "interno" else None,
                fecha_ingreso=datos["fecha_ingreso"] if datos["rol"] == "interno" else None,
                modulo=datos["modulo"] if datos["rol"] == "interno" else None,
                lugar_nacimiento=datos["lugar_nacimiento"] if datos["rol"] == "interno" else None,
                nombre_contacto_emergencia=datos["nombre_contacto_emergencia"] if datos["rol"] == "interno" else None,
                relacion_contacto_emergencia=datos["relacion_contacto_emergencia"] if datos["rol"] == "interno" else None,
                numero_contacto_emergencia=datos["numero_contacto_emergencia"] if datos["rol"] == "interno" else None,
            )
        except Exception as e:
            self.controlador.msg.mostrar_advertencia("Atención", f"No se pudo crear el usuario.\n{str(e)}")
            return

        self.controlador.msg.mostrar_mensaje("Usuario creado", "El usuario se ha creado correctamente.")
        self.mostrar_lista_usuarios()

    def abrir_edicion_usuario(self, usuario):
        ventana = VentanaUsuarioAdministrador(
            usuario=usuario,
            parent=self.controlador.ventana_administrador,
            situacion_legal_opciones=self._obtener_situaciones_legales(),
            relacion_contacto_opciones=self.RELACIONES_CONTACTO,
            permitir_eliminacion=self._puede_eliminar_usuario(usuario),
        )
        if ventana.exec_() != QDialog.Accepted:
            return

        if ventana.accion_solicitada() == "eliminar":
            if not self._eliminar_o_anonimizar_usuario(usuario):
                return
            self.mostrar_lista_usuarios()
            return

        datos = ventana.get_datos()
        if not self._validar_datos(datos, es_edicion=True):
            return

        try:
            actualizar_usuario_admin(
                id_usuario=datos["id_usuario"],
                nombre=datos["nombre"],
                email=datos["email"],
                rol=datos["rol"],
                contrasena=datos["password"] or None,
                num_colegiado=int(datos["num_colegiado"]) if datos["rol"] == "profesional" else None,
                num_rc=int(datos["num_rc"]) if datos["rol"] == "interno" else None,
                fecha_nac=datos["fecha_nac"] if datos["rol"] == "interno" else None,
                situacion_legal=datos["situacion_legal"] if datos["rol"] == "interno" else None,
                delito=datos["delito"] if datos["rol"] == "interno" else None,
                condena=datos["condena"] if datos["rol"] == "interno" else None,
                fecha_ingreso=datos["fecha_ingreso"] if datos["rol"] == "interno" else None,
                modulo=datos["modulo"] if datos["rol"] == "interno" else None,
                lugar_nacimiento=datos["lugar_nacimiento"] if datos["rol"] == "interno" else None,
                nombre_contacto_emergencia=datos["nombre_contacto_emergencia"] if datos["rol"] == "interno" else None,
                relacion_contacto_emergencia=datos["relacion_contacto_emergencia"] if datos["rol"] == "interno" else None,
                numero_contacto_emergencia=datos["numero_contacto_emergencia"] if datos["rol"] == "interno" else None,
            )
        except Exception as e:
            self.controlador.msg.mostrar_advertencia("Atención", f"No se pudo actualizar el usuario.\n{str(e)}")
            return

        self.controlador.msg.mostrar_mensaje("Usuario actualizado", "Los cambios se han guardado correctamente.")
        self.mostrar_lista_usuarios()

    def mostrar_perfil_profesional(self, usuario):
        if str(usuario.get("rol", "") or "").strip().lower() != "profesional":
            return

        self.controlador._vista_origen_perfil_profesional_admin = (
            self.controlador.ventana_administrador.stacked_widget.currentWidget()
        )
        self.controlador._titulo_origen_perfil_profesional_admin = (
            self.controlador.ventana_administrador.titulo_pantalla.text()
        )

        self.controlador._profesional_lista_admin_id = usuario.get("id_usuario")

        pantalla = self.controlador.ventana_administrador.pantalla_lista_solicitudes_profesional
        pantalla.aplicar_filtro_inicial(
            top_activo=None,
            combo_texto="Todos",
            modo_historial=False,
            mostrar_filtros_superiores=False,
            mostrar_boton_volver=True,
        )
        self.controlador.ventana_administrador.stacked_widget.setCurrentWidget(pantalla)
        self._cargar_lista_profesional(reiniciar=True)
        nombre = str(usuario.get("nombre", "") or "Profesional").strip()
        self.controlador.ventana_administrador.establecer_titulo_pantalla(f"Perfil profesional: {nombre}")

    def on_filtros_lista_profesional_cambiados(self):
        self._cargar_lista_profesional(reiniciar=True)

    def on_solicitar_mas_lista_profesional(self):
        self._cargar_lista_profesional(reiniciar=False)

    def _cargar_lista_profesional(self, reiniciar):
        pantalla = self.controlador.ventana_administrador.pantalla_lista_solicitudes_profesional
        if reiniciar and self.controlador.ventana_administrador.stacked_widget.currentWidget() != pantalla:
            return
        if reiniciar and pantalla.esta_cargando_mas():
            return

        id_profesional = getattr(self.controlador, "_profesional_lista_admin_id", None)
        if id_profesional is None:
            return

        offset = 0 if reiniciar else pantalla.obtener_offset_actual()
        try:
            if reiniciar:
                total = contar_solicitudes_resumen_staff(
                    modo="profesional_todas",
                    id_profesional=id_profesional,
                    busqueda=pantalla.obtener_texto_busqueda(),
                    estado=pantalla.obtener_combo_estado(),
                )
            else:
                total = pantalla.obtener_total_disponible()

            filas = listar_solicitudes_resumen_staff(
                modo="profesional_todas",
                id_profesional=id_profesional,
                busqueda=pantalla.obtener_texto_busqueda(),
                estado=pantalla.obtener_combo_estado(),
                limit=pantalla.obtener_tam_lote(),
                offset=offset,
            )
        except Exception as e:
            pantalla.mostrar_error_carga(f"Error al cargar las solicitudes. {e}")
            return

        solicitudes = [self._construir_solicitud_resumen_desde_fila(fila) for fila in filas]
        if reiniciar:
            pantalla.reemplazar_datos(solicitudes, total)
        else:
            pantalla.anadir_datos(solicitudes, total)

    def volver_desde_perfil_profesional(self):
        widget = getattr(self.controlador, "_vista_origen_perfil_profesional_admin", None)
        titulo = getattr(self.controlador, "_titulo_origen_perfil_profesional_admin", "Usuarios")
        if widget is not None:
            self.controlador.ventana_administrador.stacked_widget.setCurrentWidget(widget)
            self.controlador.ventana_administrador.establecer_titulo_pantalla(titulo)
            return
        self.mostrar_lista_usuarios()

    @staticmethod
    def _construir_solicitud_resumen_desde_fila(fila):
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
        if fila["entrevista_id"] is not None:
            entrevista = Entrevista(
                id_entrevista=fila["entrevista_id"],
                id_interno=fila["id_interno"],
                fecha=fila["entrevista_fecha"],
            )
            entrevista.puntuacion_ia = fila["entrevista_puntuacion_ia"]
            entrevista.puntuacion_profesional = fila["entrevista_puntuacion_profesional"]
            entrevista.estado_evaluacion_ia = fila["entrevista_estado_evaluacion_ia"] or "Sin evaluación"
            solicitud.entrevista = entrevista
        return solicitud

    def _validar_datos(self, datos, es_edicion):
        nombre = str(datos.get("nombre", "")).strip()
        email = str(datos.get("email", "")).strip()
        password = str(datos.get("password", ""))
        password_confirm = str(datos.get("password_confirm", ""))
        rol = str(datos.get("rol", "")).strip().lower()

        if not nombre or not email:
            self.controlador.msg.mostrar_advertencia("Atención", "Nombre y email son obligatorios.")
            return False

        if not self._validar_email(email):
            self.controlador.msg.mostrar_advertencia("Atención", "El formato del email no es válido.")
            return False

        if not es_edicion and not password:
            self.controlador.msg.mostrar_advertencia("Atención", "Debe indicar una contraseña.")
            return False

        if password or password_confirm:
            if password != password_confirm:
                self.controlador.msg.mostrar_advertencia("Atención", "Las contraseñas no coinciden.")
                return False

        if rol == "profesional" and not str(datos.get("num_colegiado", "")).strip():
            self.controlador.msg.mostrar_advertencia("Atención", "Debe indicar el número de colegiado.")
            return False

        if rol == "interno":
            obligatorios = {
                "num_rc": "el número de recluso",
                "fecha_nac": "la fecha de nacimiento",
                "situacion_legal": "la situación legal",
                "delito": "el delito",
                "condena": "la duración de condena",
                "fecha_ingreso": "la fecha de ingreso",
                "modulo": "el módulo",
                "lugar_nacimiento": "el lugar de nacimiento",
                "nombre_contacto_emergencia": "el nombre del contacto de emergencia",
                "relacion_contacto_emergencia": "la relación del contacto de emergencia",
                "numero_contacto_emergencia": "el número de teléfono del contacto de emergencia",
            }
            faltan = []
            for clave, etiqueta in obligatorios.items():
                valor = str(datos.get(clave, "")).strip()
                if not valor or valor == "Seleccionar...":
                    faltan.append(etiqueta)

            if faltan:
                self.controlador.msg.mostrar_advertencia(
                    "Atención",
                    "Para internos faltan estos campos obligatorios:\n- " + "\n- ".join(faltan),
                )
                return False

        return True

    @staticmethod
    def _validar_email(correo):
        patron = r"^[\w\.-]+@[\w\.-]+\.\w{2,4}$"
        return re.match(patron, correo) is not None

    def _eliminar_o_anonimizar_usuario(self, usuario):
        id_usuario = usuario.get("id_usuario")
        rol = str(usuario.get("rol", "") or "").strip().lower()

        if rol == "administrador" and not self._puede_eliminar_usuario(usuario):
            self.controlador.msg.mostrar_advertencia(
                "Atención",
                "No se puede borrar este administrador porque debe permanecer al menos un administrador en la aplicación."
            )
            return False

        if rol == "interno":
            decision = self.controlador.msg.mostrar_decision_eliminacion(
                "Borrar usuario interno",
                "¿Qué desea hacer con este interno?\n\n"
                "Si elige eliminar, se borrarán también la solicitud, entrevistas y comentarios asociados.\n"
                "Si elige anonimizar, se conservarán esos datos pero sin mantener la identidad personal.",
                "Eliminar",
                "Anonimizar"
            )
            if decision == "cancelar":
                return False
            try:
                if decision == "confirmar":
                    eliminado = eliminar_usuario_admin(id_usuario)
                    if not eliminado:
                        self.controlador.msg.mostrar_advertencia("Atención", "No se encontró el usuario a borrar.")
                        return False
                    self.controlador.msg.mostrar_mensaje(
                        "Usuario borrado",
                        "El interno y todos sus datos asociados se han eliminado correctamente."
                    )
                    return True

                anonimizar_usuario_admin(id_usuario, rol)
                self.controlador.msg.mostrar_mensaje(
                    "Usuario anonimizado",
                    "El interno se ha anonimizado y se han conservado sus solicitudes y entrevistas."
                )
                return True
            except Exception as e:
                self.controlador.msg.mostrar_advertencia(
                    "Atención",
                    f"No se pudo completar la operación sobre el interno.\n{str(e)}"
                )
                return False

        try:
            eliminado = eliminar_usuario_admin(id_usuario)
            if not eliminado:
                self.controlador.msg.mostrar_advertencia("Atención", "No se encontró el usuario a borrar.")
                return False
            self.controlador.msg.mostrar_mensaje("Usuario borrado", "El usuario se ha eliminado correctamente.")
            return True
        except Exception as e:
            if rol == "profesional":
                anonimizar = self.controlador.msg.mostrar_confirmacion(
                    "No se puede borrar el profesional",
                    "El profesional tiene datos relacionados que impiden el borrado.\n\n"
                    "¿Desea anonimizarlo para conservar comentarios y referencias sin mantener sus datos personales?"
                )
                if not anonimizar:
                    return False
                try:
                    anonimizar_usuario_admin(id_usuario, rol)
                    self.controlador.msg.mostrar_mensaje(
                        "Profesional anonimizado",
                        "El profesional se ha anonimizado y se han conservado sus referencias asociadas."
                    )
                    return True
                except Exception as error_anon:
                    self.controlador.msg.mostrar_advertencia(
                        "Atención",
                        f"No se pudo anonimizar el profesional.\n{str(error_anon)}"
                    )
                    return False

            self.controlador.msg.mostrar_advertencia(
                "Atención",
                f"No se pudo borrar el usuario.\n{str(e)}"
            )
            return False

    @staticmethod
    def _obtener_situaciones_legales():
        return [opcion.value for opcion in Tipo_situacion_legal]

    @staticmethod
    def _puede_eliminar_usuario(usuario):
        rol = str(usuario.get("rol", "") or "").strip().lower()
        if rol != "administrador":
            return True
        return contar_administradores() > 1

    @staticmethod
    def _fila_a_dict(fila):
        return {
            "id_usuario": fila[0],
            "nombre": fila[1],
            "email": fila[2],
            "rol": fila[3],
            "num_colegiado": fila[4],
            "num_rc": fila[5],
            "fecha_nac": fila[6],
            "modulo": fila[7],
            "situacion_legal": fila[8],
            "delito": fila[9],
            "condena": fila[10],
            "fecha_ingreso": fila[11],
            "lugar_nacimiento": fila[12],
            "nombre_contacto_emergencia": fila[13],
            "relacion_contacto_emergencia": fila[14],
            "numero_contacto_emergencia": fila[15],
        }
