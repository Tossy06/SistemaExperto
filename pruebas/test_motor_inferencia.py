"""Pruebas del motor de inferencia con un repositorio en memoria (no requiere PostgreSQL).
Ejecutar desde la carpeta del proyecto:  python -m unittest discover -s pruebas -v"""
import unittest
from decimal import Decimal

from app.modelo.entidades import Granulo, Hecho, ReglaNoConcluyente, Respuesta
from app.modelo.motor_inferencia import MotorInferencia

AREAS = {"LM": "Lógico-Matemática", "CI": "Científico-Investigativa", "SH": "Social-Humanística", "AF": "Administrativo-Financiera"}
RAMAS = [("LM", "Investigativo", ["Ingeniería de Software", "Ingeniería de Sistemas"]), ("LM", "Realista", ["Ingeniería Mecánica", "Ingeniería Industrial"]),
         ("LM", "Convencional", ["Estadística", "Ingeniería Financiera"]), ("CI", "Investigativo", ["Biología", "Ingeniería Ambiental"]),
         ("CI", "Social", ["Nutrición y Dietética", "Enfermería"]), ("CI", "Realista", ["Química", "Ingeniería Agroindustrial"]),
         ("SH", "Social", ["Psicología", "Trabajo Social"]), ("SH", "Artístico", ["Diseño Gráfico", "Comunicación Social"]),
         ("SH", "Emprendedor", ["Derecho", "Ciencias Políticas"]), ("AF", "Emprendedor", ["Administración de Empresas", "Negocios Internacionales"]),
         ("AF", "Convencional", ["Contaduría Pública", "Economía"]), ("AF", "Social", ["Mercadeo", "Gestión del Talento Humano"])]


class RepositorioEnMemoria:
    """Réplica en memoria de la base de conocimiento: 32 hechos, 72 gránulos y 3 reglas RN."""
    def __init__(self):
        self.hechos, self.granulos, n = {}, {}, 0
        for nombre in AREAS.values():
            for nivel in ("Alto", "Medio", "Bajo"):
                n += 1; self.hechos[(f"Desempeño {nombre}", nivel)] = Hecho(n, f"H{n}", f"Desempeño {nombre}", "AREA", nivel)
        for cat in ("Realista", "Investigativo", "Artístico", "Social", "Emprendedor", "Convencional"):
            for nivel in ("Alto", "Medio", "Bajo"):
                n += 1; self.hechos[(f"Interés {cat}", nivel)] = Hecho(n, f"H{n}", f"Interés {cat}", "INTERES", nivel)
        for estilo in ("Independiente", "Equipo"):
            n += 1; self.hechos[("Estilo de trabajo", estilo)] = Hecho(n, f"H{n}", "Estilo de trabajo", "ESTILO", estilo)
        h = 0
        for area, interes, programas in RAMAS:
            for estilo, programa in zip(("Independiente", "Equipo"), programas):
                h += 1; codigo = f"H{h:02d}"
                for clave, peso in (((f"Desempeño {AREAS[area]}", "Alto"), "0.40"), ((f"Interés {interes}", "Alto"), "0.40"), (("Estilo de trabajo", estilo), "0.20")):
                    hecho = self.hechos[clave]
                    self.granulos.setdefault(hecho.id_hecho, []).append(Granulo("RG", hecho.id_hecho, h, codigo, programa, Decimal(peso)))
        self.consultas_granulares = 0

    def derivar(self, respuesta):          # en la prueba, la respuesta ya trae (variable, nivel)
        return self.hechos[respuesta.valor_opcion]

    def por_hecho(self, id_hecho):
        self.consultas_granulares += 1
        return self.granulos.get(id_hecho, [])

    def activas(self):
        return [ReglaNoConcluyente(1, "RN-01", "Bajo rendimiento general", "AREA", "Bajo", "=", 4),
                ReglaNoConcluyente(2, "RN-02", "Empate entre áreas", "AREA", "Alto", ">=", 2),
                ReglaNoConcluyente(3, "RN-03", "Empate de interés", "INTERES", "Alto", ">=", 2)]


def perfil(areas, intereses, estilo):
    hechos = [(f"Desempeño {AREAS[a]}", n) for a, n in areas.items()] + [(f"Interés {c}", n) for c, n in intereses.items()] + [("Estilo de trabajo", estilo)]
    return [Respuesta(i, valor_opcion=h) for i, h in enumerate(hechos, start=1)]


EJEMPLO = perfil({"LM": "Alto", "CI": "Medio", "SH": "Bajo", "AF": "Medio"},
                 {"Realista": "Medio", "Investigativo": "Alto", "Artístico": "Bajo", "Social": "Medio", "Emprendedor": "Bajo", "Convencional": "Medio"},
                 "Independiente")


class PruebasMotorInferencia(unittest.TestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()
        self.motor = MotorInferencia(self.repo, self.repo, self.repo)

    def test_ejemplo_del_documento(self):
        r = self.motor.inferir(EJEMPLO)
        self.assertEqual([h.codigo_hipotesis for h in r.cinco_hipotesis], ["H01", "H02", "H03", "H05", "H07"])
        self.assertEqual([h.probabilidad for h in r.cinco_hipotesis],
                         [Decimal("15.6250"), Decimal("12.5000"), Decimal("9.3750"), Decimal("9.3750"), Decimal("9.3750")])
        self.assertEqual(r.cinco_hipotesis[0].numero_coincidencias, 3)
        self.assertFalse(r.resultado_no_concluyente)

    def test_una_consulta_granular_por_hecho(self):
        self.motor.inferir(EJEMPLO)
        self.assertEqual(self.repo.consultas_granulares, 11)

    def test_probabilidades_suman_100(self):
        r = self.motor.inferir(EJEMPLO)
        self.assertAlmostEqual(float(sum(c.probabilidad for c in r.contabilizacion)), 100.0, delta=0.01)

    def test_empate_entre_areas_marca_no_concluyente(self):
        r = self.motor.inferir(perfil({"LM": "Alto", "CI": "Alto", "SH": "Bajo", "AF": "Bajo"},
                                      {"Investigativo": "Alto", "Realista": "Bajo", "Artístico": "Bajo", "Social": "Bajo", "Emprendedor": "Bajo", "Convencional": "Bajo"},
                                      "Equipo"))
        self.assertEqual([m.codigo_regla for m in r.marcas_no_concluyente], ["RN-02"])

    def test_bajo_rendimiento_general(self):
        r = self.motor.inferir(perfil({"LM": "Bajo", "CI": "Bajo", "SH": "Bajo", "AF": "Bajo"},
                                      {"Investigativo": "Alto", "Realista": "Alto", "Artístico": "Bajo", "Social": "Bajo", "Emprendedor": "Bajo", "Convencional": "Bajo"},
                                      "Equipo"))
        self.assertEqual([m.codigo_regla for m in r.marcas_no_concluyente], ["RN-01", "RN-03"])
        self.assertEqual(len(r.cinco_hipotesis), 5)


if __name__ == "__main__":
    unittest.main()
