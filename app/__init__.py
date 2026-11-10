"""Sistema Experto de Apoyo a la Orientación Académica: aplicación web Flask con patrón MVC.

    modelo/       M: entidades, DAO, motor de inferencia y reglas de negocio (SistemaExperto)
    vista/        V: plantillas Jinja, CSS, JavaScript y filtros de formato
    controlador/  C: rutas Flask por rol que conectan la vista con el modelo

crear_app() instancia el pool de conexiones y el modelo, y registra la vista y los controladores.
"""
from datetime import timedelta

import psycopg2
from flask import Flask, g, render_template

from app import config
from app.controlador import aspirante, ingeniero, publico
from app.controlador.sesion import token_csrf, usuario_actual, verificar_csrf
from app.modelo.conexion import FabricaConexion
from app.modelo.sistema_experto import SistemaExperto
from app.vista.filtros import registrar_filtros


def crear_app(fabrica=None) -> Flask:
    """`fabrica` permite inyectar otra fuente de conexiones en las pruebas."""
    app = Flask(__name__, template_folder="vista/templates", static_folder="vista/static")
    app.config.update(SECRET_KEY=config.CLAVE_SECRETA, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=2))

    # ---------- Modelo: una conexión del pool por petición, compartida por todos los DAO ----------
    fabrica = fabrica or FabricaConexion(config.CONFIG_BD)

    def conexion_actual():
        if "conexion" not in g:
            g.conexion = fabrica.obtener()
        return g.conexion

    @app.teardown_appcontext
    def devolver_conexion(_error):
        if "conexion" in g:
            fabrica.devolver(g.pop("conexion"))

    app.extensions["fabrica_conexion"] = fabrica
    app.extensions["sistema_experto"] = SistemaExperto(conexion_actual)

    # ---------- Vista: filtros y datos disponibles en todas las plantillas ----------
    registrar_filtros(app)
    app.context_processor(lambda: {"usuario": usuario_actual(), "token_csrf": token_csrf,
                                   "nombre_bd": config.NOMBRE_PERFIL_BD})

    # ---------- Controladores ----------
    app.register_blueprint(publico.bp)
    app.register_blueprint(aspirante.bp, url_prefix="/aspirante")
    app.register_blueprint(ingeniero.bp, url_prefix="/ingeniero")
    app.before_request(verificar_csrf)

    # ---------- Páginas de error ----------
    def pagina_error(codigo, titulo, mensaje):
        return render_template("error.html", codigo=codigo, titulo=titulo, mensaje=mensaje), codigo

    app.register_error_handler(404, lambda e: pagina_error(
        404, "Esta página no existe", "El enlace puede estar incompleto o la evaluación no le pertenece."))
    app.register_error_handler(400, lambda e: pagina_error(
        400, "El formulario venció", e.description))
    app.register_error_handler(psycopg2.OperationalError, lambda e: pagina_error(
        503, "No hay conexión con la base de datos",
        f"Revise que {config.NOMBRE_PERFIL_BD} esté encendido y que los datos del archivo .env sean correctos."))
    return app
