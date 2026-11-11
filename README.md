# Sistema Experto de Apoyo a la Orientación Académica

Aplicación **web** en **Python 3.10+** con **Flask** y **PostgreSQL** (local, en Docker o en la nube con **Neon**).
A partir de las respuestas de un aspirante a un cuestionario de 23 preguntas, identifica las **cinco hipótesis**
(programas académicos) de mayor probabilidad de afinidad mediante **consultas granulares sucesivas** a una base de
conocimiento, sin sentencias condicionales sobre el dominio en el código.

> El resultado es una **probabilidad** y un **grado de coincidencia**, no una decisión ni una recomendación de admisión.
> El conocimiento del experto fue simulado con IA y validado por el ingeniero del conocimiento; los 18 ítems de intereses
> se inspiran en el modelo RIASEC de Holland y no son un test psicométrico estandarizado.

El documento técnico completo (formulación, manual técnico, reglas, diagramas y aplicación web) está en
[`docs/sistema_experto_academico-2.pdf`](docs/sistema_experto_academico-2.pdf).

## Contenido

1. [Qué hace](#qué-hace)
2. [Base de conocimiento](#base-de-conocimiento)
3. [Cómo infiere](#cómo-infiere)
4. [Diagramas](#diagramas)
5. [Capturas de la aplicación](#capturas-de-la-aplicación)
6. [Estructura del proyecto (MVC)](#estructura-del-proyecto-mvc)
7. [Instalación y ejecución](#instalación-y-ejecución)
8. [Funcionalidad por rol y rutas](#funcionalidad-por-rol-y-rutas)
9. [Seguridad](#seguridad)
10. [Pruebas](#pruebas)
11. [Versión anterior](#versión-anterior)

## Qué hace

El aspirante responde tres bloques de preguntas:

| Bloque | Preguntas | Respuesta | Clasificación |
|---|---|---|---|
| Desempeño académico | 4 notas (P01–P04): Lógico-Matemática, Científico-Investigativa, Social-Humanística, Administrativo-Financiera | Promedio de 1,0 a 5,0 | Alto (4,00–5,00), Medio (3,50–3,99), Bajo (1,00–3,49) |
| Intereses vocacionales (RIASEC) | 18 actividades (P05–P22), tres por categoría: Realista, Investigativo, Artístico, Social, Emprendedor, Convencional | Escala de 1 (me desagrada mucho) a 5 (me gusta mucho) | Por posición del promedio frente a las demás categorías (código Holland): Primera (1.º), Segunda (2.º), Tercera (3.º), Posterior (4.º a 6.º) |
| Estilo de trabajo | 1 pregunta (P23) | Escala de 1 (siempre por mi cuenta) a 5 (siempre en equipo) | Independiente (1,00–2,49), Indistinto (2,50–3,49), Equipo (3,50–5,00) |

Con esas respuestas el sistema deriva un hecho por variable (11 hechos), consulta los gránulos de conocimiento de cada
hecho, contabiliza los aportes por programa (peso × grado de certeza del hecho), calcula la probabilidad y el grado de
coincidencia de cada uno y presenta los cinco primeros, con la explicación de las reglas que los respaldan.

## Base de conocimiento

Todo el conocimiento está guardado como **datos** en PostgreSQL (esquema `conocimiento`), no en el código. Se puede
modificar sin cambiar el programa.

| Elemento | Cantidad | Tabla | Descripción |
|---|---|---|---|
| Hipótesis | 24 | `hipotesis_programas` | Programas académicos H01 a H24 |
| Variables | 11 | `variables_perfil` | 4 áreas, 6 categorías RIASEC y estilo; criterio RANGO o POSICION y si pondera intensidad |
| Preguntas | 23 | `preguntas_cuestionario_vocacional` | Enunciado, tipo (nota o escala), dominio y textos de la escala |
| Hechos (reglas RC) | 39 | `hechos_perfil` | Variable + valor con su rango (de promedio o de posición), sin huecos entre rangos |
| Gránulos (reglas RG) | 168 | `granulos_hecho_hipotesis` | Hecho → hipótesis con un peso (7 por programa) |
| Reglas RN | 3 | `reglas_resultado_no_concluyente` | Condiciones que marcan el resultado como no concluyente |

Cada programa tiene siete gránulos: área Alto 0,40 y Medio 0,20; interés en primera preferencia 0,40, segunda 0,25 y
tercera 0,10; estilo propio 0,20 e Indistinto 0,10. El máximo alcanzable por un perfil ideal es 1,00.

Reglas de resultado no concluyente (se evalúan por métrica, operador y umbral guardados en la base):

- **RN-01** Las cuatro áreas con desempeño Bajo (conteo de hechos = 4).
- **RN-02** Tres o más categorías RIASEC empatadas en primera preferencia (conteo de hechos ≥ 3).
- **RN-03** El programa de primer lugar coincide en menos de la mitad con el perfil (grado de coincidencia < 0,50).

Las transacciones de cada evaluación se guardan en el esquema `transaccional` (aspirantes, evaluaciones, respuestas,
hechos del aspirante con su grado, tabla de contabilización, cinco hipótesis y marcas de resultado no concluyente).

Scripts SQL en [`bd/`](bd):

| Script | Contenido |
|---|---|
| `01_esquema.sql` | Esquemas, tablas, claves, restricciones y triggers |
| `02_carga_conocimiento.sql` | Carga del conocimiento y cuentas de prueba |
| `03_consultas_granulos.sql` | Consultas de gránulos por hipótesis |

## Cómo infiere

El motor (`app/modelo/motor_inferencia.py`) no contiene condicionales sobre programas, áreas, categorías ni valores.

1. **RF-02. Derivación de hechos (reglas RC).** Una consulta agrupa las 23 respuestas por variable, calcula el
   promedio, la posición de cada variable frente a las de su tipo (`DENSE_RANK`, los empates comparten lugar) y el
   grado de certeza (promedio ÷ 5 si la variable pondera intensidad; 1 para el estilo). Según el criterio de la
   variable, el promedio o la posición se ubica en el rango de un hecho.
2. **RF-03. Consulta granular (reglas RG).** Por cada hecho, una consulta independiente a `granulos_hecho_hipotesis`.
   Cada gránulo suma 1 coincidencia y aporta peso × grado a su hipótesis en la tabla de contabilización.
3. **RF-03. Probabilidad (reglas RI).** P(h) = suma de aportes de h ÷ suma de aportes de todas las hipótesis × 100.
   Grado de coincidencia = suma de aportes ÷ máximo alcanzable de h. Se ordena por suma, luego por coincidencias y
   luego por código; de las cinco primeras se informa la probabilidad entre ellas (suma 100 %).
4. **Reglas RN.** Cada regla calcula su métrica (conteo de hechos o coincidencia del primer lugar) y la compara con el
   operador y el umbral de la base de conocimiento, por tabla de despacho.
5. **RNF-04. Persistencia.** La evaluación completa se guarda en una sola transacción. Los triggers de la base impiden
   modificarla o eliminarla después.

Ejemplo (el mismo del documento técnico): notas 4,5 / 3,7 / 3,4 / 3,9; intereses I 4,33 > R 3,67 > S 3,33 > C 3,00 >
E 2,33 > A 1,67 (código Holland I-R-S); estilo 2 (Independiente). Resultado: Ingeniería de Software 25,10 %
(coincidencia 90,6 %), Ingeniería Mecánica 20,59 %, Ingeniería de Sistemas 19,56 %, Biología 19,23 % y Estadística 15,51 %.

## Diagramas

Los diagramas en SVG se generan con [`docs/diagramas/generar_diagramas.py`](docs/diagramas/generar_diagramas.py)
(también se exportan a PDF en `docs/*.svg.pdf`). Los diagramas hechos en draw.io están en PDF en `docs/` y aquí se
muestran en PNG.

### Árbol de decisión

Cada nivel es un hecho con su peso (área Alta 0,40 → interés Alto 0,40 → estilo 0,20) y cada hoja es una hipótesis.
La rama roja agrupa las condiciones de resultado no concluyente.
PDF: [`docs/Arbol_de_Decision_corregido.drawio.pdf`](docs/Arbol_de_Decision_corregido.drawio.pdf)

![Árbol de decisión](docs/diagramas/Arbol_de_Decision.png)

### Modelo relacional (bases de conocimiento y transaccional)

PDF: [`docs/Modelo_Relacional_Corregido.drawio.pdf`](docs/Modelo_Relacional_Corregido.drawio.pdf)

![Modelo relacional](docs/diagramas/Modelo_Relacional.png)

### Casos de uso de alto nivel

Roles: aspirante e ingeniero del conocimiento.
PDF: [`docs/CasosDeUso.svg.pdf`](docs/CasosDeUso.svg.pdf)

![Casos de uso](docs/diagramas/CasosDeUso.svg)

### Caja negra del sistema experto

PDF: [`docs/CajaNegra.drawio.pdf`](docs/CajaNegra.drawio.pdf)

![Caja negra](docs/diagramas/Caja_Negra.png)

### Diagrama de flujo de datos

Nivel 0 (contexto). PDF: [`docs/DFD_Nivel0.drawio.pdf`](docs/DFD_Nivel0.drawio.pdf)

![DFD nivel 0](docs/diagramas/DFD_Nivel0.png)

Nivel 1 del sistema de inferencia: los procesos 2.0 a 6.0 forman el motor de inferencia.

![DFD nivel 1](docs/diagramas/DFD_Nivel1.png)

### Diagrama de clases DAO

`BaseDAO` y un DAO por tabla, la fábrica de conexiones, la fachada `SistemaExperto` y el `MotorInferencia`.
PDF: [`docs/Clases_DAO.svg.pdf`](docs/Clases_DAO.svg.pdf) · Detalle en Mermaid:
[`docs/diagrama_clases_dao.md`](docs/diagrama_clases_dao.md)

![Diagrama de clases DAO](docs/diagramas/Clases_DAO.svg)

### Arquitectura de la aplicación web (MVC)

PDF: [`docs/Arquitectura_Web_MVC.svg.pdf`](docs/Arquitectura_Web_MVC.svg.pdf)

![Arquitectura web MVC](docs/diagramas/Arquitectura_Web_MVC.svg)

## Capturas de la aplicación

**Cuestionario por bloques.** Cada bloque explica qué mide, qué se responde y cómo se clasifica; en el bloque de
intereses muestra en vivo el orden de preferencias (código Holland). No deja avanzar con respuestas vacías o fuera de rango y termina con una revisión de todas las respuestas.

![Cuestionario](docs/capturas/cuestionario.png)

**Resultado.** Programa con mayor probabilidad, cinco hipótesis, perfil clasificado con su certeza, explicación por reglas y tabla
de contabilización.

![Resultado](docs/capturas/resultado.png)

Diseño de la interfaz (colores, tipografía y decisiones de uso): [`docs/diseno_interfaz.md`](docs/diseno_interfaz.md).

## Estructura del proyecto (MVC)

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
    conexion.py                 Pool de conexiones PostgreSQL (FabricaConexion)
    dao/                        BaseDAO y un DAO por tabla: Aspirante, Ingeniero, Pregunta, Hecho, Hipotesis,
                                Granulo, ReglaNoConcluyente, Evaluacion
  vista/                        V: presentación
    templates/                  Plantillas Jinja (publico/, aspirante/, ingeniero/, componentes/)
    static/                     CSS, JavaScript e imágenes
    filtros.py                  Formato de porcentajes, números y fechas
  controlador/                  C: rutas Flask (Blueprints) por rol
    publico.py                  Inicio, registro, ingreso y salida
    aspirante.py                Cuestionario, resultado e historial
    ingeniero.py                Panel, gránulos, reglas y evaluaciones
    sesion.py                   Sesión por rol y protección CSRF
bd/                             Scripts SQL: esquema, carga del conocimiento, consultas de gránulos
docs/                           Documento técnico, diagramas (PDF, SVG y PNG) y capturas
pruebas/                        Pruebas del motor y de la capa web (sin base de datos)
legado/aws_lambda/              Versión anterior: API en AWS Lambda + base de conocimiento en S3
```

Flujo de una petición: **navegador → controlador → modelo (SistemaExperto → DAO / motor → PostgreSQL) →
controlador → vista (plantilla) → navegador**.

## Instalación y ejecución

Requisitos: Python 3.10 o superior y un servidor PostgreSQL (Docker, instalado en el equipo o Neon).

### 1. Preparar la base de datos

**Opción A: Docker (recomendada).**

```
docker compose up -d
```

Crea PostgreSQL 17 en el puerto **5439** (usuario `admin`, contraseña `admin123`, base
`sistema_experto_orientacion`). La primera vez, cuando el volumen está vacío, carga automáticamente los tres scripts
de `bd/`.

**Opción B: PostgreSQL local o Neon.** Ejecute en orden `bd/01_esquema.sql`, `bd/02_carga_conocimiento.sql` y
`bd/03_consultas_granulos.sql` (pgAdmin › Query Tool, o Neon › SQL Editor).

> **Si ya tenía cargada la versión anterior** (11 preguntas): vuelva a ejecutar los tres scripts. `01_esquema.sql`
> borra y crea de nuevo los dos esquemas, así que se pierden las evaluaciones y cuentas creadas; las cuentas de
> prueba vuelven con `02_carga_conocimiento.sql`. Con Docker: `docker compose down -v` y `docker compose up -d`.

### 2. Configurar el archivo `.env`

Copie `.env.example` como `.env` (en la misma carpeta de `run.py`) y complete los datos:

- `SEO_BD_PERFIL`: servidor a usar, `local` o `neon`.
- `LOCAL_BD_*` o `NEON_BD_*`: datos de conexión. Si usa Docker, ponga `LOCAL_BD_PUERTO=5439`,
  `LOCAL_BD_USUARIO=admin` y `LOCAL_BD_CLAVE=admin123`.
- `SEO_CLAVE_SECRETA`: clave para firmar las sesiones; así sobreviven a un reinicio del servidor. Genere una con:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

El archivo `.env` no se sube al repositorio (está en `.gitignore`).

### 3. Instalar dependencias y ejecutar

```
python -m pip install -r requirements.txt
python run.py                  # desarrollo: http://127.0.0.1:5000
python run.py --produccion     # servidor waitress en 0.0.0.0:5000
```

Dependencias: Flask, psycopg2-binary y waitress.

### Cuentas de prueba

Las carga `02_carga_conocimiento.sql` (cámbielas en un entorno real):

| Rol | Correo | Contraseña |
|---|---|---|
| Ingeniero del conocimiento | ingeniero.conocimiento@umb.edu.co | Ingeniero2026* |
| Aspirante | laura.martinez@correo.com | Aspirante2026* |

También puede crear una cuenta de aspirante desde la página de inicio.

## Funcionalidad por rol y rutas

**Aspirante:** crear una cuenta, iniciar sesión, responder el cuestionario por bloques (con la descripción de cada
pregunta y la clasificación en vivo según los rangos de la base de conocimiento), ver el resultado con las cinco
hipótesis, su perfil (promedio, posición y certeza), la explicación por reglas y la tabla de contabilización,
consultar su historial de evaluaciones e imprimir o guardar el resultado en PDF.

**Ingeniero del conocimiento:** ver un panel con indicadores, consultar los gránulos por hipótesis, agregar gránulos,
editar su peso, activarlos o desactivarlos, revisar las reglas RN y los rangos RC, y buscar y revisar todas las
evaluaciones.

| Rol | Caso de uso | Requerimiento | Ruta (método HTTP) |
|---|---|---|---|
| Público | CU-01 Registrarse como aspirante | RF-01 | `POST /registro` |
| Aspirante e ingeniero | CU-02 Iniciar sesión (y cerrarla) | RF-01 | `POST /ingresar`, `POST /salir` |
| Aspirante | CU-03 y CU-04 Responder el cuestionario y ejecutar la inferencia | RF-02, RF-03 | `GET` y `POST /aspirante/cuestionario` |
| Aspirante | CU-05 Consultar el resultado de la evaluación | RF-03 | `GET /aspirante/evaluaciones/<id>` |
| Aspirante | CU-08 Consultar el historial de evaluaciones | RF-02 | `GET /aspirante/` |
| Ingeniero | Panel con indicadores de la base de conocimiento | RF-04 | `GET /ingeniero/` |
| Ingeniero | CU-06 Consultar gránulos por hipótesis | RF-04 | `GET /ingeniero/granulos?hipotesis=H01` |
| Ingeniero | CU-07 Cargar y mantener el conocimiento | RF-04 | `GET` y `POST /ingeniero/granulos/nuevo`, `GET` y `POST /ingeniero/granulos/<id>` |
| Ingeniero | CU-09 Consultar reglas RN y rangos RC | RF-04 | `GET /ingeniero/reglas` |
| Ingeniero | CU-10 Supervisar las evaluaciones | RF-04 | `GET /ingeniero/evaluaciones`, `GET /ingeniero/evaluaciones/<id>` |

La interfaz funciona también sin JavaScript: el cuestionario muestra los tres bloques juntos.

## Seguridad

- Contraseñas guardadas con hash scrypt.
- Rutas protegidas por rol; cada aspirante solo puede ver sus propias evaluaciones.
- Todos los formularios llevan token CSRF.
- Cookie de sesión HttpOnly y SameSite=Lax.
- Consultas con parámetros, sin concatenar valores en el SQL.
- Las evaluaciones no se pueden modificar ni eliminar después de registradas (triggers en la base).

## Pruebas

```
python -m unittest discover -s pruebas -v
```

14 pruebas, sin base de datos: motor de inferencia (`test_motor_inferencia.py`) y capa web (`test_web.py`).

## Versión anterior

[`legado/aws_lambda/`](legado) conserva la primera versión web: una API FastAPI en AWS Lambda que lee la base de
conocimiento desde un JSON en S3, más una página estática. No tenía usuarios ni procesos transaccionales, por eso la
reemplazó la aplicación Flask. Detalles en [`legado/README.md`](legado/README.md).
