"""Fábrica de conexiones a PostgreSQL con un pool seguro para hilos.

Se instancia una sola vez en crear_app(); cada petición web toma una conexión y la devuelve al terminar.
"""
import threading

import psycopg2
import psycopg2.extras
import psycopg2.pool


class FabricaConexion:
    def __init__(self, configuracion: dict, minimo: int = 1, maximo: int = 10):
        self._configuracion = configuracion
        self._minimo, self._maximo = minimo, maximo
        self._pool = None
        self._candado = threading.Lock()

    def _obtener_pool(self):
        with self._candado:
            if self._pool is None:
                self._pool = psycopg2.pool.ThreadedConnectionPool(self._minimo, self._maximo, **self._configuracion)
            return self._pool

    def obtener(self):
        """Entrega una conexión viva. Si el servidor cerró una conexión inactiva (p. ej. Neon), abre otra."""
        pool = self._obtener_pool()
        conexion = pool.getconn()
        try:
            with conexion.cursor() as cur:
                cur.execute("SELECT 1")
            conexion.rollback()
        except psycopg2.Error:
            pool.putconn(conexion, close=True)
            conexion = pool.getconn()
        return conexion

    def devolver(self, conexion):
        if self._pool is None:
            return
        if conexion.closed:
            self._pool.putconn(conexion, close=True)
            return
        try:
            conexion.rollback()          # descarta cualquier transacción de solo lectura abierta
            self._pool.putconn(conexion)
        except psycopg2.Error:
            self._pool.putconn(conexion, close=True)

    def verificar(self):
        """Lanza psycopg2.OperationalError si no hay conexión con el servidor."""
        conexion = self.obtener()
        self.devolver(conexion)

    def cerrar(self):
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None


def cursor_diccionario(conexion):
    return conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
