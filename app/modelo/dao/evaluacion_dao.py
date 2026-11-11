"""DAO de las evaluaciones vocacionales (esquema transaccional).

Una evaluación se guarda completa en UNA transacción: respuestas, hechos derivados (con su grado), tabla de contabilización,
cinco hipótesis y marcas de resultado no concluyente (RNF-04). Las evaluaciones no se modifican (RNF-04).
"""
from app.modelo.dao.base_dao import BaseDAO

# Fila resumen de una evaluación: aspirante y programa que quedó en primer lugar.
_RESUMEN = """
    SELECT e.id_evaluacion, e.fecha_evaluacion, e.resultado_no_concluyente,
           a.id_aspirante, a.nombres || ' ' || a.apellidos AS aspirante, a.documento,
           h.codigo AS codigo_primera, h.programa_academico AS programa_primera, r.probabilidad AS probabilidad_primera,
           c.grado_coincidencia AS coincidencia_primera
    FROM transaccional.evaluaciones_vocacionales e
    JOIN transaccional.aspirantes a ON a.id_aspirante = e.id_aspirante
    LEFT JOIN transaccional.resultado_cinco_hipotesis r ON r.id_evaluacion = e.id_evaluacion AND r.posicion = 1
    LEFT JOIN transaccional.contabilizacion_coincidencias_hipotesis c
      ON c.id_evaluacion = r.id_evaluacion AND c.id_hipotesis = r.id_hipotesis
    LEFT JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = r.id_hipotesis"""


