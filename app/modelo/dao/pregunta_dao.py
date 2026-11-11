"""DAO de las preguntas del cuestionario vocacional (RF-02)."""
from app.modelo.dao.base_dao import BaseDAO
from app.modelo.entidades import Pregunta


class PreguntaDAO(BaseDAO):
    def activas(self) -> list:
        """Preguntas en orden, con la variable del perfil que mide cada una."""
        filas = self._consultar("""
            SELECT p.id_pregunta, p.codigo, v.codigo AS codigo_variable, v.nombre AS nombre_variable, v.tipo_variable,
                   p.tipo_respuesta, p.enunciado, p.valor_minimo, p.valor_maximo, p.etiqueta_minima, p.etiqueta_maxima
            FROM conocimiento.preguntas_cuestionario_vocacional p
            JOIN conocimiento.variables_perfil v ON v.id_variable = p.id_variable
            WHERE p.activa ORDER BY p.orden""")
        return [Pregunta(**f) for f in filas]
