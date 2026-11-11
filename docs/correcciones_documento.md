# Correcciones pendientes del documento técnico

Revisión de `docs/sistema_experto_academico-2.pdf` (45 páginas) frente al sistema actual: código, base de datos y
`bd/02_carga_conocimiento.sql`. El documento todavía describe la **versión anterior**, con 11 preguntas, el test
RIASEC en porcentajes, 32 hechos, 72 gránulos y reglas RN de empate entre áreas.

El PDF se exportó desde Writer, así que estas correcciones se aplican en el archivo fuente (.odt/.docx) y después se
vuelve a exportar. Cada apartado indica la página, qué dice hoy y el texto de reemplazo.

> **Ya aplicado en el PDF (10/11/2026):** se eliminó la Figura 14 («recorrido por el árbol de decisión»), que ocupaba la
> página 38. También se renumeraron las figuras 15–21 como 14–20, se corrigió el párrafo de la pág. 35 y se ajustaron
> los números de página y la tabla de contenido. El documento tiene ahora 44 páginas: las páginas citadas abajo a partir
> de la 38 corresponden a la numeración anterior (réstele 1). Si se vuelve a exportar desde Writer, haga el mismo cambio
> en el archivo fuente.

Datos actuales de referencia: 23 preguntas, 11 variables, 39 hechos (RC-01 a RC-39), 168 gránulos (RG-001 a RG-168),
4 reglas RI y 3 reglas RN.

---

## 1. Resumen de discrepancias

