"""API del sistema experto de orientación académica."""
import logging
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel

from motor import ErroresValidacion, MotorInferencia
from repositorio import RepositorioConocimiento

logger = logging.getLogger(__name__)
ORIGENES = os.getenv("CORS_ORIGENES", "http://localhost:5500,http://127.0.0.1:5500").split(",")

app = FastAPI(title="Sistema experto de orientación académica", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in ORIGENES],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
repositorio = RepositorioConocimiento()


class SolicitudInferencia(BaseModel):
    respuestas: dict[str, str]      # {codigo_variable: texto ingresado}


def base_conocimiento():
    try:
        return repositorio.obtener()
    except Exception:
        logger.exception("No se pudo leer la base de conocimiento")
        raise HTTPException(status_code=503, detail="No se pudo leer la base de conocimiento.")


@app.get("/")
def inicio():
    return {"servicio": app.title, "documentacion": "/docs"}


@app.get("/salud")
def salud(base=Depends(base_conocimiento)):
    return {"estado": "ok", "origen": repositorio.origen, **base.resumen}


@app.get("/preguntas")
def preguntas(base=Depends(base_conocimiento)):
    return base.preguntas


@app.post("/inferir")
def inferir(solicitud: SolicitudInferencia, base=Depends(base_conocimiento)):
    try:
        return MotorInferencia(base).inferir(solicitud.respuestas)
    except ErroresValidacion as error:
        raise HTTPException(status_code=422, detail={"errores": error.errores})


handler = Mangum(app, lifespan="off")      # punto de entrada de AWS Lambda: main.handler
