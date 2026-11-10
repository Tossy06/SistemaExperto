"""Controlador público: página de inicio, registro de aspirantes (CU-01) e inicio y cierre de sesión (CU-02)."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.controlador import sistema
from app.controlador.sesion import INICIO_POR_ROL, abrir_sesion, usuario_actual
from app.modelo.validaciones import ErroresFormulario, ErrorNegocio

bp = Blueprint("publico", __name__)


def _pagina_inicio(pestana, datos=None, errores=None, estado=200):
    return render_template("publico/inicio.html", pestana=pestana, datos=datos or {}, errores=errores or {}), estado


@bp.get("/")
def inicio():
    usuario = usuario_actual()
    if usuario:
        return redirect(url_for(INICIO_POR_ROL[usuario["rol"]]))
    return _pagina_inicio(request.args.get("pestana", "ingresar"))


@bp.post("/ingresar")
def ingresar():
    rol, correo = request.form.get("rol", "aspirante"), request.form.get("correo", "")
    try:
        usuario = sistema().autenticar(rol, correo, request.form.get("contrasena", ""))
    except ErrorNegocio as error:
        flash(str(error), "error")
        return _pagina_inicio("ingresar", {"rol": rol, "correo": correo}, estado=401)
    abrir_sesion(rol, usuario)
    siguiente = request.args.get("siguiente", "")
    # Solo se vuelve a rutas internas del mismo rol (evita redirecciones a otros sitios).
    return redirect(siguiente if siguiente.startswith(f"/{rol}/") else url_for(INICIO_POR_ROL[rol]))


@bp.post("/registro")
def registro():
    datos = {campo: request.form.get(campo, "") for campo in ("documento", "nombres", "apellidos", "correo")}
    try:
        aspirante = sistema().registrar_aspirante(datos, request.form.get("contrasena", ""))
    except ErroresFormulario as error:
        return _pagina_inicio("registro", datos, error.errores, 422)
    except ErrorNegocio as error:
        flash(str(error), "error")
        return _pagina_inicio("registro", datos, estado=409)
    abrir_sesion("aspirante", aspirante)
    flash(f"Cuenta creada. Bienvenido(a), {aspirante.nombres}.", "exito")
    return redirect(url_for("aspirante.cuestionario"))


@bp.post("/salir")
def salir():
    session.clear()
    flash("Cerró la sesión.", "exito")
    return redirect(url_for("publico.inicio"))
