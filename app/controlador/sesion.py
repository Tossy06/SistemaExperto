"""Sesión por rol y protección CSRF de los formularios."""
import hmac
import secrets
from functools import wraps

from flask import abort, flash, redirect, request, session, url_for

INICIO_POR_ROL = {"aspirante": "aspirante.inicio", "ingeniero": "ingeniero.panel"}


def abrir_sesion(rol, usuario):
    """Guarda en la cookie firmada los datos mínimos del usuario autenticado."""
    session.clear()
    session.permanent = True
    session["usuario"] = {"rol": rol, "id": getattr(usuario, f"id_{rol}"), "nombres": usuario.nombres,
                          "apellidos": usuario.apellidos, "correo": usuario.correo}


def usuario_actual():
    return session.get("usuario")


def rol_requerido(rol):
    """Decorador: sin sesión envía al inicio; con otro rol envía a la página de ese rol."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            usuario = usuario_actual()
            if usuario is None:
                flash("Inicie sesión para continuar.", "aviso")
                return redirect(url_for("publico.inicio", siguiente=request.path))
            if usuario["rol"] != rol:
                return redirect(url_for(INICIO_POR_ROL[usuario["rol"]]))
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def token_csrf():
    """Token secreto por sesión que cada formulario envía en un campo oculto."""
    session.setdefault("csrf", secrets.token_urlsafe(32))
    return session["csrf"]


def verificar_csrf():
    """Se ejecuta antes de cada petición: rechaza los POST cuyo token no coincide con el de la sesión."""
    if request.method == "POST":
        esperado = session.get("csrf", "")
        if not esperado or not hmac.compare_digest(request.form.get("csrf", ""), esperado):
            abort(400, "El formulario estuvo abierto demasiado tiempo. Recargue la página e intente de nuevo.")
