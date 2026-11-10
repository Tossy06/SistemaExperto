"""DAO de los hechos del perfil y sus rangos de clasificación (reglas RC)."""
from app.modelo.dao.base_dao import BaseDAO
from app.modelo.entidades import Hecho, Respuesta


class HechoDAO(BaseDAO):
    def derivar(self, respuesta: Respuesta):
        """RF-02: una consulta por respuesta; devuelve el Hecho cuyo rango (u opción) la contiene, o None."""
        f = self._consultar_uno("""
            SELECT h.id_hecho, h.codigo, v.nombre AS variable, v.tipo_variable, h.valor_clasificado
            FROM conocimiento.hechos_perfil h
            JOIN conocimiento.preguntas_cuestionario_vocacional p ON p.id_variable = h.id_variable
            JOIN conocimiento.variables_perfil v ON v.id_variable = h.id_variable
            WHERE p.id_pregunta = %(id)s
              AND (%(numero)s::numeric BETWEEN h.rango_minimo AND h.rango_maximo OR h.valor_clasificado = %(opcion)s)""",
                                {"id": respuesta.id_pregunta, "numero": respuesta.valor_numerico, "opcion": respuesta.valor_opcion})
        return f and Hecho(**f)

    def listar(self) -> list:
        """Consulta C4: todos los hechos con su variable y rango."""
        return self._consultar("""
            SELECT h.id_hecho, h.codigo, v.codigo AS codigo_variable, v.nombre AS variable, v.tipo_variable,
                   h.valor_clasificado, h.rango_minimo, h.rango_maximo
            FROM conocimiento.hechos_perfil h
            JOIN conocimiento.variables_perfil v ON v.id_variable = h.id_variable
            ORDER BY v.id_variable, h.rango_minimo DESC NULLS LAST, h.id_hecho""")

    def rangos_por_variable(self) -> dict:
        """{codigo_variable: [{valor, minimo, maximo}]}: la vista los usa para clasificar mientras se responde."""
        rangos = {}
        for f in self.listar():
            if f["rango_minimo"] is not None:
                rangos.setdefault(f["codigo_variable"], []).append(
                    {"valor": f["valor_clasificado"], "minimo": float(f["rango_minimo"]), "maximo": float(f["rango_maximo"])})
        return rangos
