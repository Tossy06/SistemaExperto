"""Pruebas de la capa web que no necesitan PostgreSQL: protección de rutas por rol y CSRF.
Ejecutar desde la raíz del proyecto:  python -m unittest discover -s pruebas -v"""
import unittest

from app import crear_app


class FabricaSinBase:
    """Sustituye al pool: si alguna ruta intentara consultar la base, la prueba fallaría."""
    def obtener(self):
        raise AssertionError("La ruta no debería consultar la base de datos")

    def devolver(self, conexion):
        pass


class PruebasWeb(unittest.TestCase):
    def setUp(self):
        self.cliente = crear_app(FabricaSinBase()).test_client()

    def test_inicio_publico(self):
        respuesta = self.cliente.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Crear cuenta", respuesta.get_data(as_text=True))

    def test_rutas_de_aspirante_exigen_sesion(self):
        for ruta in ("/aspirante/", "/aspirante/cuestionario", "/aspirante/evaluaciones/1"):
            respuesta = self.cliente.get(ruta)
            self.assertEqual(respuesta.status_code, 302, ruta)
            self.assertIn("/?siguiente=", respuesta.headers["Location"])

    def test_rutas_de_ingeniero_exigen_sesion(self):
        for ruta in ("/ingeniero/", "/ingeniero/granulos", "/ingeniero/evaluaciones"):
            self.assertEqual(self.cliente.get(ruta).status_code, 302, ruta)

    def test_aspirante_no_entra_al_panel_del_ingeniero(self):
        with self.cliente.session_transaction() as sesion:
            sesion["usuario"] = {"rol": "aspirante", "id": 1, "nombres": "A", "apellidos": "B", "correo": "a@b.co"}
        respuesta = self.cliente.get("/ingeniero/granulos")
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.headers["Location"].endswith("/aspirante/"))

    def test_formulario_sin_token_csrf_se_rechaza(self):
        respuesta = self.cliente.post("/ingresar", data={"rol": "aspirante", "correo": "x@y.co", "contrasena": "12345678"})
        self.assertEqual(respuesta.status_code, 400)


if __name__ == "__main__":
    unittest.main()