| Pág. | Sección | Qué dice hoy | Qué debe decir |
|---|---|---|---|
| 5 | Objetivos de negocio | Lista vacía («1.», «2.»). El texto de los dos objetivos quedó dentro del proceso 1 | Mover los dos párrafos a los objetivos de negocio 1 y 2 |
| 6 | Listado de procesos | «cuestionario de evaluación (11 preguntas)» | 23 preguntas |
| 6 | RF-02 | «11 preguntas (promedio por área, **porcentaje** por categoría RIASEC y estilo)» | 23 preguntas: 4 notas, 18 actividades RIASEC (escala 1–5) y estilo (escala 1–5) |
| 7 | RNF-01 | «Las 11 preguntas se presentan en un único formulario» | 23 preguntas, tres bloques |
| 8–10 | Levantamiento | Rangos con huecos (3.5–3.9, 1.0–3.4), RIASEC en % (≥70, 40–69, <40), estilo binario, RN «dos o más áreas en Alto» | Rangos sin huecos, RIASEC por posición (código Holland), estilo con tres valores, nuevas RN |
| 10–13 | Árbol de decisión (Fig. 1–5) | 3 niveles por rama, 71 ramas y 27 hojas, «interés Alto» | Cada programa tiene 7 gránulos (Alto/Medio, Primera/Segunda/Tercera, estilo propio/Indistinto). **Rehacer las figuras** |
| 14–16 | Reglas RC | RC-01 a RC-32, «11 respuestas → 11 hechos», RIASEC en % | RC-01 a RC-39 (ver §3) |
| 16–21 | Reglas RG | RG-01 a RG-72, 3 por hipótesis, peso total 1.00 | RG-001 a RG-168, 7 por hipótesis (ver §4) |
| 21–22 | Reglas RI | La suma es de **pesos** | La suma es de **aportes = peso × grado de certeza**; se agrega el grado de coincidencia y la probabilidad entre las cinco (ver §5) |
| 22 | Reglas RN | RN-02 «≥ 2 áreas Alto», RN-03 «≥ 2 intereses Alto» | RN-02 «≥ 3 intereses en Primera», RN-03 «coincidencia del 1.er lugar < 0,50» (ver §6) |
| 22–23 | Ejemplo + Tabla 1 | RIASEC en %, suma 6.40, H01 15.63 % … | Ítems en escala 1–5, suma 8,9032, H01 10,18 % / 25,10 % … (ver §7) |
| 23–24 | Tabla 2 | variables 11, **preguntas 11**, **hechos 32**, **gránulos 72**; faltan `hechos_aspirante` y el grado | preguntas 23, hechos 39, gránulos 168; agregar `hechos_aspirante` (ver §8) |
| 24 | Carga del conocimiento | «11 variables con sus 11 preguntas, 32 hechos, 72 gránulos» y `RG-01` en el ejemplo | 23 preguntas, 39 hechos, 168 gránulos; `RG-001` |
| 25–27 | Tablas 3 y 4 | H01 con 3 gránulos; 3 gránulos y peso máximo 1.00 por hipótesis | H01 con 7 gránulos; 7 gránulos por hipótesis, suma de pesos 1,65 y máximo alcanzable 1,00 (ver §9) |
| 28 | CU-03 (Tabla 7) | «responde las 11 preguntas» | «responde las 23 preguntas» |
| 30–31 | Caja negra, DFD (Fig. 8–10) | Entradas de la versión anterior (%) | Rehacer con 23 respuestas y el almacén `hechos_aspirante` |
| 31–32 | Tabla 8 | EvaluacionDAO con 5 tablas; HechoDAO «derivación del hecho por rango» | 6 tablas (agregar `hechos_aspirante`); HechoDAO deriva los 11 hechos en una consulta (promedio, posición y grado) |
| 33 | Figura 11 (clases DAO) | Versión vieja: `_derivar`, `_conteos`, `calcular_probabilidades`, «5 tablas» | Reemplazar por `docs/Clases_DAO.svg.pdf` (ya corregido) |
| 29 | Figura 7 (casos de uso) | Versión anterior del diagrama | Reemplazar por `docs/CasosDeUso.svg.pdf` (ya corregido) |
| 39 | Figura 15 (arquitectura) | No menciona los hechos | Reemplazar por `docs/Arquitectura_Web_MVC.svg.pdf` (ya corregido) |
| 34–35 | Fragmento de `inferir` | Código anterior (`_derivar` por respuesta, `calcular_probabilidades`, `Counter`) | Código actual (ver §10) |
| 35–36 | Ejecución + Tabla 10 | «11 consultas para derivar + 11 granulares», 16 hipótesis, mismos % de la Tabla 1 | 1 consulta de derivación + 11 granulares, 22 hipótesis, nuevos % (ver §11) |
| 36 | Figura 12 | Captura del cuestionario anterior | Nueva captura (`docs/capturas/cuestionario.png`) |
| 37 | Figura 13 | Captura del resultado anterior | Reemplazar por `docs/capturas/resultado.png`. (La Fig. 14 del árbol ya se eliminó.) |
| 41 (antes 42) | Figura 15 (antes 16) | La captura de inicio dice «Responda 11 preguntas» y «15,63 %» | Nueva captura de la página de inicio |

---

## 2. Texto de reemplazo: cuestionario (págs. 6–7)

**Proceso 2.** Aplicación del cuestionario de evaluación (23 preguntas en tres bloques).

**RF-02. Evaluación vocacional.** El sistema aplica al aspirante un cuestionario de 23 preguntas en tres bloques:
el promedio de notas de cuatro áreas académicas (P01–P04, escala 1,0 a 5,0), 18 actividades del modelo RIASEC, tres
por categoría (P05–P22, escala 1 «me desagrada mucho» a 5 «me gusta mucho»), y el estilo de trabajo (P23, escala 1
«siempre por mi cuenta» a 5 «siempre en equipo»). Valida sus respuestas, deriva un hecho por cada una de las 11
variables del perfil según los rangos de la base de conocimiento, con su grado de certeza, y conserva el historial
de evaluaciones de cada aspirante.

**RNF-01. Usabilidad (interfaz de usuario).** Las 23 preguntas se presentan en un único formulario de tres bloques
(desempeño académico, intereses y estilo de trabajo). El formulario señala el campo con error y no permite enviar
respuestas fuera de dominio o sin diligenciar. El resultado se presenta como probabilidad de afinidad, no como una
recomendación.

### Estructura del cuestionario (se sugiere agregarla como tabla nueva después de RF-02)

