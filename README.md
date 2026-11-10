# Sistema Experto de Apoyo a la Orientación Académica

Aplicación **web** en **Python 3.10+** con **Flask** y **PostgreSQL** (local, en Docker o en la nube con **Neon**).
Identifica las **cinco hipótesis** (programas académicos) de mayor probabilidad para un aspirante mediante
**consultas granulares sucesivas** a la base de conocimiento, sin condicionales sobre el dominio.

## Estructura (patrón MVC)

```
run.py                          Punto de entrada: crea la app y arranca el servidor
app/
  __init__.py                   crear_app(): instancia el modelo y registra la vista y los controladores
  config.py                     Lee .env: base de datos, clave de sesión, puerto
  modelo/                       M: datos y lógica de negocio (no conoce Flask ni HTML)
    sistema_experto.py          Fachada del modelo: registrar, autenticar, evaluar, mantener gránulos
    entidades.py                Aspirante, Pregunta, Respuesta, Hecho, Granulo, ConteoHipotesis, ...
    motor_inferencia.py         MotorInferencia y TablaContabilizacion
    validaciones.py             Validación de respuestas, registro y pesos; errores de negocio
    seguridad.py                Hash de contraseñas (scrypt)
    conexion.py                 Pool de conexiones PostgreSQL
    dao/                        Un DAO por tabla: Aspirante, Ingeniero, Pregunta, Hecho, Hipotesis,
                                Granulo, ReglaNoConcluyente, Evaluacion
  vista/                        V: presentación
    templates/                  Plantillas Jinja (publico/, aspirante/, ingeniero/, componentes/)
    static/                     CSS, JavaScript e imágenes
    filtros.py                  Formato de porcentajes, números y fechas
  controlador/                  C: rutas Flask por rol
    publico.py                  Inicio, registro, ingreso y salida
    aspirante.py                Cuestionario, resultado e historial
    ingeniero.py                Panel, gránulos, reglas y evaluaciones
    sesion.py                   Sesión por rol y protección CSRF
bd/                             Scripts SQL: esquema, carga del conocimiento, consultas de gránulos
docs/                           Diagrama de clases DAO y MVC, roles y casos de uso, diseño de la interfaz
pruebas/                        Pruebas del motor y de la capa web (sin base de datos)
legado/aws_lambda/              Versión anterior: API en AWS Lambda + base de conocimiento en S3
.claude/skills/                 Skill oficial frontend-design de Anthropic usada para la interfaz
```

Flujo de una petición: **navegador → controlador → modelo (SistemaExperto → DAO / motor → PostgreSQL) → controlador → vista (plantilla) → navegador**.

## 1. Preparar la base de datos

**Opción A: Docker (recomendada).** `docker compose up -d` crea PostgreSQL 17 en el puerto 5439. La primera vez
carga los tres scripts de `bd/` de forma automática.

**Opción B: PostgreSQL local o Neon.** Ejecute en orden `bd/01_esquema.sql`, `bd/02_carga_conocimiento.sql` y
`bd/03_consultas_granulos.sql` (pgAdmin › Query Tool, o en Neon › SQL Editor).

## 2. Configurar (.env)

Copie `.env.example` como `.env` y complete los datos. `SEO_BD_PERFIL` elige el servidor (`local` o `neon`).
Defina `SEO_CLAVE_SECRETA` para que las sesiones sobrevivan a un reinicio del servidor:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

## 3. Instalar y ejecutar

```
python -m pip install -r requirements.txt
python run.py                               # desarrollo: http://127.0.0.1:5000
python run.py --produccion                  # waitress en 0.0.0.0:5000
python -m unittest discover -s pruebas -v   # pruebas
```

Cuentas de prueba que carga `02_carga_conocimiento.sql` (cámbielas en un entorno real):

| Rol | Correo | Contraseña |
|---|---|---|
| Ingeniero del conocimiento | ingeniero.conocimiento@umb.edu.co | Ingeniero2026* |
| Aspirante | laura.martinez@correo.com | Aspirante2026* |

## Funcionalidad por rol

**Aspirante:** crear una cuenta, iniciar sesión, responder el cuestionario de 11 preguntas (con clasificación en vivo
según los rangos de la base de conocimiento), ver el resultado con las cinco hipótesis, la explicación por reglas y la
tabla de contabilización, consultar su historial de evaluaciones e imprimir o guardar el resultado en PDF.

**Ingeniero del conocimiento:** ver un panel con indicadores, consultar los gránulos por hipótesis, agregar gránulos,
editar su peso, activarlos o desactivarlos, revisar las reglas RN y los rangos RC, y buscar y revisar todas las
evaluaciones.

Detalle de clases, roles y rutas en [docs/diagrama_clases_dao.md](docs/diagrama_clases_dao.md).

## Cómo infiere (sin condicionales)

1. **RF-02** Por cada una de las 11 respuestas, una consulta devuelve el hecho cuyo rango contiene el valor.
2. **RF-03** Por cada hecho, una consulta a `granulos_hecho_hipotesis`. Cada gránulo suma 1 coincidencia y su peso
   en la tabla de contabilización de la hipótesis.
3. **RF-03** P(h) = suma de pesos de h ÷ suma de pesos de todas las hipótesis × 100. Se ordena por probabilidad,
   coincidencias y código, y se toman las cinco primeras.
4. Las reglas RN se evalúan contando hechos por (tipo de variable, valor), con un operador tomado de la base de conocimiento.
5. La evaluación completa se guarda en **una sola transacción**. Los triggers de la base impiden modificarla después (RNF-04).

## Seguridad

Las contraseñas se guardan con hash scrypt. Las rutas están protegidas por rol, los formularios tienen token CSRF y la
cookie de sesión es HttpOnly y SameSite=Lax. Las consultas usan parámetros, sin concatenar valores, y cada aspirante
solo puede ver sus propias evaluaciones.
