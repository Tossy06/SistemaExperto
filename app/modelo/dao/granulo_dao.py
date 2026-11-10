"""DAO de los gránulos de conocimiento (reglas RG): «si el aspirante tiene este hecho, la hipótesis suma este peso»."""
from decimal import Decimal

import psycopg2

from app.modelo.dao.base_dao import BaseDAO
from app.modelo.entidades import Granulo
from app.modelo.validaciones import ErrorNegocio

# Columnas y uniones comunes de los listados del ingeniero (vista legible de cada gránulo).
_LISTADO = """
    SELECT g.id_granulo, g.codigo_regla AS regla, h.codigo AS hipotesis, h.programa_academico,
           v.nombre AS variable, he.valor_clasificado AS valor_hecho, g.peso, g.activo, g.fecha_modificacion,
           COALESCE(i.nombres || ' ' || i.apellidos, '') AS ingeniero
    FROM conocimiento.granulos_hecho_hipotesis g
    JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = g.id_hipotesis
    JOIN conocimiento.hechos_perfil he      ON he.id_hecho    = g.id_hecho
    JOIN conocimiento.variables_perfil v    ON v.id_variable  = he.id_variable
    LEFT JOIN conocimiento.ingenieros_conocimiento i ON i.id_ingeniero = g.id_ingeniero"""


class GranuloDAO(BaseDAO):
    def por_hecho(self, id_hecho: int) -> list:
        """RF-03: consulta granular que el motor ejecuta una vez por cada hecho del aspirante."""
        filas = self._consultar("""
            SELECT g.codigo_regla, g.id_hecho, g.id_hipotesis, h.codigo AS codigo_hipotesis, h.programa_academico, g.peso
            FROM conocimiento.granulos_hecho_hipotesis g
            JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = g.id_hipotesis
            WHERE g.id_hecho = %s AND g.activo AND h.activa ORDER BY h.codigo""", (id_hecho,))
        return [Granulo(**{**f, "peso": Decimal(f["peso"])}) for f in filas]

    def listar(self, codigo_hipotesis=None) -> list:
        """CU-06: gránulos (activos e inactivos) de una hipótesis, o de todas si no se indica código."""
        return self._consultar(_LISTADO + """
            WHERE %(codigo)s::varchar IS NULL OR h.codigo = %(codigo)s
            ORDER BY h.codigo, g.activo DESC, v.id_variable, g.codigo_regla""", {"codigo": codigo_hipotesis or None})

    def obtener(self, id_granulo: int):
        return self._consultar_uno(_LISTADO + " WHERE g.id_granulo = %s", (id_granulo,))

    def resumen_por_hipotesis(self) -> list:
        """Consulta C2: cantidad de gránulos activos y peso máximo alcanzable por hipótesis."""
        return self._consultar("""
            SELECT h.codigo AS hipotesis, h.programa_academico,
                   COUNT(g.id_granulo) FILTER (WHERE g.activo)      AS numero_granulos,
                   COALESCE(SUM(g.peso) FILTER (WHERE g.activo), 0) AS peso_maximo
            FROM conocimiento.hipotesis_programas h
            LEFT JOIN conocimiento.granulos_hecho_hipotesis g ON g.id_hipotesis = h.id_hipotesis
            WHERE h.activa GROUP BY h.codigo, h.programa_academico ORDER BY h.codigo""")

    def contar_activos(self) -> int:
        return self._consultar_uno("SELECT COUNT(*) AS n FROM conocimiento.granulos_hecho_hipotesis WHERE activo")["n"]

    def insertar(self, id_hecho, id_hipotesis, peso, id_ingeniero) -> str:
        """CU-07: crea un gránulo con el siguiente código RG libre y lo devuelve (p. ej. «RG-73»)."""
        try:
            with self._transaccion() as cur:
                cur.execute("LOCK TABLE conocimiento.granulos_hecho_hipotesis IN SHARE ROW EXCLUSIVE MODE")
                cur.execute("""SELECT COALESCE(MAX(SUBSTRING(codigo_regla FROM 4)::int), 0) + 1 AS n
                               FROM conocimiento.granulos_hecho_hipotesis WHERE codigo_regla ~ '^RG-[0-9]+$'""")
                codigo = f"RG-{cur.fetchone()['n']:02d}"
                cur.execute("""INSERT INTO conocimiento.granulos_hecho_hipotesis (codigo_regla, id_hecho, id_hipotesis, peso, id_ingeniero)
                               VALUES (%s, %s, %s, %s, %s)""", (codigo, id_hecho, id_hipotesis, peso, id_ingeniero))
        except psycopg2.IntegrityError:
            raise ErrorNegocio("Ese hecho ya tiene un gránulo para ese programa. Edite el existente en lugar de crear otro.")
        return codigo

    def actualizar(self, id_granulo, peso, activo, id_ingeniero):
        """CU-07: cambia el peso y el estado de un gránulo y registra quién lo modificó."""
        with self._transaccion() as cur:
            cur.execute("""UPDATE conocimiento.granulos_hecho_hipotesis
                           SET peso = %s, activo = %s, id_ingeniero = %s, fecha_modificacion = now()
                           WHERE id_granulo = %s""", (peso, activo, id_ingeniero, id_granulo))