| Bloque | Preguntas | Variable | Respuesta | Clasificación (hecho) |
|---|---|---|---|---|
| Desempeño académico | P01 | Desempeño Lógico-Matemática | Nota 1,0–5,0 | Alto 4,00–5,00 · Medio 3,50–3,99 · Bajo 1,00–3,49 |
| | P02 | Desempeño Científico-Investigativa | Nota 1,0–5,0 | ídem |
| | P03 | Desempeño Social-Humanística | Nota 1,0–5,0 | ídem |
| | P04 | Desempeño Administrativo-Financiera | Nota 1,0–5,0 | ídem |
| Intereses (RIASEC) | P05–P07 | Interés Realista | Escala 1–5 (3 ítems, se promedian) | Posición del promedio frente a las 6 categorías: Primera (1.º), Segunda (2.º), Tercera (3.º), Posterior (4.º–6.º) |
| | P08–P10 | Interés Investigativo | ídem | ídem |
| | P11–P13 | Interés Artístico | ídem | ídem |
| | P14–P16 | Interés Social | ídem | ídem |
| | P17–P19 | Interés Emprendedor | ídem | ídem |
| | P20–P22 | Interés Convencional | ídem | ídem |
| Estilo de trabajo | P23 | Estilo de trabajo | Escala 1–5 | Independiente 1,00–2,49 · Indistinto 2,50–3,49 · Equipo 3,50–5,00 |

Ítems RIASEC (enunciados cargados en la base):

- **Realista:** P05 Armar, reparar o ajustar aparatos, máquinas o instalaciones. P06 Trabajar con herramientas en un
  taller o en un laboratorio de prácticas. P07 Hacer actividades al aire libre, como cultivar, construir o tomar
  medidas en campo.
- **Investigativo:** P08 Investigar por qué ocurre un fenómeno natural o técnico. P09 Resolver problemas difíciles de
  matemáticas, lógica o programación. P10 Diseñar y realizar experimentos para comprobar una idea.
- **Artístico:** P11 Dibujar, diseñar o crear piezas visuales. P12 Escribir textos, guiones o contenidos propios.
  P13 Participar en actividades de música, teatro, fotografía o video.
- **Social:** P14 Explicarle un tema a un compañero que no lo entiende. P15 Escuchar y ayudar a personas que
  atraviesan una dificultad. P16 Participar en actividades comunitarias o de voluntariado.
- **Emprendedor:** P17 Liderar un grupo para alcanzar una meta. P18 Convencer a otras personas de una idea, un
  producto o una propuesta. P19 Organizar y poner en marcha un negocio o un evento.
- **Convencional:** P20 Llevar registros ordenados de datos, cuentas o inventarios. P21 Revisar documentos o cifras
  para encontrar errores. P22 Seguir procedimientos y normas detalladas para completar una tarea.

> Nota que conviene conservar: los 18 ítems se inspiran en el modelo RIASEC de Holland (1997) y no son un test
> psicométrico estandarizado.

---

## 3. Reglas de clasificación de hechos (págs. 14–16)

**Párrafo introductorio.** Estas reglas convierten las 23 respuestas del aspirante en exactamente un hecho por cada
una de las 11 variables del perfil. Primero se promedian las preguntas de cada variable: las áreas y el estilo tienen
una pregunta, y cada categoría RIASEC tiene tres. Las áreas y el estilo se clasifican por **rango del promedio**. Las
categorías RIASEC se clasifican por la **posición** de su promedio frente a las otras cinco (código Holland); las
categorías empatadas comparten posición. Los rangos son contiguos y no dejan valores sin clasificar. Cada hecho
lleva un **grado de certeza**: el promedio dividido entre 5 para las áreas y los intereses, y 1 para el estilo.

- **RC-01 a RC-12 (áreas).** Para cada área (Lógico-Matemática, Científico-Investigativa, Social-Humanística,
  Administrativo-Financiera):
  - SI 4,00 ≤ promedio ≤ 5,00 ENTONCES «Desempeño <área> = Alto».
  - SI 3,50 ≤ promedio ≤ 3,99 ENTONCES «… = Medio».
  - SI 1,00 ≤ promedio ≤ 3,49 ENTONCES «… = Bajo».

  (RC-01/02/03 Lógico-Matemática; RC-04/05/06 Científico-Investigativa; RC-07/08/09 Social-Humanística;
  RC-10/11/12 Administrativo-Financiera.)
