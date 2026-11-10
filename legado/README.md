# Versión anterior (AWS Lambda + S3)

Primera versión web: API FastAPI desplegada en AWS Lambda que lee la base de conocimiento desde un JSON en S3,
más una página estática (`web/`). No tiene usuarios ni procesos transaccionales, por eso la reemplazó la aplicación
Flask de la raíz del proyecto. Se conserva como referencia.

- `api/` código de la API, `web/` página estática, `base_conocimiento/` JSON de reglas
- `despliegue/` políticas IAM y el paquete de dependencias de Lambda (se puede regenerar con `pip install -t`)
- Pruebas: `cd legado/aws_lambda && python -m unittest discover -s pruebas`
