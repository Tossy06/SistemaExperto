"""Motor de inferencia con encadenamiento hacia adelante.

Ciclo: se buscan las reglas cuyas condiciones se cumplen en la memoria de trabajo, se disparan todas
y se repite hasta que ninguna regla nueva pueda dispararse. Todo el conocimiento viene del JSON:
aquí no hay condicionales sobre programas, áreas ni categorías RIASEC.
"""
import operator
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

NUMERO_HIPOTESIS_RESULTADO = 5
OPERADORES = {"=": operator.eq, ">=": operator.ge}
_CUANTO = Decimal("0.0001")


class ErroresValidacion(Exception):
    """Errores por pregunta: {codigo_variable: mensaje}."""

    def __init__(self, errores):
        super().__init__("Hay respuestas con errores.")
        self.errores = errores


@dataclass(frozen=True)
class Hecho:
    codigo: str
    variable: str
    nombre_variable: str
    tipo_variable: str
    valor: str

    @property
    def descripcion(self):
        return f"{self.nombre_variable} = {self.valor}"


class Evidencia:
    """Acumulado de una hipótesis: coincidencias, pesos y reglas que la apoyaron."""

    def __init__(self, codigo, programa):
        self.codigo = codigo
        self.programa = programa
        self.coincidencias = 0
        self.suma_pesos = Decimal("0")
        self.reglas = []
        self.probabilidad = Decimal("0")


class MemoriaTrabajo:
    def __init__(self, respuestas):
        self.respuestas = respuestas      # {codigo_variable: Decimal o str}
        self.hechos = {}                  # {codigo_hecho: Hecho}
        self.evidencias = {}              # {codigo_hipotesis: Evidencia}
        self.marcas = []                  # reglas RN que se cumplieron

    def contar_hechos(self, tipo_variable, valor):
        return sum(h.tipo_variable == tipo_variable and h.valor == valor for h in self.hechos.values())


@dataclass(frozen=True)
class ReglaRango:
    """RC numérica: SI minimo <= respuesta <= maximo ENTONCES se afirma el hecho."""
    codigo: str
    hecho: Hecho
    minimo: Decimal
    maximo: Decimal

    def aplica(self, memoria):
        return self.minimo <= memoria.respuestas[self.hecho.variable] <= self.maximo

    def disparar(self, memoria):
        memoria.hechos[self.hecho.codigo] = self.hecho


@dataclass(frozen=True)
class ReglaOpcion:
    """RC de opción: SI respuesta = valor ENTONCES se afirma el hecho."""
    codigo: str
    hecho: Hecho

    def aplica(self, memoria):
        return memoria.respuestas[self.hecho.variable] == self.hecho.valor

    def disparar(self, memoria):
        memoria.hechos[self.hecho.codigo] = self.hecho


@dataclass(frozen=True)
class ReglaGranulo:
    """RG: SI el hecho está en memoria ENTONCES suma su peso a la hipótesis."""
    codigo: str
    hecho: str
    hipotesis: str
    programa: str
    peso: Decimal

    def aplica(self, memoria):
        return self.hecho in memoria.hechos

    def disparar(self, memoria):
        evidencia = memoria.evidencias.setdefault(self.hipotesis, Evidencia(self.hipotesis, self.programa))
        evidencia.coincidencias += 1
        evidencia.suma_pesos += self.peso
        evidencia.reglas.append({"regla": self.codigo, "hecho": memoria.hechos[self.hecho].descripcion,
                                 "peso": float(self.peso)})


@dataclass(frozen=True)
class ReglaNoConcluyente:
    """RN: SI la cantidad de hechos (tipo, valor) cumple el operador ENTONCES marca el resultado."""
    codigo: str
    descripcion: str
    tipo_variable: str
    valor_hecho: str
    operador: str
    cantidad: int

    def aplica(self, memoria):
        conteo = memoria.contar_hechos(self.tipo_variable, self.valor_hecho)
        return OPERADORES[self.operador](conteo, self.cantidad)

    def disparar(self, memoria):
        memoria.marcas.append({"codigo": self.codigo, "descripcion": self.descripcion})


def _numero(pregunta, texto):
    try:
        valor = Decimal(texto.replace(",", "."))
    except InvalidOperation:
        raise ValueError("Debe ingresar un número.")
    minimo, maximo = Decimal(str(pregunta["minimo"])), Decimal(str(pregunta["maximo"]))
    if not valor.is_finite() or not minimo <= valor <= maximo:
        raise ValueError(f"El valor debe estar entre {pregunta['minimo']} y {pregunta['maximo']}.")
    return valor.quantize(Decimal("0.01"))