- **RC-13 a RC-36 (intereses).** Para cada categoría (Realista, Investigativo, Artístico, Social, Emprendedor,
  Convencional):
  - SI posición = 1 ENTONCES «Interés <categoría> = Primera».
  - SI posición = 2 ENTONCES «… = Segunda».
  - SI posición = 3 ENTONCES «… = Tercera».
  - SI 4 ≤ posición ≤ 6 ENTONCES «… = Posterior».

  (RC-13 a RC-16 Realista; RC-17 a RC-20 Investigativo; RC-21 a RC-24 Artístico; RC-25 a RC-28 Social;
  RC-29 a RC-32 Emprendedor; RC-33 a RC-36 Convencional.)
- **RC-37.** SI 1,00 ≤ estilo ≤ 2,49 ENTONCES «Estilo de trabajo = Independiente».
- **RC-38.** SI 2,50 ≤ estilo ≤ 3,49 ENTONCES «Estilo de trabajo = Indistinto».
- **RC-39.** SI 3,50 ≤ estilo ≤ 5,00 ENTONCES «Estilo de trabajo = Equipo».

En la entrevista (págs. 8–10) hay que actualizar las respuestas del experto con estos mismos criterios:

- Áreas: Alto 4,00–5,00, Medio 3,50–3,99, Bajo 1,00–3,49.
- Intereses: la categoría en primera, segunda y tercera posición forma el código Holland del aspirante.
- Estilo: Independiente, Indistinto o Equipo.
- Pesos: área Alto 0,40 y Medio 0,20; interés en Primera 0,40, Segunda 0,25 y Tercera 0,10; estilo propio 0,20 e
  Indistinto 0,10.
- Condiciones de resultado no concluyente: las de §6.

---

## 4. Reglas de conocimiento (gránulos) (págs. 16–21)

**Párrafo de reemplazo.** Cada regla de conocimiento tiene una única condición y una única conclusión, por lo que
constituye un gránulo de conocimiento: relaciona un hecho con una hipótesis y un peso. Cada hipótesis tiene siete
gránulos:

- desempeño **Alto** en su área (0,40) y **Medio** (0,20);
- interés en **Primera** (0,40), **Segunda** (0,25) y **Tercera** (0,10) posición en su categoría RIASEC;
- su estilo de trabajo (0,20) y el estilo **Indistinto** (0,10).

Con 24 hipótesis se obtienen 168 reglas, RG-001 a RG-168. Como un perfil tiene un solo hecho por variable, el máximo
que puede acumular una hipótesis es 0,40 + 0,40 + 0,20 = 1,00.

Ejemplo para H01 (Ingeniería de Software): RG-001 «Desempeño Lógico-Matemática = Alto» 0,40 · RG-002 «= Medio» 0,20 ·
RG-003 «Interés Investigativo = Primera» 0,40 · RG-004 «= Segunda» 0,25 · RG-005 «= Tercera» 0,10 ·
RG-006 «Estilo = Independiente» 0,20 · RG-007 «Estilo = Indistinto» 0,10.

Para no listar las 168 reglas una por una, se recomienda presentar una tabla con las 24 hipótesis y su área,
categoría RIASEC y estilo, que no cambiaron frente a la versión anterior, más el patrón de los siete pesos.

---

## 5. Reglas de inferencia (págs. 21–22)

- **RI-01.** SI un hecho del aspirante es igual al hecho de un gránulo ENTONCES se suma 1 a las coincidencias de la
  hipótesis del gránulo y se suma a su suma de aportes el **aporte = peso del gránulo × grado de certeza del hecho**,
  en la tabla de contabilización.
- **RI-02.** SI una hipótesis tiene al menos una coincidencia ENTONCES su probabilidad = suma de aportes de la
  hipótesis ÷ suma de aportes de todas las hipótesis con coincidencias × 100, y su **grado de coincidencia** = suma de
  aportes ÷ máximo alcanzable por la hipótesis (1,00).
