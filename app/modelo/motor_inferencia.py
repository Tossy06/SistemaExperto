"""
Motor de inferencia probabilístico del sistema experto.

No contiene condicionales sobre programas académicos, áreas, categorías RIASEC ni valores de las
variables (RNF-03). Todo el conocimiento se obtiene de la base de conocimiento mediante
consultas sucesivas y granulares: una consulta por cada respuesta (derivación del hecho) y una consulta
por cada hecho (gránulos asociados).
"""
import operator
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

from app.config import DECIMALES_CALCULO, NUMERO_HIPOTESIS_RESULTADO
from app.modelo.entidades import ConteoHipotesis, ResultadoInferencia

# Operadores de las reglas RN, resueltos por tabla (despacho) y no con if/else.
OPERADORES = {"=": operator.eq, ">=": operator.ge}
_CUANTO = Decimal(1).scaleb(-DECIMALES_CALCULO)        # 0.0001


class HechoNoDerivable(Exception):
    """Ningún rango de la base de conocimiento contiene el valor respondido."""

    def __init__(self, id_pregunta):
        super().__init__("El valor no corresponde a ningún rango de clasificación.")
        self.id_pregunta = id_pregunta


class TablaContabilizacion:
    """Tabla de contabilización de coincidencias para las hipótesis (RF-03)."""

    def __init__(self):
        self._filas = {}

    def registrar(self, granulo, hecho):
        fila = self._filas.setdefault(granulo.id_hipotesis, ConteoHipotesis(
            granulo.id_hipotesis, granulo.codigo_hipotesis, granulo.programa_academico))
        fila.numero_coincidencias += 1
        fila.suma_pesos += granulo.peso
        fila.hechos_coincidentes.append((hecho.descripcion(), granulo.peso, granulo.codigo_regla))

    def calcular_probabilidades(self) -> list:
        """RF-03 / RI-02: P(h) = suma de pesos de h / suma de pesos de todas las hipótesis × 100.
        RI-03: ante igual probabilidad, mayor número de coincidencias y luego menor código."""
        total = sum((f.suma_pesos for f in self._filas.values()), Decimal("0"))
        for fila in self._filas.values():
            fila.probabilidad = (fila.suma_pesos * 100 / total).quantize(_CUANTO, rounding=ROUND_HALF_UP) if total else Decimal("0")
        return sorted(self._filas.values(),
                      key=lambda f: (-f.probabilidad, -f.numero_coincidencias, f.codigo_hipotesis))


class MotorInferencia:
    """Lo instancia SistemaExperto con los DAO de hechos, gránulos y reglas RN (en pruebas, con un repositorio en memoria)."""

    def __init__(self, hecho_dao, granulo_dao, regla_dao):
        self._hechos, self._granulos, self._reglas = hecho_dao, granulo_dao, regla_dao

    def _derivar(self, respuesta):
        hecho = self._hechos.derivar(respuesta)
        if hecho is None:
            raise HechoNoDerivable(respuesta.id_pregunta)
        return hecho

    def inferir(self, respuestas) -> ResultadoInferencia:
        # RF-02: una consulta por cada respuesta -> un hecho.
        hechos = [self._derivar(r) for r in respuestas]

        # RF-03: una consulta granular por cada hecho; cada gránulo se contabiliza.
        tabla = TablaContabilizacion()
        for hecho in hechos:
            for granulo in self._granulos.por_hecho(hecho.id_hecho):
                tabla.registrar(granulo, hecho)

        # RF-03: probabilidades y selección de las cinco hipótesis (RI-02 a RI-04).
        contabilizacion = tabla.calcular_probabilidades()
        cinco = contabilizacion[:NUMERO_HIPOTESIS_RESULTADO]

        # Reglas RN: se cuentan los hechos por (tipo de variable, valor).
        conteo = Counter((h.tipo_variable, h.valor_clasificado) for h in hechos)
        cumple = lambda regla: OPERADORES[regla.operador](
            conteo[(regla.tipo_variable, regla.valor_hecho)], regla.cantidad)
        marcas = tuple(filter(cumple, self._reglas.activas()))

        return ResultadoInferencia(tuple(hechos), tuple(contabilizacion), tuple(cinco), marcas)
