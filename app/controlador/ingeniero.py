"""Controlador del ingeniero del conocimiento: panel, gránulos por hipótesis (CU-06),
mantenimiento del conocimiento (CU-07), reglas y rangos, y supervisión de evaluaciones (CU-08)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.controlador import sistema
from app.controlador.sesion import rol_requerido, usuario_actual
from app.modelo.validaciones import ErroresFormulario, ErrorNegocio

bp = Blueprint("ingeniero", __name__)


@bp.before_request
@rol_requerido("ingeniero")
def proteger():
    """Todas las rutas de este Blueprint exigen sesión de ingeniero."""


def _agrupar(filas, clave):
    """Agrupa filas en {clave(fila): [filas]} conservando el orden de la consulta."""
    grupos = {}
    for fila in filas:
        grupos.setdefault(clave(fila), []).append(fila)
    return grupos


@bp.get("/")
def panel():
    return render_template("ingeniero/panel.html", resumen=sistema().resumen())


@bp.get("/granulos")
def granulos():
    codigo = request.args.get("hipotesis", "")
    filas = sistema().granulos.listar(codigo)
    return render_template("ingeniero/granulos.html", hipotesis=sistema().hipotesis.activas(), codigo=codigo,
                           grupos=_agrupar(filas, lambda f: (f["hipotesis"], f["programa_academico"])),
                           total=len(filas), activos=sum(f["activo"] for f in filas))


def _pagina_nuevo(datos, errores, estado=200):
    return render_template("ingeniero/granulo_nuevo.html", hipotesis=sistema().hipotesis.activas(),
                           hechos=_agrupar(sistema().hechos.listar(), lambda h: h["variable"]),
                           datos=datos, errores=errores), estado


@bp.get("/granulos/nuevo")
def granulo_nuevo():
    return _pagina_nuevo({"peso": "0,20"}, {})


@bp.post("/granulos/nuevo")
def granulo_crear():
    datos = {campo: request.form.get(campo, "") for campo in ("id_hecho", "id_hipotesis", "peso")}
    try:
        codigo = sistema().crear_granulo(usuario_actual()["id"], datos["id_hecho"], datos["id_hipotesis"], datos["peso"])
    except ErroresFormulario as error:
        return _pagina_nuevo(datos, error.errores, 422)
    except ErrorNegocio as error:
        flash(str(error), "error")
        return _pagina_nuevo(datos, {}, 409)
    flash(f"Gránulo {codigo} guardado. El motor lo usará desde la próxima evaluación.", "exito")
    return redirect(url_for("ingeniero.granulos", _anchor=codigo))


def _granulo_o_404(id_granulo):
    return sistema().granulos.obtener(id_granulo) or abort(404)


@bp.get("/granulos/<int:id_granulo>")
def granulo_editar(id_granulo):
    granulo = _granulo_o_404(id_granulo)
    return render_template("ingeniero/granulo_editar.html", granulo=granulo, peso=granulo["peso"], errores={})


@bp.post("/granulos/<int:id_granulo>")
def granulo_guardar(id_granulo):
    granulo = _granulo_o_404(id_granulo)
    peso = request.form.get("peso", "")
    try:
        sistema().actualizar_granulo(usuario_actual()["id"], id_granulo, peso, request.form.get("activo") == "1")
    except ErroresFormulario as error:
        return render_template("ingeniero/granulo_editar.html", granulo=granulo, peso=peso, errores=error.errores), 422
    flash(f"Cambios guardados en {granulo['regla']}.", "exito")
    return redirect(url_for("ingeniero.granulos", hipotesis=granulo["hipotesis"], _anchor=granulo["regla"]))


@bp.get("/reglas")
def reglas():
    return render_template("ingeniero/reglas.html", reglas=sistema().reglas.activas(),
                           variables=_agrupar(sistema().hechos.listar(), lambda h: h["variable"]))


@bp.get("/evaluaciones")
def evaluaciones():
    texto = request.args.get("q", "")
    return render_template("ingeniero/evaluaciones.html", evaluaciones=sistema().evaluaciones.listar_todas(texto), q=texto)


@bp.get("/evaluaciones/<int:id_evaluacion>")
def evaluacion(id_evaluacion):
    datos = sistema().evaluaciones.detalle(id_evaluacion) or abort(404)
    return render_template("aspirante/resultado.html", **datos, volver=url_for("ingeniero.evaluaciones"))
