"""DAO de las hipótesis: los programas académicos que el sistema puede proponer."""
from app.modelo.dao.base_dao import BaseDAO


class HipotesisDAO(BaseDAO):
    def activas(self) -> list:
        return self._consultar("""SELECT id_hipotesis, codigo, programa_academico
                                  FROM conocimiento.hipotesis_programas WHERE activa ORDER BY codigo""")
