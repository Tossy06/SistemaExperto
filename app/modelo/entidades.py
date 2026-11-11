"""Entidades del dominio del sistema experto (sin lógica de presentación ni de acceso a datos)."""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Aspirante:
    id_aspirante: int
    documento: str
    nombres: str
    apellidos: str
    correo: str


@dataclass(frozen=True)
class IngenieroConocimiento:
    id_ingeniero: int
    documento: str
    nombres: str
    apellidos: str
    correo: str


@dataclass(frozen=True)
class Pregunta:
    id_pregunta: int
    codigo: str                    # P01 ... P23 (nombre del campo en el formulario)
    codigo_variable: str           # variable del perfil que mide (DES-LM, INT-I, EST)
    nombre_variable: str
    tipo_variable: str             # AREA, INTERES o ESTILO
    tipo_respuesta: str            # NUMERICA (nota con decimales) o ESCALA (entero de 1 a 5)
    enunciado: str
    valor_minimo: Decimal
    valor_maximo: Decimal
    etiqueta_minima: Optional[str] = None
    etiqueta_maxima: Optional[str] = None


@dataclass(frozen=True)
class Respuesta:
    id_pregunta: int
    valor: Decimal


@dataclass(frozen=True)
class Hecho:
    """Hecho del perfil derivado de las respuestas (RF-02), con su grado de certeza."""
    id_hecho: int
    codigo: str
    variable: str
    tipo_variable: str             # AREA, INTERES o ESTILO
    valor_clasificado: str         # Alto, Medio, Bajo, Primera, Segunda, Tercera, Posterior, Independiente, ...
    valor_calculado: Decimal = Decimal("0")   # promedio de las preguntas de la variable
    posicion: int = 1              # lugar frente a las variables del mismo tipo
    grado: Decimal = Decimal("1")  # factor de certeza (0 a 1]

    def descripcion(self) -> str:
        return f"{self.variable} = {self.valor_clasificado}"


@dataclass(frozen=True)
class Granulo:
    codigo_regla: str
    id_hecho: int
    id_hipotesis: int
    codigo_hipotesis: str
    programa_academico: str
    peso: Decimal


@dataclass(frozen=True)
class ReglaNoConcluyente:
    id_regla: int
    codigo_regla: str
    descripcion: str
    metrica: str                   # CONTEO_HECHOS o COINCIDENCIA_PRIMERA
    tipo_variable: Optional[str]   # solo para CONTEO_HECHOS
    valor_hecho: Optional[str]
    operador: str                  # '=', '>=' o '<'
    umbral: Decimal


@dataclass
class ConteoHipotesis:
    """Fila de la tabla de contabilización de coincidencias para una hipótesis."""
    id_hipotesis: int
    codigo_hipotesis: str
    programa_academico: str
    numero_coincidencias: int = 0
    suma_aportes: Decimal = Decimal("0")          # suma de peso x grado de los gránulos que coinciden
    maximo_alcanzable: Decimal = Decimal("1")     # suma que tendría un perfil ideal para esta hipótesis
    grado_coincidencia: Decimal = Decimal("0")    # suma_aportes / maximo_alcanzable (0 a 1)
    probabilidad: Decimal = Decimal("0")          # frente a todas las hipótesis contabilizadas
    probabilidad_resultado: Decimal = Decimal("0")  # entre las cinco presentadas (solo las cinco)
    hechos_coincidentes: list = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoInferencia:
    hechos: tuple                  # hechos derivados de las respuestas (RF-02)
    contabilizacion: tuple         # ConteoHipotesis ordenados (RF-03)
    cinco_hipotesis: tuple         # las cinco de mayor probabilidad (RF-03)
    marcas_no_concluyente: tuple   # reglas RN que se cumplieron

    @property
    def resultado_no_concluyente(self) -> bool:
        return len(self.marcas_no_concluyente) > 0