class EvaluacionDAO(BaseDAO):
    def insertar(self, id_aspirante, respuestas, resultado) -> int:
        """Guarda la evaluación completa en una sola transacción y devuelve su número."""
        with self._transaccion() as cur:
            cur.execute("""INSERT INTO transaccional.evaluaciones_vocacionales (id_aspirante, resultado_no_concluyente)
                           VALUES (%s, %s) RETURNING id_evaluacion""", (id_aspirante, resultado.resultado_no_concluyente))
            id_evaluacion = cur.fetchone()["id_evaluacion"]
            cur.executemany("""INSERT INTO transaccional.respuestas_aspirante (id_evaluacion, id_pregunta, valor)
                               VALUES (%s, %s, %s)""",
                            [(id_evaluacion, r.id_pregunta, r.valor) for r in respuestas])
            cur.executemany("""INSERT INTO transaccional.hechos_aspirante
                               (id_evaluacion, id_hecho, valor_calculado, posicion, grado) VALUES (%s, %s, %s, %s, %s)""",
                            [(id_evaluacion, h.id_hecho, h.valor_calculado, h.posicion, h.grado) for h in resultado.hechos])
            cur.executemany("""INSERT INTO transaccional.contabilizacion_coincidencias_hipotesis
                               (id_evaluacion, id_hipotesis, numero_coincidencias, suma_aportes, grado_coincidencia, probabilidad)
                               VALUES (%s, %s, %s, %s, %s, %s)""",
                            [(id_evaluacion, c.id_hipotesis, c.numero_coincidencias, c.suma_aportes, c.grado_coincidencia,
                              c.probabilidad) for c in resultado.contabilizacion])
            cur.executemany("""INSERT INTO transaccional.resultado_cinco_hipotesis
                               (id_evaluacion, posicion, id_hipotesis, probabilidad) VALUES (%s, %s, %s, %s)""",
                            [(id_evaluacion, posicion, c.id_hipotesis, c.probabilidad_resultado)
                             for posicion, c in enumerate(resultado.cinco_hipotesis, start=1)])
            cur.executemany("""INSERT INTO transaccional.marcas_resultado_no_concluyente
                               (id_evaluacion, id_regla_resultado_no_concluyente) VALUES (%s, %s)""",
                            [(id_evaluacion, regla.id_regla) for regla in resultado.marcas_no_concluyente])
        return id_evaluacion

    def listar_por_aspirante(self, id_aspirante) -> list:
        return self._consultar(_RESUMEN + " WHERE e.id_aspirante = %s ORDER BY e.fecha_evaluacion DESC, e.id_evaluacion DESC",
                               (id_aspirante,))

    def listar_todas(self, texto=None, limite=200) -> list:
        """CU-08: todas las evaluaciones; `texto` filtra por nombre o documento del aspirante."""
        filtro = f"%{texto.strip()}%" if texto and texto.strip() else None
        return self._consultar(_RESUMEN + """
            WHERE %(filtro)s::text IS NULL
               OR a.nombres || ' ' || a.apellidos ILIKE %(filtro)s OR a.documento ILIKE %(filtro)s
            ORDER BY e.fecha_evaluacion DESC, e.id_evaluacion DESC LIMIT %(limite)s""",
                               {"filtro": filtro, "limite": limite})

    def contar(self) -> int:
        return self._consultar_uno("SELECT COUNT(*) AS n FROM transaccional.evaluaciones_vocacionales")["n"]

    def programas_mas_frecuentes(self, limite=5) -> list:
        """Programas que más veces quedaron en primer lugar."""
        return self._consultar("""
            SELECT h.codigo, h.programa_academico, COUNT(*) AS veces
            FROM transaccional.resultado_cinco_hipotesis r
            JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = r.id_hipotesis
            WHERE r.posicion = 1
            GROUP BY h.codigo, h.programa_academico
            ORDER BY veces DESC, h.codigo LIMIT %s""", (limite,))

    def detalle(self, id_evaluacion):
        """Evaluación tal como quedó registrada, o None si no existe."""
        evaluacion = self._consultar_uno(_RESUMEN + " WHERE e.id_evaluacion = %s", (id_evaluacion,))
        if evaluacion is None:
            return None
        cinco = self._consultar("""
            SELECT r.posicion, h.id_hipotesis, h.codigo, h.programa_academico, r.probabilidad,
                   c.numero_coincidencias, c.suma_aportes, c.grado_coincidencia, c.probabilidad AS probabilidad_global
            FROM transaccional.resultado_cinco_hipotesis r
            JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = r.id_hipotesis
            JOIN transaccional.contabilizacion_coincidencias_hipotesis c
              ON c.id_evaluacion = r.id_evaluacion AND c.id_hipotesis = r.id_hipotesis
            WHERE r.id_evaluacion = %s ORDER BY r.posicion""", (id_evaluacion,))
        contabilizacion = self._consultar("""
            SELECT h.codigo, h.programa_academico, c.numero_coincidencias, c.suma_aportes, c.grado_coincidencia, c.probabilidad
            FROM transaccional.contabilizacion_coincidencias_hipotesis c
            JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = c.id_hipotesis
            WHERE c.id_evaluacion = %s
            ORDER BY c.suma_aportes DESC, c.numero_coincidencias DESC, h.codigo""", (id_evaluacion,))
        # Perfil: un hecho por variable, con el promedio, la posición y el grado de certeza.
        perfil = self._consultar("""
            SELECT v.codigo AS codigo_variable, v.nombre AS variable, v.tipo_variable, v.criterio_clasificacion,
                   ha.valor_calculado, ha.posicion, ha.grado, he.valor_clasificado,
                   (SELECT COUNT(*) FROM transaccional.respuestas_aspirante r
                    JOIN conocimiento.preguntas_cuestionario_vocacional p ON p.id_pregunta = r.id_pregunta
                    WHERE r.id_evaluacion = ha.id_evaluacion AND p.id_variable = v.id_variable) AS numero_preguntas
            FROM transaccional.hechos_aspirante ha
            JOIN conocimiento.hechos_perfil he ON he.id_hecho = ha.id_hecho
            JOIN conocimiento.variables_perfil v ON v.id_variable = he.id_variable
            WHERE ha.id_evaluacion = %s ORDER BY v.id_variable""", (id_evaluacion,))
        respuestas = self._consultar("""
            SELECT p.codigo, p.enunciado, v.nombre AS variable, v.tipo_variable,
                   RTRIM(RTRIM(r.valor::text, '0'), '.') AS valor
            FROM transaccional.respuestas_aspirante r
            JOIN conocimiento.preguntas_cuestionario_vocacional p ON p.id_pregunta = r.id_pregunta
            JOIN conocimiento.variables_perfil v ON v.id_variable = p.id_variable
            WHERE r.id_evaluacion = %s ORDER BY p.orden""", (id_evaluacion,))
        # Hechos del aspirante que respaldan cada una de las cinco hipótesis (gránulos coincidentes y su aporte).
        apoyos = self._consultar("""
            SELECT h.codigo, g.codigo_regla, v.nombre AS variable, he.valor_clasificado, g.peso, ha.grado,
                   ROUND(g.peso * ha.grado, 4) AS aporte
            FROM transaccional.resultado_cinco_hipotesis r
            JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = r.id_hipotesis
            JOIN transaccional.hechos_aspirante ha ON ha.id_evaluacion = r.id_evaluacion
            JOIN conocimiento.granulos_hecho_hipotesis g ON g.id_hecho = ha.id_hecho AND g.id_hipotesis = r.id_hipotesis
            JOIN conocimiento.hechos_perfil he ON he.id_hecho = ha.id_hecho
            JOIN conocimiento.variables_perfil v ON v.id_variable = he.id_variable
            WHERE r.id_evaluacion = %s
            ORDER BY r.posicion, aporte DESC, g.codigo_regla""", (id_evaluacion,))
        marcas = self._consultar("""
            SELECT rn.codigo_regla, rn.descripcion
            FROM transaccional.marcas_resultado_no_concluyente m
            JOIN conocimiento.reglas_resultado_no_concluyente rn
              ON rn.id_regla_resultado_no_concluyente = m.id_regla_resultado_no_concluyente
            WHERE m.id_evaluacion = %s ORDER BY rn.codigo_regla""", (id_evaluacion,))
        por_hipotesis = {}
        for a in apoyos:
            por_hipotesis.setdefault(a["codigo"], []).append(a)
        for h in cinco:
            h["apoyos"] = por_hipotesis.get(h["codigo"], [])
        return {"evaluacion": evaluacion, "cinco": cinco, "contabilizacion": contabilizacion,
                "perfil": perfil, "respuestas": respuestas, "marcas": marcas}
