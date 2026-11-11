"""Pruebas del motor de inferencia con un repositorio en memoria (no requiere PostgreSQL).
El repositorio replica la base de conocimiento (39 hechos, 168 gránulos, 3 reglas RN) y la consulta de
derivación de hechos (promedio, posición con empates compartidos y grado de certeza).
Ejecutar desde la carpeta del proyecto:  python -m unittest discover -s pruebas -v"""
import unittest
from decimal import Decimal, ROUND_HALF_UP

from app.modelo.entidades import Granulo, Hecho, ReglaNoConcluyente, Respuesta
from app.modelo.motor_inferencia import HechoNoDerivable, MotorInferencia

AREAS = {"LM": "Lógico-Matemática", "CI": "Científico-Investigativa", "SH": "Social-Humanística", "AF": "Administrativo-Financiera"}
RIASEC = {"R": "Realista", "I": "Investigativo", "A": "Artístico", "S": "Social", "E": "Emprendedor", "C": "Convencional"}
RAMAS = [("LM", "I"), ("LM", "R"), ("LM", "C"), ("CI", "I"), ("CI", "S"), ("CI", "R"),
         ("SH", "S"), ("SH", "A"), ("SH", "E"), ("AF", "E"), ("AF", "C"), ("AF", "S")]
DOS = Decimal("0.01")

# Variables: (código, nombre, tipo, criterio, pondera intensidad, preguntas, máximo)
VARIABLES = ([(f"DES-{a}", f"Desempeño {n}", "AREA", "RANGO", True, 1, 5) for a, n in AREAS.items()]
             + [(f"INT-{c}", f"Interés {n}", "INTERES", "POSICION", True, 3, 5) for c, n in RIASEC.items()]
             + [("EST", "Estilo de trabajo", "ESTILO", "RANGO", False, 1, 5)])
RANGOS = {"AREA": [("ALT", "Alto", 4, 5), ("MED", "Medio", Decimal("3.5"), Decimal("3.99")), ("BAJ", "Bajo", 1, Decimal("3.49"))],
          "INTERES": [("P1", "Primera", 1, 1), ("P2", "Segunda", 2, 2), ("P3", "Tercera", 3, 3), ("P4", "Posterior", 4, 6)],
          "ESTILO": [("IND", "Independiente", 1, Decimal("2.49")), ("NEU", "Indistinto", Decimal("2.5"), Decimal("3.49")),
                     ("EQU", "Equipo", Decimal("3.5"), 5)]}


class RepositorioEnMemoria:
    """Réplica en memoria de la base de conocimiento y de la consulta de derivación."""

    def __init__(self):
        self.preguntas, self.hechos, n = {}, {}, 0          # id_pregunta -> variable; (variable, código) -> Hecho
        for codigo, nombre, tipo, criterio, pondera, cantidad, maximo in VARIABLES:
            for _ in range(cantidad):
                n += 1
                self.preguntas[n] = codigo
        self.variables = {v[0]: v for v in VARIABLES}
        n = 0
        for codigo, nombre, tipo, *_ in VARIABLES:
            for sufijo, valor, minimo, maximo in RANGOS[tipo]:
                n += 1
                self.hechos[(codigo, sufijo)] = (Hecho(n, f"{codigo}-{sufijo}", nombre, tipo, valor), Decimal(minimo), Decimal(maximo))
        self.granulos, h, k = {}, 0, 0
        for area, interes in RAMAS:
            for estilo in ("IND", "EQU"):
                h += 1
                for (variable, sufijo), peso in (((f"DES-{area}", "ALT"), "0.40"), ((f"DES-{area}", "MED"), "0.20"),
                                                 ((f"INT-{interes}", "P1"), "0.40"), ((f"INT-{interes}", "P2"), "0.25"),
                                                 ((f"INT-{interes}", "P3"), "0.10"), (("EST", estilo), "0.20"), (("EST", "NEU"), "0.10")):
                    hecho, k = self.hechos[(variable, sufijo)][0], k + 1
                    self.granulos.setdefault(hecho.id_hecho, []).append(
                        Granulo(f"RG-{k:03d}", hecho.id_hecho, h, f"H{h:02d}", f"Programa {h}", Decimal(peso)))
        self.consultas_granulares = 0

    def derivar(self, respuestas):
        valores = {}
        for r in respuestas:
            valores.setdefault(self.preguntas[r.id_pregunta], []).append(r.valor)
        promedios = {c: (sum(v) / len(v)).quantize(DOS, rounding=ROUND_HALF_UP) for c, v in valores.items()}
        hechos, sin_hecho = [], []
        for codigo, promedio in promedios.items():
            _, nombre, tipo, criterio, pondera, _, maximo = self.variables[codigo]
            distintos = sorted({p for c, p in promedios.items() if self.variables[c][2] == tipo}, reverse=True)
            posicion = distintos.index(promedio) + 1                     # DENSE_RANK
            comparado = Decimal(posicion) if criterio == "POSICION" else promedio
            grado = (promedio / maximo).quantize(Decimal("0.0001")) if pondera else Decimal("1")
            encontrado = [h for (c, _), (h, mi, ma) in self.hechos.items() if c == codigo and mi <= comparado <= ma]
            if not encontrado:
                sin_hecho.append(codigo)
                continue
            base = encontrado[0]
            hechos.append(Hecho(base.id_hecho, base.codigo, base.variable, base.tipo_variable, base.valor_clasificado,
                                promedio, posicion, grado))
        return hechos, sin_hecho

    def por_hecho(self, id_hecho):
        self.consultas_granulares += 1
        return self.granulos.get(id_hecho, [])

    def maximos_por_hipotesis(self):
        return {h: Decimal("1.00") for h in range(1, 25)}

    def activas(self):
        return [ReglaNoConcluyente(1, "RN-01", "Cuatro áreas en Bajo", "CONTEO_HECHOS", "AREA", "Bajo", "=", Decimal(4)),
                ReglaNoConcluyente(2, "RN-02", "Intereses sin diferenciar", "CONTEO_HECHOS", "INTERES", "Primera", ">=", Decimal(3)),
                ReglaNoConcluyente(3, "RN-03", "Coincidencia baja", "COINCIDENCIA_PRIMERA", None, None, "<", Decimal("0.50"))]


