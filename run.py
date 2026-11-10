"""Punto de entrada de la aplicación web.

Uso:
    python run.py                 servidor de desarrollo en http://127.0.0.1:5000
    python run.py --produccion    servidor waitress (Windows/Linux) en 0.0.0.0
"""
import sys

import psycopg2

from app import crear_app
from app.config import CONFIG_BD, NOMBRE_PERFIL_BD, PUERTO_WEB

app = crear_app()

if __name__ == "__main__":
    try:
        app.extensions["fabrica_conexion"].verificar()
        print(f"Conectado a {NOMBRE_PERFIL_BD} ({CONFIG_BD['host']}:{CONFIG_BD['port']}/{CONFIG_BD['dbname']}).")
    except psycopg2.OperationalError as error:
        print(f"AVISO: no hay conexión con {NOMBRE_PERFIL_BD} ({CONFIG_BD['host']}:{CONFIG_BD['port']}). "
              f"La aplicación mostrará un mensaje hasta que la base esté disponible.\n  {str(error).strip().splitlines()[0]}")
    if "--produccion" in sys.argv:
        from waitress import serve
        print(f"Servidor en http://0.0.0.0:{PUERTO_WEB}")
        serve(app, host="0.0.0.0", port=PUERTO_WEB)
    else:
        app.run(host="127.0.0.1", port=PUERTO_WEB, debug=True)