def _opcion(pregunta, texto):
    opciones = {o.lower(): o for o in pregunta["opciones"]}
    if texto.lower() not in opciones:
        raise ValueError(f"Opciones válidas: {', '.join(pregunta['opciones'])}.")
    return opciones[texto.lower()]


VALIDADORES = {"NUMERICA": _numero, "OPCION": _opcion}


class BaseConocimiento:
    """Convierte el JSON de la base de conocimiento en preguntas y reglas ejecutables."""

    def __init__(self, datos):
        self.version = datos["version"]
        variables = {v["codigo"]: v for v in datos["variables"]}
        programas = {h["codigo"]: h["programa"] for h in datos["hipotesis"]}

        opciones = defaultdict(list)
        clasificacion = []
        for dato in datos["hechos"]:
            variable = variables[dato["variable"]]
            hecho = Hecho(dato["codigo"], variable["codigo"], variable["nombre"],
                          variable["tipo_variable"], dato["valor"])
            codigo = f"RC-{dato['codigo']}"
            if dato["minimo"] is None:
                opciones[variable["codigo"]].append(dato["valor"])
                clasificacion.append(ReglaOpcion(codigo, hecho))
            else:
                clasificacion.append(ReglaRango(codigo, hecho, Decimal(str(dato["minimo"])),
                                                Decimal(str(dato["maximo"]))))

        granulos = [ReglaGranulo(r["codigo"], r["hecho"], r["hipotesis"], programas[r["hipotesis"]],
                                 Decimal(str(r["peso"]))) for r in datos["reglas_granulo"]]
        no_concluyente = [ReglaNoConcluyente(r["codigo"], r["descripcion"], r["tipo_variable"],
                                             r["valor_hecho"], r["operador"], r["cantidad"])
                          for r in datos["reglas_no_concluyente"]]

        self.reglas = clasificacion + granulos + no_concluyente
        self.preguntas = [{**v, "opciones": opciones[v["codigo"]]}
                          for v in sorted(datos["variables"], key=lambda v: v["orden"])]
        self.resumen = {"version": self.version, "preguntas": len(self.preguntas),
                        "hechos": len(clasificacion), "hipotesis": len(programas),
                        "reglas_granulo": len(granulos), "reglas_no_concluyente": len(no_concluyente)}

    def validar(self, respuestas):
        """Devuelve {codigo_variable: valor} o lanza ErroresValidacion con todos los errores."""
        validas, errores = {}, {}
        for pregunta in self.preguntas:
            codigo = pregunta["codigo"]
            texto = respuestas.get(codigo, "").strip()
            try:
                if not texto:
                    raise ValueError("La respuesta es obligatoria.")
                validas[codigo] = VALIDADORES[pregunta["tipo_respuesta"]](pregunta, texto)
            except ValueError as error:
                errores[codigo] = str(error)
        if errores:
            raise ErroresValidacion(errores)
        return validas


class MotorInferencia:
    def __init__(self, base):
        self._base = base

    def inferir(self, respuestas):
        memoria = MemoriaTrabajo(self._base.validar(respuestas))
        disparadas, traza = set(), []

        while True:
            # Se arma el conjunto completo antes de disparar, para que cada ciclo vea la misma memoria.
            conjunto = [r for r in self._base.reglas if r.codigo not in disparadas and r.aplica(memoria)]
            if not conjunto:
                break
            for regla in conjunto:
                regla.disparar(memoria)
                disparadas.add(regla.codigo)
            traza.append({"ciclo": len(traza) + 1, "reglas": [r.codigo for r in conjunto]})

        contabilizacion = self._contabilizar(memoria)
        return {
            "hechos": [{"codigo": h.codigo, "descripcion": h.descripcion} for h in memoria.hechos.values()],
            "recomendaciones": contabilizacion[:NUMERO_HIPOTESIS_RESULTADO],
            "contabilizacion": contabilizacion,
            "no_concluyente": bool(memoria.marcas),
            "marcas": memoria.marcas,
            "traza": traza,
        }

    @staticmethod
    def _contabilizar(memoria):
        """P(h) = pesos de h / pesos de todas las hipótesis x 100.
        Desempate: mayor número de coincidencias y luego menor código."""
        evidencias = list(memoria.evidencias.values())
        total = sum((e.suma_pesos for e in evidencias), Decimal("0"))
        for evidencia in evidencias:
            evidencia.probabilidad = (evidencia.suma_pesos * 100 / total).quantize(_CUANTO, rounding=ROUND_HALF_UP)
        evidencias.sort(key=lambda e: (-e.probabilidad, -e.coincidencias, e.codigo))
        return [{"codigo": e.codigo, "programa": e.programa, "probabilidad": float(e.probabilidad),
                 "coincidencias": e.coincidencias, "suma_pesos": float(e.suma_pesos), "reglas": e.reglas}
                for e in evidencias]
