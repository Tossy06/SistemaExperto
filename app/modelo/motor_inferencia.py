"""
Motor de inferencia probabilístico del sistema experto (encadenamiento hacia adelante).

No contiene condicionales sobre programas académicos, áreas, categorías RIASEC ni valores de las
variables (RNF-03). Todo el conocimiento se obtiene de la base de conocimiento:
  1. derivación de los hechos del perfil a partir de las respuestas (reglas RC, una consulta);
  2. una consulta granular por cada hecho para traer sus gránulos (reglas RG);
  3. contabilización: cada gránulo aporta peso × grado de certeza del hecho;
  4. probabilidades, grado de coincidencia y las cinco hipótesis (reglas RI);
  5. reglas de resultado no concluyente evaluadas por métrica y operador (reglas RN).
"""
import operator
from decimal import Decimal, ROUND_HALF_UP

from app.config import DECIMALES_CALCULO, NUMERO_HIPOTESIS_RESULTADO
from app.modelo.entidades import ConteoHipotesis, ResultadoInferencia

_CUANTO = Decimal(1).scaleb(-DECIMALES_CALCULO)        # 0.0001

# Operadores y métricas de las reglas RN, resueltos por tabla (despacho) y no con if/else.
OPERADORES = {"=": operator.eq, ">=": operator.ge, "<": operator.lt}
METRICAS = {
    # cantidad de hechos del aspirante con el tipo de variable y el valor de la regla
    "CONTEO_HECHOS": lambda regla, hechos, cinco: sum(
        1 for h in hechos if (h.tipo_variable, h.valor_clasificado) == (regla.tipo_variable, regla.valor_hecho)),
    # grado de coincidencia de la hipótesis de primer lugar (0 si no hubo ninguna)
    "COINCIDENCIA_PRIMERA": lambda regla, hechos, cinco: cinco[0].grado_coincidencia if cinco else Decimal("0"),
}


def _redondear(valor):
    return valor.quantize(_CUANTO, rounding=ROUND_HALF_UP)


class HechoNoDerivable(Exception):
    """Ningún rango de la base de conocimiento contiene el valor calculado para una variable."""

    def __init__(self, codigos_variable):
        super().__init__("El valor no corresponde a ningún rango de clasificación.")
        self.codigos_variable = tuple(codigos_variable)


class TablaContabilizacion:
    """Tabla de contabilización de coincidencias para las hipótesis (RF-03)."""

    def __init__(self, maximos: dict):
        self._filas, self._maximos = {}, maximos

    def registrar(self, granulo, hecho):
        """RI-01: el gránulo coincide con un hecho del aspirante y aporta peso × grado."""
        fila = self._filas.setdefault(granulo.id_hipotesis, ConteoHipotesis(
            granulo.id_hipotesis, granulo.codigo_hipotesis, granulo.programa_academico,
            maximo_alcanzable=self._maximos.get(granulo.id_hipotesis, Decimal("1"))))
        aporte = _redondear(granulo.peso * hecho.grado)
        fila.numero_coincidencias += 1
        fila.suma_aportes += aporte
        fila.hechos_coincidentes.append((hecho.descripcion(), granulo.peso, hecho.grado, aporte, granulo.codigo_regla))

    def calcular(self) -> list:
        """RI-02: P(h) = suma de aportes de h / suma de aportes de todas las hipótesis × 100.
        Grado de coincidencia = suma de aportes / máximo alcanzable por la hipótesis.
        RI-03: ante igual probabilidad, mayor número de coincidencias y luego menor código."""
        total = sum((f.suma_aportes for f in self._filas.values()), Decimal("0"))
        for fila in self._filas.values():
            fila.probabilidad = _redondear(fila.suma_aportes * 100 / total) if total else Decimal("0")
            fila.grado_coincidencia = min(Decimal("1"), _redondear(fila.suma_aportes / fila.maximo_alcanzable))
        return sorted(self._filas.values(),
                      key=lambda f: (-f.suma_aportes, -f.numero_coincidencias, f.codigo_hipotesis))


def seleccionar_cinco(contabilizacion) -> tuple:
    """RI-04: las cinco de mayor probabilidad; su probabilidad de resultado se reparte entre ellas (suma 100 %)."""
    cinco = tuple(contabilizacion[:NUMERO_HIPOTESIS_RESULTADO])
    suma = sum((f.suma_aportes for f in cinco), Decimal("0"))
    for fila in cinco:
        fila.probabilidad_resultado = _redondear(fila.suma_aportes * 100 / suma) if suma else Decimal("0")
    return cinco


class MotorInferencia:
    """Lo instancia SistemaExperto con los DAO de hechos, gránulos y reglas RN (en pruebas, con un repositorio en memoria)."""

    def __init__(self, hecho_dao, granulo_dao, regla_dao):
        self._hechos, self._granulos, self._reglas = hecho_dao, granulo_dao, regla_dao

    def inferir(self, respuestas) -> ResultadoInferencia:
        # RF-02 / RC: respuestas -> un hecho por variable del perfil (promedio, posición y grado).
        hechos, sin_hecho = self._hechos.derivar(respuestas)
        if sin_hecho:
            raise HechoNoDerivable(sin_hecho)

        # RF-03 / RG: una consulta granular por cada hecho; cada gránulo se contabiliza.
        tabla = TablaContabilizacion(self._granulos.maximos_por_hipotesis())
        for hecho in hechos:
            for granulo in self._granulos.por_hecho(hecho.id_hecho):
                tabla.registrar(granulo, hecho)

        # RF-03 / RI: probabilidades, grado de coincidencia y las cinco hipótesis.
        contabilizacion = tabla.calcular()
        cinco = seleccionar_cinco(contabilizacion)

        # RN: cada regla se evalúa con su métrica y su operador.
        cumple = lambda regla: OPERADORES[regla.operador](METRICAS[regla.metrica](regla, hechos, cinco), regla.umbral)
        marcas = tuple(filter(cumple, self._reglas.activas()))

        return ResultadoInferencia(tuple(hechos), tuple(contabilizacion), cinco, marcas)
