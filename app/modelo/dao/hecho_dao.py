"""DAO de los hechos del perfil y sus rangos de clasificación (reglas RC)."""
from decimal import Decimal

from app.modelo.dao.base_dao import BaseDAO
from app.modelo.entidades import Hecho

# RF-02 / RC: una sola consulta deriva un hecho por variable a partir de todas las respuestas.
#   1. promedio de las preguntas de cada variable (las de interés tienen tres ítems);
#   2. posición de cada variable frente a las del mismo tipo (DENSE_RANK: los empates comparten posición);
#   3. el valor que se compara con el rango del hecho lo indica la variable (RANGO -> promedio, POSICION -> posición);
#   4. grado de certeza: promedio / valor máximo si la variable pondera intensidad; si no, 1.
# Las variables sin hecho (valor fuera de todos los rangos) salen con id_hecho NULL.
_DERIVAR = """
    WITH respuestas (id_pregunta, valor) AS (SELECT * FROM unnest(%(ids)s::int[], %(valores)s::numeric[])),
    por_variable AS (
        SELECT v.id_variable, v.codigo AS codigo_variable, v.nombre AS variable, v.tipo_variable,
               v.criterio_clasificacion, v.pondera_intensidad,
               ROUND(AVG(r.valor), 2) AS promedio, MAX(p.valor_maximo) AS maximo
        FROM respuestas r
        JOIN conocimiento.preguntas_cuestionario_vocacional p ON p.id_pregunta = r.id_pregunta
        JOIN conocimiento.variables_perfil v ON v.id_variable = p.id_variable
        GROUP BY v.id_variable),
    posiciones AS (
        SELECT *, DENSE_RANK() OVER (PARTITION BY tipo_variable ORDER BY promedio DESC) AS posicion
        FROM por_variable)
    SELECT h.id_hecho, h.codigo, pv.variable, pv.tipo_variable, h.valor_clasificado, pv.codigo_variable,
           pv.promedio AS valor_calculado, pv.posicion,
           CASE WHEN pv.pondera_intensidad THEN ROUND(pv.promedio / pv.maximo, 4) ELSE 1 END AS grado
    FROM posiciones pv
    LEFT JOIN conocimiento.hechos_perfil h
      ON h.id_variable = pv.id_variable
     AND (CASE pv.criterio_clasificacion WHEN 'POSICION' THEN pv.posicion ELSE pv.promedio END)
         BETWEEN h.rango_minimo AND h.rango_maximo
    ORDER BY pv.id_variable"""


class HechoDAO(BaseDAO):
    def derivar(self, respuestas) -> tuple:
        """RF-02: devuelve (hechos derivados, códigos de variable que no caen en ningún rango)."""
        filas = self._consultar(_DERIVAR, {"ids": [r.id_pregunta for r in respuestas],
                                           "valores": [r.valor for r in respuestas]})
        sin_hecho = [f["codigo_variable"] for f in filas if f["id_hecho"] is None]
        hechos = [Hecho(id_hecho=f["id_hecho"], codigo=f["codigo"], variable=f["variable"], tipo_variable=f["tipo_variable"],
                        valor_clasificado=f["valor_clasificado"], valor_calculado=Decimal(f["valor_calculado"]),
                        posicion=f["posicion"], grado=Decimal(f["grado"]))
                  for f in filas if f["id_hecho"] is not None]
        return hechos, sin_hecho

    def listar(self) -> list:
        """Consulta C4: todos los hechos con su variable, criterio y rango."""
        return self._consultar("""
            SELECT h.id_hecho, h.codigo, v.codigo AS codigo_variable, v.nombre AS variable, v.tipo_variable,
                   v.criterio_clasificacion, h.valor_clasificado, h.rango_minimo, h.rango_maximo
            FROM conocimiento.hechos_perfil h
            JOIN conocimiento.variables_perfil v ON v.id_variable = h.id_variable
            ORDER BY v.id_variable,
                     CASE v.criterio_clasificacion WHEN 'POSICION' THEN h.rango_minimo ELSE -h.rango_minimo END, h.id_hecho""")

    def rangos_por_variable(self) -> dict:
        """{codigo_variable: {criterio, rangos: [{valor, minimo, maximo}]}}: la vista los usa para clasificar mientras se responde."""
        rangos = {}
        for f in self.listar():
            variable = rangos.setdefault(f["codigo_variable"], {"criterio": f["criterio_clasificacion"], "rangos": []})
            variable["rangos"].append({"valor": f["valor_clasificado"], "minimo": float(f["rango_minimo"]),
                                       "maximo": float(f["rango_maximo"])})
        return rangos
