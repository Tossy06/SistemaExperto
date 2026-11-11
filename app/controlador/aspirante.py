"""Controlador del aspirante: cuestionario (CU-03), resultado (CU-04) e historial de evaluaciones (CU-05)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.config import EJEMPLO_DEMO
from app.controlador import sistema
from app.controlador.sesion import rol_requerido, usuario_actual
from app.modelo.validaciones import ErroresFormulario

bp = Blueprint("aspirante", __name__)


@bp.before_request
@rol_requerido("aspirante")
def proteger():
    """Todas las rutas de este Blueprint exigen sesión de aspirante."""


@bp.get("/")
def inicio():
    evaluaciones = sistema().evaluaciones.listar_por_aspirante(usuario_actual()["id"])
    return render_template("aspirante/inicio.html", evaluaciones=evaluaciones)


def _pagina_cuestionario(valores, errores, estado=200):
    preguntas = sistema().preguntas.activas()
    return render_template("aspirante/cuestionario.html", preguntas=preguntas, valores=valores, errores=errores,
                           rangos=sistema().hechos.rangos_por_variable(), ejemplo=EJEMPLO_DEMO,
                           nombres={p.codigo_variable: p.nombre_variable for p in preguntas}), estado


@bp.get("/cuestionario")
def cuestionario():
    return _pagina_cuestionario({}, {})


@bp.post("/cuestionario")
def evaluar():
    valores = request.form.to_dict()
    try:
        id_evaluacion = sistema().evaluar(usuario_actual()["id"], valores)
    except ErroresFormulario as error:
        flash(f"Revise {len(error.errores)} respuesta(s) marcada(s) en el cuestionario.", "error")
        return _pagina_cuestionario(valores, error.errores, 422)
    return redirect(url_for("aspirante.evaluacion", id_evaluacion=id_evaluacion))


@bp.get("/evaluaciones/<int:id_evaluacion>")
def evaluacion(id_evaluacion):
    datos = sistema().evaluaciones.detalle(id_evaluacion)
    # Un aspirante solo puede ver sus propias evaluaciones.
    if datos is None or datos["evaluacion"]["id_aspirante"] != usuario_actual()["id"]:
        abort(404)
    return render_template("aspirante/resultado.html", **datos, volver=url_for("aspirante.inicio"))