- **RI-03.** SI dos hipótesis tienen la misma suma de aportes ENTONCES se ubica primero la de mayor número de
  coincidencias y, si persiste el empate, la de menor código.
- **RI-04.** SI una hipótesis ocupa una de las cinco primeras posiciones ENTONCES forma parte del resultado; entre
  esas cinco se informa además su probabilidad relativa, que suma 100 %.

---

## 6. Reglas de resultado no concluyente (pág. 22)

- **RN-01.** SI el número de hechos «Desempeño … = Bajo» es igual a 4 ENTONCES la evaluación recibe la marca
  «Resultado no concluyente» (las notas no distinguen un área de fortaleza).
- **RN-02.** SI el número de hechos «Interés … = Primera» es mayor o igual a 3 ENTONCES la evaluación recibe la
  marca (tres o más categorías RIASEC empatan en primera preferencia: los intereses no están diferenciados).
- **RN-03.** SI el grado de coincidencia de la hipótesis de primer lugar es menor que 0,50 ENTONCES la evaluación
  recibe la marca (el programa de primer lugar coincide en menos de la mitad con el perfil).

Las reglas se guardan con métrica (`CONTEO_HECHOS` o `COINCIDENCIA_PRIMERA`), operador y umbral, y el motor las
evalúa sin condicionales sobre el dominio.

---

## 7. Ejemplo de aplicación de las reglas y Tabla 1 (págs. 22–23)

**Texto de reemplazo.** Un aspirante registra promedio 4,5 en Lógico-Matemática, 3,7 en Científico-Investigativa,
3,4 en Social-Humanística y 3,9 en Administrativo-Financiera.

En las 18 actividades RIASEC obtiene estos promedios (ítems entre paréntesis):

| Categoría | Ítems | Promedio | Posición |
|---|---|---|---|
| Investigativo | 5, 4, 4 | 4,33 | 1.ª |
| Realista | 4, 3, 4 | 3,67 | 2.ª |
| Social | 3, 4, 3 | 3,33 | 3.ª |
| Convencional | 3, 3, 3 | 3,00 | 4.ª |
| Emprendedor | 2, 3, 2 | 2,33 | 5.ª |
| Artístico | 2, 1, 2 | 1,67 | 6.ª |

Su código Holland es I-R-S. En el estilo de trabajo responde 2, que corresponde a Independiente.

Las reglas de clasificación producen 11 hechos:

| Hecho | Grado de certeza |
|---|---|
| Lógico-Matemática = Alto | 0,90 |
| Científico-Investigativa = Medio | 0,74 |
| Social-Humanística = Bajo | 0,68 |
| Administrativo-Financiera = Medio | 0,78 |
| Investigativo = Primera | 0,866 |
| Realista = Segunda | 0,734 |
| Social = Tercera | 0,666 |
| Convencional = Posterior | 0,60 |
| Emprendedor = Posterior | 0,466 |
| Artístico = Posterior | 0,334 |
| Estilo = Independiente | 1 |

Los gránulos activados alcanzan a 22 hipótesis, y la suma de aportes de todas ellas es 8,9032. Por ejemplo, H01 suma
0,40 × 0,90 + 0,40 × 0,866 + 0,20 × 1 = 0,9064.

Ninguna regla de resultado no concluyente se cumple:

- RN-01 no se cumple: solo un área está en Bajo.
- RN-02 no se cumple: solo una categoría está en Primera.
- RN-03 no se cumple: el primer lugar coincide en un 90,64 %.

**Tabla 1. Tabla de contabilización del ejemplo (cinco primeras hipótesis)**

| Posición | Hipótesis | Coincidencias | Suma de aportes | Grado de coincidencia | Probabilidad (todas) | Probabilidad (entre las cinco) |
|---|---|---|---|---|---|---|
| 1 | H01 Ingeniería de Software | 3 | 0,9064 | 90,64 % | 10,18 % | 25,10 % |
| 2 | H03 Ingeniería Mecánica | 3 | 0,7435 | 74,35 % | 8,35 % | 20,59 % |
| 3 | H02 Ingeniería de Sistemas | 2 | 0,7064 | 70,64 % | 7,93 % | 19,56 % |
| 4 | H07 Biología | 3 | 0,6944 | 69,44 % | 7,80 % | 19,23 % |
| 5 | H05 Estadística | 2 | 0,5600 | 56,00 % | 6,29 % | 15,51 % |

