"""Reglas de validación del negocio y errores que el controlador muestra al usuario.

Los límites de cada pregunta vienen de la base de conocimiento, no están escritos aquí.
"""
import re
from decimal import Decimal, InvalidOperation

from app.modelo.entidades import Respuesta


class ErrorNegocio(Exception):
    """Error general con un mensaje para el usuario (p. ej. correo ya registrado)."""


class ErroresFormulario(Exception):
    """Errores por campo: {nombre_del_campo: mensaje}."""
    def __init__(self, errores):
        super().__init__("Hay campos con errores.")
        self.errores = errores


def _decimal(texto):
    try:
        return Decimal(str(texto).strip().replace(",", "."))
    except InvalidOperation:
        return None


def validar_respuesta(pregunta, texto) -> Respuesta:
    """RF-02: convierte el texto de una pregunta en una Respuesta válida o lanza ValueError.
    Las preguntas de ESCALA aceptan enteros; las NUMERICAS, hasta dos decimales."""
    if not texto:
        raise ValueError("La respuesta es obligatoria." if pregunta.tipo_respuesta == "NUMERICA" else "Elija una opción.")
    valor = _decimal(texto)
    if valor is None or not valor.is_finite():
        raise ValueError("Escriba un número.")
    if not pregunta.valor_minimo <= valor <= pregunta.valor_maximo:
        raise ValueError(f"El valor debe estar entre {pregunta.valor_minimo:g} y {pregunta.valor_maximo:g}.".replace(".", ","))
    if pregunta.tipo_respuesta == "ESCALA" and valor != valor.to_integral_value():
        raise ValueError("Elija una opción de la escala.")
    return Respuesta(pregunta.id_pregunta, valor.quantize(Decimal("0.01")))


def validar_registro(datos: dict, contrasena: str):
    """CU-01: revisa los datos del formulario de registro del aspirante."""
    errores = {campo: "Este campo es obligatorio." for campo, valor in datos.items() if not valor}
    if datos["documento"] and not datos["documento"].isdigit():
        errores["documento"] = "Escriba solo números, sin puntos ni espacios."
    if datos["correo"] and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", datos["correo"]):
        errores["correo"] = "Escriba un correo con el formato nombre@dominio.com."
    if len(contrasena) < 8:
        errores["contrasena"] = "Use al menos 8 caracteres."
    if errores:
        raise ErroresFormulario(errores)


def validar_peso(texto) -> Decimal:
    """CU-07: el peso de un gránulo es un número entre 0.00 y 1.00."""
    valor = _decimal(texto)
    if valor is None or not Decimal("0") <= valor <= Decimal("1"):
        raise ErroresFormulario({"peso": "Escriba un número entre 0,00 y 1,00."})
    return valor.quantize(Decimal("0.01"))
