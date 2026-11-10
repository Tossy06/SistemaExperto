"""DAO de los usuarios: aspirantes (esquema transaccional) e ingenieros del conocimiento (esquema conocimiento)."""
import psycopg2

from app.modelo.dao.base_dao import BaseDAO
from app.modelo.entidades import Aspirante, IngenieroConocimiento
from app.modelo.validaciones import ErrorNegocio


class AspiranteDAO(BaseDAO):
    def insertar(self, documento, nombres, apellidos, correo, contrasena_hash) -> Aspirante:
        """CU-01: guarda un aspirante nuevo. Si el documento o el correo ya existen lanza ErrorNegocio."""
        try:
            with self._transaccion() as cur:
                cur.execute("""INSERT INTO transaccional.aspirantes (documento, nombres, apellidos, correo, contrasena_hash)
                               VALUES (%s, %s, %s, %s, %s) RETURNING id_aspirante""",
                            (documento, nombres, apellidos, correo, contrasena_hash))
                id_aspirante = cur.fetchone()["id_aspirante"]
        except psycopg2.IntegrityError:
            raise ErrorNegocio("Ya hay una cuenta con ese documento o correo. Inicie sesión con ella.")
        return Aspirante(id_aspirante, documento, nombres, apellidos, correo)

    def credenciales(self, correo):
        """Devuelve (Aspirante, hash de la contraseña) o None si el correo no existe."""
        f = self._consultar_uno("""SELECT id_aspirante, documento, nombres, apellidos, correo, contrasena_hash
                                   FROM transaccional.aspirantes WHERE correo = %s""", (correo,))
        return f and (Aspirante(f["id_aspirante"], f["documento"], f["nombres"], f["apellidos"], f["correo"]),
                      f["contrasena_hash"])

    def contar(self) -> int:
        return self._consultar_uno("SELECT COUNT(*) AS n FROM transaccional.aspirantes")["n"]


class IngenieroDAO(BaseDAO):
    def credenciales(self, correo):
        """Devuelve (IngenieroConocimiento, hash de la contraseña) o None si el correo no existe."""
        f = self._consultar_uno("""SELECT id_ingeniero, documento, nombres, apellidos, correo, contrasena_hash
                                   FROM conocimiento.ingenieros_conocimiento WHERE correo = %s""", (correo,))
        return f and (IngenieroConocimiento(f["id_ingeniero"], f["documento"], f["nombres"], f["apellidos"], f["correo"]),
                      f["contrasena_hash"])