Las 17 hipótesis restantes con coincidencias suman el 59,45 % de la probabilidad. Ya no hay empates entre los cinco
primeros, así que el párrafo sobre H03, H05 y H07 empatados se elimina.

> Estos valores salen de la evaluación real guardada en la base (evaluación 1) y de la prueba automatizada
> `pruebas/test_motor_inferencia.py`.

---

## 8. Tabla 2: tablas de la base de datos (págs. 23–24)

| Esquema | Tabla | Contenido | Registros |
|---|---|---|---|
| conocimiento | hipotesis_programas | Programas académicos (H01 a H24) | 24 |
| conocimiento | variables_perfil | 4 áreas, 6 categorías RIASEC y estilo; criterio RANGO o POSICION y si pondera intensidad | 11 |
| conocimiento | preguntas_cuestionario_vocacional | Preguntas, tipo (nota o escala), dominio y textos de la escala | **23** |
| conocimiento | hechos_perfil | Hechos con su rango de promedio o de posición (reglas RC) | **39** |
| conocimiento | granulos_hecho_hipotesis | Gránulos: hecho, hipótesis y peso (reglas RG) | **168** |
| conocimiento | reglas_resultado_no_concluyente | Reglas RN con métrica, operador y umbral | 3 |
| conocimiento | ingenieros_conocimiento | Responsables del conocimiento | 1 |
| transaccional | aspirantes | Personas que responden el cuestionario | 2 |
| transaccional | evaluaciones_vocacionales | Cada aplicación del cuestionario | 0 |
| transaccional | respuestas_aspirante | Respuesta a cada una de las 23 preguntas | 0 |
| transaccional | **hechos_aspirante** (nueva) | Hecho derivado por variable con su valor calculado, posición y grado de certeza | 0 |
| transaccional | contabilizacion_coincidencias_hipotesis | Coincidencias, suma de aportes, **grado de coincidencia** y probabilidad | 0 |
| transaccional | resultado_cinco_hipotesis | Las cinco hipótesis y su probabilidad entre ellas | 0 |
| transaccional | marcas_resultado_no_concluyente | Reglas RN que se cumplieron | 0 |

El modelo relacional (Figura 6) también debe incluir `hechos_aspirante` y las columnas nuevas. Las columnas nuevas
son `criterio_clasificacion` y `pondera_intensidad` en `variables_perfil`, `etiqueta_minima` y `etiqueta_maxima` en
preguntas, y `grado_coincidencia` en la contabilización.

**Carga del conocimiento (pág. 24).** «Se cargaron 24 hipótesis, 11 variables con sus **23 preguntas**, **39 hechos**
con sus rangos de clasificación, **168 gránulos** de conocimiento y 3 reglas de resultado no concluyente.» En el
ejemplo de INSERT, cambiar `'RG-01'` por `'RG-001'`.

---

## 9. Tablas 3, 4 y 5 (págs. 25–27)

**Tabla 3 (gránulos de H01).** Las siete filas de RG-001 a RG-007 que aparecen en §4.

**Tabla 4.** Cada hipótesis tiene 7 gránulos, y la suma de sus pesos es 1,65. El **peso máximo alcanzable** es 1,00,
porque por cada variable solo cuenta el gránulo de mayor peso (consulta C2 de `bd/03_consultas_granulos.sql`). La
columna «Hechos» queda así, por ejemplo para H01: «Lógico-Matemática Alto/Medio; Investigativo Primera/Segunda/Tercera;
Estilo Independiente/Indistinto».

**Tabla 5.** Sin cambios: para «Desempeño Lógico-Matemática = Alto» siguen saliendo H01 a H06 con 0,40.

---

## 10. Fragmento de código del motor (págs. 34–35)