def respuestas(notas, intereses, estilo):
    """notas: 4 valores; intereses: {R: (a, b, c), ...} en orden RIASEC; estilo: 1 a 5."""
    valores = list(notas) + [v for c in RIASEC for v in intereses[c]] + [estilo]
    return [Respuesta(i, Decimal(str(v))) for i, v in enumerate(valores, start=1)]


EJEMPLO = respuestas((4.5, 3.7, 3.4, 3.9),
                     {"R": (4, 3, 4), "I": (5, 4, 4), "A": (2, 1, 2), "S": (3, 4, 3), "E": (2, 3, 2), "C": (3, 3, 3)}, 2)


class PruebasMotorInferencia(unittest.TestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()
        self.motor = MotorInferencia(self.repo, self.repo, self.repo)

    def test_ejemplo_del_documento(self):
        r = self.motor.inferir(EJEMPLO)
        self.assertEqual([h.codigo_hipotesis for h in r.cinco_hipotesis], ["H01", "H03", "H02", "H07", "H05"])
        primera = r.cinco_hipotesis[0]
        self.assertEqual(primera.suma_aportes, Decimal("0.9064"))      # 0,40×0,90 + 0,40×0,866 + 0,20×1
        self.assertEqual(primera.grado_coincidencia, Decimal("0.9064"))
        self.assertEqual(primera.probabilidad_resultado, Decimal("25.1032"))
        self.assertFalse(r.resultado_no_concluyente)

    def test_codigo_holland_por_posicion(self):
        hechos = {h.codigo: h for h in self.motor.inferir(EJEMPLO).hechos}
        self.assertEqual(hechos["INT-I-P1"].posicion, 1)
        self.assertEqual(hechos["INT-R-P2"].valor_clasificado, "Segunda")
        self.assertEqual(hechos["INT-S-P3"].valor_clasificado, "Tercera")
        self.assertIn("INT-A-P4", hechos)

    def test_una_consulta_granular_por_hecho(self):
        self.motor.inferir(EJEMPLO)
        self.assertEqual(self.repo.consultas_granulares, 11)

    def test_probabilidades(self):
        r = self.motor.inferir(EJEMPLO)
        self.assertAlmostEqual(float(sum(c.probabilidad for c in r.contabilizacion)), 100.0, delta=0.01)
        self.assertAlmostEqual(float(sum(c.probabilidad_resultado for c in r.cinco_hipotesis)), 100.0, delta=0.01)

    def test_medio_tambien_suma(self):
        """Un área Medio aporta (0,20 × grado): Biología entra con Científico-Investigativa = Medio."""
        biologia = next(c for c in self.motor.inferir(EJEMPLO).contabilizacion if c.codigo_hipotesis == "H07")
        self.assertIn(("Desempeño Científico-Investigativa = Medio", Decimal("0.20"), Decimal("0.7400"), Decimal("0.1480"), "RG-044"),
                      [tuple(x) for x in biologia.hechos_coincidentes])

    def test_cuatro_areas_en_bajo(self):
        r = self.motor.inferir(respuestas((3.0, 2.8, 3.2, 3.4),
                                          {"R": (2, 2, 2), "I": (5, 5, 4), "A": (1, 1, 1), "S": (2, 3, 2), "E": (1, 2, 1), "C": (3, 2, 3)}, 4))
        self.assertIn("RN-01", [m.codigo_regla for m in r.marcas_no_concluyente])
        self.assertEqual(len(r.cinco_hipotesis), 5)

    def test_intereses_sin_diferenciar(self):
        r = self.motor.inferir(respuestas((4.5, 4.2, 3.0, 3.0),
                                          {c: (3, 3, 3) for c in RIASEC}, 1))
        self.assertIn("RN-02", [m.codigo_regla for m in r.marcas_no_concluyente])

    def test_coincidencia_baja(self):
        r = self.motor.inferir(respuestas((3.6, 3.5, 3.0, 2.0),
                                          {"R": (1, 1, 2), "I": (1, 2, 1), "A": (2, 1, 1), "S": (1, 1, 1), "E": (2, 2, 2), "C": (1, 1, 1)}, 3))
        self.assertLess(r.cinco_hipotesis[0].grado_coincidencia, Decimal("0.50"))
        self.assertIn("RN-03", [m.codigo_regla for m in r.marcas_no_concluyente])

    def test_valor_sin_rango(self):
        with self.assertRaises(HechoNoDerivable) as error:
            self.motor.inferir(respuestas((4.5, 3.7, 3.4, 5.5),
                                          {"R": (4, 3, 4), "I": (5, 4, 4), "A": (2, 1, 2), "S": (3, 4, 3), "E": (2, 3, 2), "C": (3, 3, 3)}, 2))
        self.assertEqual(error.exception.codigos_variable, ("DES-AF",))


if __name__ == "__main__":
    unittest.main()
