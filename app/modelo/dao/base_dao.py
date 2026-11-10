"""Clase base de todos los DAO (Data Access Object): encapsula cómo se consulta PostgreSQL.

Cada DAO recibe `conexion_actual`, una función que devuelve la conexión de la petición en curso;
así todos los DAO de una misma petición comparten conexión y transacción.
"""
from contextlib import contextmanager

from app.modelo.conexion import cursor_diccionario


class BaseDAO:
    def __init__(self, conexion_actual):
        self._conexion = conexion_actual

    def _consultar(self, sql, parametros=None) -> list:
        """SELECT que devuelve todas las filas como diccionarios."""
        with cursor_diccionario(self._conexion()) as cur:
            cur.execute(sql, parametros)
            return cur.fetchall()

    def _consultar_uno(self, sql, parametros=None):
        """SELECT que devuelve una fila (diccionario) o None."""
        with cursor_diccionario(self._conexion()) as cur:
            cur.execute(sql, parametros)
            return cur.fetchone()

    @contextmanager
    def _transaccion(self):
        """Bloque de escritura: COMMIT si termina bien, ROLLBACK si hay un error."""
        conexion = self._conexion()
        with conexion, cursor_diccionario(conexion) as cur:
            yield cur