Reemplazar por el método actual de `app/modelo/motor_inferencia.py`:

```python
    def inferir(self, respuestas) -> ResultadoInferencia:
        # RF-02 / RC: respuestas -> un hecho por variable del perfil (promedio, posición y grado).
        hechos, sin_hecho = self._hechos.derivar(respuestas)
        if sin_hecho:
            raise HechoNoDerivable(sin_hecho)

        # RF-03 / RG: una consulta granular por cada hecho; cada gránulo se contabiliza.
        tabla = TablaContabilizacion(self._granulos.maximos_por_hipotesis())
        for hecho in hechos:
            for granulo in self._granulos.por_hecho(hecho.id_hecho):
                tabla.registrar(granulo, hecho)

        # RF-03 / RI: probabilidades, grado de coincidencia y las cinco hipótesis.
        contabilizacion = tabla.calcular()
        cinco = seleccionar_cinco(contabilizacion)

        # RN: cada regla se evalúa con su métrica y su operador.
        cumple = lambda regla: OPERADORES[regla.operador](METRICAS[regla.metrica](regla, hechos, cinco), regla.umbral)
        marcas = tuple(filter(cumple, self._reglas.activas()))

        return ResultadoInferencia(tuple(hechos), tuple(contabilizacion), cinco, marcas)
```

El párrafo siguiente debe mencionar que `EvaluacionDAO.insertar` también guarda los **hechos derivados con su grado**
(tabla `hechos_aspirante`).

---

## 11. Ejecución del sistema de inferencia y Tabla 10 (págs. 35–36)

**Texto de reemplazo.** Con las respuestas del aspirante del ejemplo, registradas desde el cuestionario web (botón
«Usar respuestas de ejemplo»), el sistema:

1. deriva los 11 hechos en **una sola consulta**;
2. ejecuta 11 consultas granulares, una por hecho;
3. contabiliza 22 hipótesis;
4. presenta las cinco de mayor probabilidad (Tabla 10), que coinciden con la Tabla 1.

El resultado no tiene la marca «Resultado no concluyente».

El cuestionario se responde en tres bloques: desempeño académico, intereses y estilo de trabajo. Cada bloque explica
qué mide, qué se escribe y cómo se clasifica cada valor. No deja avanzar con respuestas vacías o fuera de rango, y al
final presenta una revisión de todas las respuestas con su clasificación (Figura 12). La Figura 13 muestra la página
de resultado.

**Tabla 10**

| Posición | Hipótesis | Programa | Coincidencias | Grado de coincidencia | Probabilidad |
|---|---|---|---|---|---|
| 1 | H01 | Ingeniería de Software | 3 | 90,64 % | 25,10 % |
| 2 | H03 | Ingeniería Mecánica | 3 | 74,35 % | 20,59 % |
| 3 | H02 | Ingeniería de Sistemas | 2 | 70,64 % | 19,56 % |
| 4 | H07 | Biología | 3 | 69,44 % | 19,23 % |
| 5 | H05 | Estadística | 2 | 56,00 % | 15,51 % |

La Figura 14 («recorrido por el árbol de decisión») ya se eliminó del PDF.

---

## 12. Figuras que hay que rehacer fuera de este repositorio

Estas figuras se hicieron en draw.io y sus archivos fuente no están en el proyecto. Siguen mostrando la versión
anterior:

- **Figuras 1–5, árbol de decisión** (`Arbol_de_Decision_corregido.drawio.pdf`): cada rama debe mostrar los niveles
  Alto/Medio, Primera/Segunda/Tercera e Independiente o Equipo/Indistinto, con sus pesos.
- **Figura 6, modelo relacional** (`Modelo_Relacional_Corregido.drawio.pdf`): agregar `hechos_aspirante` y las
  columnas nuevas.
- **Figura 8, caja negra** (`CajaNegra.drawio.pdf`): las entradas son 23 respuestas (4 notas, 18 ítems de 1 a 5 y el
  estilo de 1 a 5), no porcentajes.
- **Figuras 9 y 10, DFD**: el proceso de derivación produce hechos con su grado, y aparece el almacén
  `hechos_aspirante`.
