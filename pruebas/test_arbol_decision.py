"""Pruebas del recorrido del árbol de decisión que se anima en la página de resultado (sin base de datos).
Ejecutar desde la raíz del proyecto:  python -m unittest discover -s pruebas -v"""
import unittest
from decimal import Decimal

from app.modelo.arbol_decision import construir_recorrido

# Orden de las preguntas: áreas 1-4, intereses 5-10, estilo 11 (como en la base de conocimiento).
ORDEN = {"Desempeño Lógico-Matemática": 1, "Desempeño Científico-Investigativa": 2, "Interés Realista": 5,
         "Interés Investigativo": 6, "Interés Convencional": 10, "Estilo de trabajo": 11}
# Aspirante del ejemplo del documento: LM Alto, Investigativo Alto, Independiente.
HECHOS = {("Desempeño Lógico-Matemática", "Alto"), ("Interés Investigativo", "Alto"),
          ("Estilo de trabajo", "Independiente")}
RESPUESTAS = [{"variable": "Desempeño Lógico-Matemática", "valor_clasificado": "Alto"},
              {"variable": "Desempeño Científico-Investigativa", "valor_clasificado": "Medio"},
              {"variable": "Interés Realista", "valor_clasificado": "Medio"},
              {"variable": "Interés Investigativo", "valor_clasificado": "Alto"},
              {"variable": "Interés Convencional", "valor_clasificado": "Medio"},
              {"variable": "Estilo de trabajo", "valor_clasificado": "Independiente"}]
HIPOTESIS = [  # código, programa, posición (None si no quedó entre las cinco), probabilidad, (área, interés, estilo)
    ("H01", "Ingeniería de Software", 1, "15.63", ("Desempeño Lógico-Matemática", "Interés Investigativo", "Independiente")),
    ("H02", "Ingeniería de Sistemas", 2, "12.50", ("Desempeño Lógico-Matemática", "Interés Investigativo", "Equipo")),
    ("H03", "Ingeniería Mecánica", 3, "9.38", ("Desempeño Lógico-Matemática", "Interés Realista", "Independiente")),
    ("H04", "Ingeniería Industrial", None, "6.25", ("Desempeño Lógico-Matemática", "Interés Realista", "Equipo")),
    ("H05", "Estadística", 4, "9.38", ("Desempeño Lógico-Matemática", "Interés Convencional", "Independiente")),
    ("H07", "Biología", 5, "9.38", ("Desempeño Científico-Investigativa", "Interés Investigativo", "Independiente")),
    ("H12", "Ingeniería Agroindustrial", None, None, ("Desempeño Científico-Investigativa", "Interés Realista", "Equipo")),
]
REGLAS_RN = [{"codigo_regla": "RN-01", "descripcion": "Bajo rendimiento general", "cumple": False},
             {"codigo_regla": "RN-02", "descripcion": "Empate entre áreas", "cumple": False},
             {"codigo_regla": "RN-03", "descripcion": "Empate de interés", "cumple": False}]


def ramas():
    filas = []
    for cod, prog, pos, prob, (area, interes, estilo) in HIPOTESIS:
        granulos = ((area, "Alto", "0.40"), (interes, "Alto", "0.40"), ("Estilo de trabajo", estilo, "0.20"))
        coincidencias = sum((v, val) in HECHOS for v, val, _ in granulos)
        for variable, valor, peso in granulos:
            filas.append({"codigo": cod, "programa_academico": prog, "posicion": pos,
                          "probabilidad": Decimal(prob) if prob else None,
                          "numero_coincidencias": coincidencias or None, "variable": variable,
                          "valor_clasificado": valor, "peso": Decimal(peso),
                          "coincide": (variable, valor) in HECHOS, "orden": ORDEN[variable]})
    return filas[::-1]  # el orden de llegada no debe importar


def hojas(nodo):
    salida = []
    for h in nodo["hijos"]:
        salida += [h] if (h.get("hoja") or h.get("regla")) else hojas(h)
    return salida


