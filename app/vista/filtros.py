"""Filtros de formato para las plantillas: porcentajes, números y fechas en estilo colombiano."""
from decimal import ROUND_HALF_UP, Decimal

from app.config import DECIMALES_PRESENTACION

_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def porcentaje(valor):
    """15.6250 -> «15,63 %»."""
    if valor is None:
        return ""
    redondeado = Decimal(valor).quantize(Decimal(1).scaleb(-DECIMALES_PRESENTACION), rounding=ROUND_HALF_UP)
    return f"{redondeado} %".replace(".", ",")


def numero(valor, decimales=2):
    """0.4 -> «0,40»."""
    return "" if valor is None else f"{Decimal(valor):.{decimales}f}".replace(".", ",")


def fecha(valor):
    """datetime -> «9 nov 2026, 12:42»."""
    return f"{valor.day} {_MESES[valor.month - 1]} {valor.year}, {valor:%H:%M}" if valor else ""


def registrar_filtros(app):
    """Hace disponibles los filtros en Jinja como |pct, |num y |fecha."""
    app.jinja_env.filters.update(pct=porcentaje, num=numero, fecha=fecha)
    app.jinja_env.trim_blocks = app.jinja_env.lstrip_blocks = True
