"""DAO de las preguntas del cuestionario vocacional (RF-02)."""
from app.modelo.dao.base_dao import BaseDAO
from app.modelo.entidades import Pregunta


class PreguntaDAO(BaseDAO):
    def activas(self) -> list:
        """Preguntas en orden, con su variable y, si es de opción, los valores permitidos."""
        filas = self._consultar("""
            SELECT p.id_pregunta, v.codigo AS codigo_variable, v.nombre AS nombre_variable, v.tipo_variable,
                   v.tipo_respuesta, p.enunciado, p.valor_minimo, p.valor_maximo,
                   ARRAY(SELECT h.valor_clasificado FROM conocimiento.hechos_perfil h
                         WHERE h.id_variable = v.id_variable AND h.rango_minimo IS NULL ORDER BY h.id_hecho) AS opciones
            FROM conocimiento.preguntas_cuestionario_vocacional p
            JOIN conocimiento.variables_perfil v ON v.id_variable = p.id_variable
            WHERE p.activa ORDER BY p.orden""")
        return [Pregunta(**{**f, "opciones": tuple(f["opciones"])}) for f in filas]
