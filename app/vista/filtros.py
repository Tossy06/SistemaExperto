"""Filtros de formato para las plantillas: porcentajes, números y fechas en estilo colombiano."""
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal

from app.config import DECIMALES_PRESENTACION

_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def porcentaje(valor):
    """15.6250 -> «15,63 %»."""
    if valor is None:
        return ""
    redondeado = Decimal(valor).quantize(Decimal(1).scaleb(-DECIMALES_PRESENTACION), rounding=ROUND_HALF_UP)
    return f"{redondeado} %".replace(".", ",")


def coincidencia(valor):
    """Grado de 0 a 1 como porcentaje: 0.9064 -> «90,6 %»."""
    return "" if valor is None else f"{Decimal(valor) * 100:.1f} %".replace(".", ",")


def numero(valor, decimales=2):
    """0.4 -> «0,40»."""
    return "" if valor is None else f"{Decimal(valor):.{decimales}f}".replace(".", ",")


def fecha(valor):
    """datetime -> «9 nov 2026, 12:42»."""
    return f"{valor.day} {_MESES[valor.month - 1]} {valor.year}, {valor:%H:%M}" if valor else ""


def clase(valor):
    """«Primera» -> «primera», «Indistinto» -> «indistinto»: nombre seguro para una clase CSS."""
    texto = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")


def registrar_filtros(app):
    """Hace disponibles los filtros en Jinja como |pct, |num, |fecha y |clase."""
    app.jinja_env.filters.update(pct=porcentaje, pct1=coincidencia, num=numero, fecha=fecha, clase=clase)
    app.jinja_env.trim_blocks = app.jinja_env.lstrip_blocks = True
