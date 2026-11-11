"""DAO de las reglas de resultado no concluyente (reglas RN)."""
from app.modelo.dao.base_dao import BaseDAO
from app.modelo.entidades import ReglaNoConcluyente


class ReglaNoConcluyenteDAO(BaseDAO):
    def activas(self) -> list:
        filas = self._consultar("""
            SELECT id_regla_resultado_no_concluyente AS id_regla, codigo_regla, descripcion,
                   metrica, tipo_variable, valor_hecho, operador, umbral
            FROM conocimiento.reglas_resultado_no_concluyente WHERE activa ORDER BY codigo_regla""")
        return [ReglaNoConcluyente(**f) for f in filas]
