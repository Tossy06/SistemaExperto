"""Lee la base de conocimiento desde Amazon S3.

Si no existe S3_BUCKET usa el archivo del proyecto, solo para pruebas locales.
Ese archivo no se despliega con la API, así que en AWS las reglas siempre vienen de S3.
"""
import json
import os
import time
from pathlib import Path

from motor import BaseConocimiento

BUCKET = os.getenv("S3_BUCKET")
CLAVE = os.getenv("S3_CLAVE", "base_conocimiento.json")
ARCHIVO_LOCAL = Path(__file__).resolve().parent.parent / "base_conocimiento" / "base_conocimiento.json"
SEGUNDOS_CACHE = 60


class RepositorioConocimiento:
    def __init__(self):
        self.origen = "amazon_s3" if BUCKET else "archivo_local"
        self._base = None
        self._leida_en = 0.0

    def obtener(self):
        """Devuelve la base en memoria y la vuelve a leer cada SEGUNDOS_CACHE."""
        ahora = time.monotonic()
        if self._base is None or ahora - self._leida_en >= SEGUNDOS_CACHE:
            self._base = BaseConocimiento(json.loads(self._leer()))
            self._leida_en = ahora
        return self._base

    def _leer(self):
        if BUCKET:
            import boto3    # viene incluido en AWS Lambda; no hace falta para las pruebas locales
            return boto3.client("s3").get_object(Bucket=BUCKET, Key=CLAVE)["Body"].read()
        return ARCHIVO_LOCAL.read_bytes()