class PruebasArbolDecision(unittest.TestCase):
    def setUp(self):
        self.arbol = construir_recorrido(ramas(), RESPUESTAS, REGLAS_RN)

    def test_primer_nivel_son_las_areas_y_la_rama_de_condiciones(self):
        primer_nivel = [(n.get("variable") or "condiciones", n["coincide"]) for n in self.arbol["hijos"]]
        self.assertEqual(primer_nivel, [("Desempeño Lógico-Matemática", True),
                                        ("Desempeño Científico-Investigativa", False), ("condiciones", False)])

    def test_camino_completo_de_la_primera_hipotesis(self):
        nodo, camino = self.arbol, []
        while not nodo.get("hoja"):
            nodo = nodo["hijos"][0]
            camino.append(nodo.get("codigo") or (nodo["variable"], nodo["valor"], nodo["coincide"]))
        self.assertEqual(camino, [("Desempeño Lógico-Matemática", "Alto", True), ("Interés Investigativo", "Alto", True),
                                  ("Estilo de trabajo", "Independiente", True), "H01"])
        self.assertEqual(self.arbol["niveles"], 4)

    def test_rama_que_no_coincide_muestra_el_nivel_del_aspirante(self):
        realista = self.arbol["hijos"][0]["hijos"][1]
        self.assertEqual((realista["variable"], realista["coincide"], realista["su_nivel"]), ("Interés Realista", False, "Medio"))
        self.assertEqual(realista["peso"], Decimal("0.40"))

    def test_incluye_todas_las_hipotesis_en_orden_de_codigo(self):
        programas = [h["codigo"] for h in hojas(self.arbol) if h.get("hoja")]
        self.assertEqual(programas, ["H01", "H02", "H03", "H04", "H05", "H07", "H12"])
        self.assertEqual(self.arbol["hojas"], 7)

    def test_hipotesis_fuera_de_las_cinco_y_sin_coincidencias(self):
        por_codigo = {h["codigo"]: h for h in hojas(self.arbol) if h.get("hoja")}
        self.assertIsNone(por_codigo["H04"]["posicion"])
        self.assertEqual(por_codigo["H04"]["numero_coincidencias"], 1)
        self.assertEqual((por_codigo["H12"]["numero_coincidencias"], por_codigo["H12"]["probabilidad"]), (0, None))

    def test_rama_de_condiciones_alineada_con_las_hojas(self):
        reglas = [h for h in hojas(self.arbol) if h.get("regla")]
        self.assertEqual([r["codigo"] for r in reglas], ["RN-01", "RN-02", "RN-03"])
        self.assertTrue(all(r["nivel"] == self.arbol["niveles"] for r in reglas))


class PruebasColumnaSinCoincidencias(unittest.TestCase):
    """Caso de la evaluación 4: áreas en Alto, pero todos los intereses en Bajo (se escribió 4 en lugar de un %)."""

    def test_columna_de_intereses_sin_coincidencias(self):
        hechos = {("Desempeño Lógico-Matemática", "Alto"), ("Estilo de trabajo", "Independiente")}
        filas = [{**f, "coincide": (f["variable"], f["valor_clasificado"]) in hechos} for f in ramas()]
        respuestas = [{**r, "valor_clasificado": "Bajo"} if r["variable"].startswith("Interés") else r for r in RESPUESTAS]
        arbol = construir_recorrido(filas, respuestas, REGLAS_RN)
        self.assertEqual(len(arbol["niveles_sin_coincidencia"]), 1)
        columna = arbol["niveles_sin_coincidencia"][0]
        self.assertEqual((columna["nivel"], columna["grupo"]), (2, "Interés"))
        self.assertEqual((columna["valores_con_peso"], columna["niveles_aspirante"]), (["Alto"], ["Bajo"]))

    def test_sin_nota_cuando_cada_columna_tiene_alguna_coincidencia(self):
        self.assertEqual(construir_recorrido(ramas(), RESPUESTAS, REGLAS_RN)["niveles_sin_coincidencia"], [])


if __name__ == "__main__":
    unittest.main()
