"""CONTROLADOR (la C de MVC): rutas Flask agrupadas por rol (Blueprints).

Cada ruta recibe la petición, llama al modelo (SistemaExperto) y elige qué plantilla de la vista mostrar.
"""
from flask import current_app


def sistema():
    """Devuelve la instancia de SistemaExperto (el modelo) creada en crear_app()."""
    return current_app.extensions["sistema_experto"]
