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

# Respuestas del aspirante de ejemplo del documento (botón «Usar respuestas de ejemplo»).
# P01-P04: notas por área; P05-P22: tres ítems por categoría RIASEC (R, I, A, S, E, C) en escala 1 a 5;
# P23: estilo de trabajo (1 = siempre por mi cuenta, 5 = siempre en equipo).
EJEMPLO_DEMO = {"P01": "4.5", "P02": "3.7", "P03": "3.4", "P04": "3.9",
                "P05": "4", "P06": "3", "P07": "4",      # Realista      3,67
                "P08": "5", "P09": "4", "P10": "4",      # Investigativo 4,33
                "P11": "2", "P12": "1", "P13": "2",      # Artístico     1,67
                "P14": "3", "P15": "4", "P16": "3",      # Social        3,33
                "P17": "2", "P18": "3", "P19": "2",      # Emprendedor   2,33
                "P20": "3", "P21": "3", "P22": "3",      # Convencional  3,00
                "P23": "2"}                              # Estilo: Independiente
