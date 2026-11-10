"""Configuración de la aplicación web y de la conexión a PostgreSQL.

Los datos se leen del archivo .env de la raíz del proyecto (o de variables de entorno).
SEO_BD_PERFIL elige el servidor:
    local -> PostgreSQL instalado en el equipo o en Docker (variables LOCAL_BD_*)
    neon  -> PostgreSQL en la nube de Neon                 (variables NEON_BD_*)
"""
import os
import secrets
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def _cargar_env(ruta: Path):
    """Carga líneas CLAVE=valor del archivo .env sin reemplazar variables ya definidas."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env(RAIZ_PROYECTO / ".env")

# ---------------- Base de datos ----------------
PERFILES = {
    "local": {"nombre": "PostgreSQL local", "host": "localhost", "port": "5432",
              "dbname": "sistema_experto_orientacion", "user": "postgres", "password": "postgres", "sslmode": "prefer"},
    "neon": {"nombre": "PostgreSQL en Neon", "host": "", "port": "5432",
             "dbname": "neondb", "user": "neondb_owner", "password": "", "sslmode": "require"},
}
_VARIABLES = {"host": "HOST", "port": "PUERTO", "dbname": "NOMBRE", "user": "USUARIO", "password": "CLAVE", "sslmode": "SSL"}

PERFIL_BD = os.getenv("SEO_BD_PERFIL", "local").strip().lower()
if PERFIL_BD not in PERFILES:
    raise SystemExit(f"SEO_BD_PERFIL='{PERFIL_BD}' no es válido. Use: {', '.join(PERFILES)}.")

_base = PERFILES[PERFIL_BD]
NOMBRE_PERFIL_BD = _base["nombre"]
CONFIG_BD = {campo: os.getenv(f"{PERFIL_BD.upper()}_BD_{sufijo}", _base[campo]) for campo, sufijo in _VARIABLES.items()}
CONFIG_BD["port"] = int(CONFIG_BD["port"])
CONFIG_BD["connect_timeout"] = 10

# ---------------- Aplicación web ----------------
# Clave para firmar la cookie de sesión. Si no se define, se genera una al arrancar
# (las sesiones abiertas se pierden al reiniciar el servidor).
CLAVE_SECRETA = os.getenv("SEO_CLAVE_SECRETA") or secrets.token_hex(32)
PUERTO_WEB = int(os.getenv("SEO_PUERTO_WEB", "5000"))

# ---------------- Motor de inferencia ----------------
NUMERO_HIPOTESIS_RESULTADO = 5   # RF-03: el sistema presenta las cinco hipótesis de mayor probabilidad
DECIMALES_CALCULO = 4            # decimales del cálculo de probabilidades
DECIMALES_PRESENTACION = 2       # decimales al presentar las probabilidades

# Respuestas del aspirante de ejemplo del documento (botón «Usar respuestas de ejemplo»)
EJEMPLO_DEMO = {"DES-LM": "4.5", "DES-CI": "3.7", "DES-SH": "3.4", "DES-AF": "3.9", "INT-R": "60", "INT-I": "80",
                "INT-A": "30", "INT-S": "55", "INT-E": "35", "INT-C": "45", "EST": "Independiente"}
