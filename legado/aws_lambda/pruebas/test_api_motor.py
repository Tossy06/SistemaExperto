"""Pruebas del motor de la API y del JSON de la base de conocimiento (sin AWS ni PostgreSQL)."""
import json
import sys
import unittest
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "api"))

from motor import BaseConocimiento, ErroresValidacion, MotorInferencia

DATOS = json.loads((RAIZ / "base_conocimiento" / "base_conocimiento.json").read_text(encoding="utf-8"))
EJEMPLO = {"DES-LM": "4.5", "DES-CI": "3.7", "DES-SH": "3.0", "DES-AF": "3.6",
           "INT-R": "50", "INT-I": "85", "INT-A": "20", "INT-S": "45", "INT-E": "30", "INT-C": "55",
           "EST": "Independiente"}


class PruebasMotorApi(unittest.TestCase):
    def setUp(self):
        self.motor = MotorInferencia(BaseConocimiento(DATOS))

    def test_base_conocimiento_completa(self):
        self.assertEqual(BaseConocimiento(DATOS).resumen, {
            "version": "1.0", "preguntas": 11, "hechos": 32, "hipotesis": 24,
            "reglas_granulo": 72, "reglas_no_concluyente": 3})
        pesos = defaultdict(Decimal)
        for regla in DATOS["reglas_granulo"]:
            pesos[regla["hipotesis"]] += Decimal(str(regla["peso"]))
        self.assertEqual(set(pesos.values()), {Decimal("1.00")})

    def test_mismo_resultado_que_el_motor_original(self):
        r = self.motor.inferir(EJEMPLO)
        self.assertEqual([h["codigo"] for h in r["recomendaciones"]], ["H01", "H02", "H03", "H05", "H07"])
        self.assertEqual([h["probabilidad"] for h in r["recomendaciones"]], [15.625, 12.5, 9.375, 9.375, 9.375])
        self.assertAlmostEqual(sum(h["probabilidad"] for h in r["contabilizacion"]), 100.0, delta=0.01)
        self.assertFalse(r["no_concluyente"])

    def test_encadenamiento_por_ciclos(self):
        traza = self.motor.inferir(EJEMPLO)["traza"]
        self.assertEqual(len(traza), 2)
        self.assertEqual(len(traza[0]["reglas"]), 11)      # ciclo 1: respuestas -> hechos
        self.assertEqual(len(traza[1]["reglas"]), 22)      # ciclo 2: hechos -> hipótesis

    def test_nota_en_el_antiguo_hueco_de_rangos(self):
        hechos = [h["codigo"] for h in self.motor.inferir({**EJEMPLO, "DES-LM": "3.95", "DES-AF": "3,45"})["hechos"]]
        self.assertIn("DES-LM-MED", hechos)
        self.assertIn("DES-AF-BAJ", hechos)

    def test_reglas_no_concluyente(self):
        r = self.motor.inferir({**EJEMPLO, "DES-LM": "2", "DES-CI": "2", "DES-SH": "2", "DES-AF": "2",
                                "INT-R": "90"})
        self.assertEqual([m["codigo"] for m in r["marcas"]], ["RN-01", "RN-03"])
        self.assertTrue(r["no_concluyente"])

    def test_validacion_reporta_cada_pregunta(self):
        with self.assertRaises(ErroresValidacion) as contexto:
            self.motor.inferir({**EJEMPLO, "DES-LM": "9", "INT-R": "NaN", "EST": "Otro", "INT-C": ""})
        self.assertEqual(set(contexto.exception.errores), {"DES-LM", "INT-R", "EST", "INT-C"})


if __name__ == "__main__":
    unittest.main()
