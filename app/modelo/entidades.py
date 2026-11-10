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
    codigo_variable: str
    nombre_variable: str
    tipo_variable: str             # AREA, INTERES o ESTILO
    tipo_respuesta: str            # NUMERICA u OPCION
    enunciado: str
    valor_minimo: Optional[Decimal]
    valor_maximo: Optional[Decimal]
    opciones: tuple = ()           # valores válidos cuando tipo_respuesta = OPCION


@dataclass(frozen=True)
class Respuesta:
    id_pregunta: int
    valor_numerico: Optional[Decimal] = None
    valor_opcion: Optional[str] = None


@dataclass(frozen=True)
class Hecho:
    id_hecho: int
    codigo: str
    variable: str
    tipo_variable: str             # AREA, INTERES o ESTILO
    valor_clasificado: str         # Alto, Medio, Bajo, Independiente o Equipo

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
    tipo_variable: str
    valor_hecho: str
    operador: str                  # '=' o '>='
    cantidad: int


@dataclass
class ConteoHipotesis:
    """Fila de la tabla de contabilización de coincidencias para una hipótesis."""
    id_hipotesis: int
    codigo_hipotesis: str
    programa_academico: str
    numero_coincidencias: int = 0
    suma_pesos: Decimal = Decimal("0")
    probabilidad: Decimal = Decimal("0")
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
