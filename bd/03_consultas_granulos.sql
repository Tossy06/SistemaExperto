-- =====================================================================
--  Consultas de los gránulos de conocimiento por hipótesis
-- =====================================================================
CREATE OR REPLACE VIEW conocimiento.vw_granulos_por_hipotesis AS
SELECT h.codigo            AS hipotesis,
       h.programa_academico,
       g.codigo_regla      AS regla,
       v.nombre            AS variable,
       he.valor_clasificado AS valor_hecho,
       g.peso
FROM conocimiento.granulos_hecho_hipotesis g
JOIN conocimiento.hipotesis_programas h            ON h.id_hipotesis = g.id_hipotesis
JOIN conocimiento.hechos_perfil he              ON he.id_hecho    = g.id_hecho
JOIN conocimiento.variables_perfil v ON v.id_variable  = he.id_variable
WHERE g.activo AND h.activa;

-- C1. Gránulos de una hipótesis (ejemplo: H01 Ingeniería de Software)
SELECT regla, variable, valor_hecho, peso
FROM conocimiento.vw_granulos_por_hipotesis
WHERE hipotesis = 'H01'
ORDER BY regla;

-- C2. Resumen de gránulos por hipótesis (las 24 hipótesis), agrupados por variable.
--     Peso máximo alcanzable: por cada variable cuenta solo el gránulo de mayor peso (el perfil tiene un hecho por variable).
SELECT hipotesis, programa_academico,
       SUM(numero)     AS numero_granulos,
       SUM(peso_mayor) AS peso_maximo,
       STRING_AGG(variable || ' (' || valores || ')', '; ' ORDER BY primera_regla) AS hechos
FROM (SELECT hipotesis, programa_academico, variable, COUNT(*) AS numero, MAX(peso) AS peso_mayor,
             MIN(regla) AS primera_regla, STRING_AGG(valor_hecho || ' ' || peso, ', ' ORDER BY regla) AS valores
      FROM conocimiento.vw_granulos_por_hipotesis
      GROUP BY hipotesis, programa_academico, variable) por_variable
GROUP BY hipotesis, programa_academico
ORDER BY hipotesis;

-- C3. Consulta granular que ejecuta el motor de inferencia por cada hecho
--     (ejemplo: hecho DES-LM-ALT = «Desempeño Lógico-Matemática = Alto»)
SELECT h.codigo AS hipotesis, h.programa_academico, g.peso
FROM conocimiento.granulos_hecho_hipotesis g
JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = g.id_hipotesis
WHERE g.id_hecho = (SELECT id_hecho FROM conocimiento.hechos_perfil WHERE codigo = 'DES-LM-ALT')
  AND g.activo AND h.activa
ORDER BY h.codigo;

-- C4. Rangos de clasificación de hechos (reglas RC) almacenados como datos.
--     criterio RANGO: el rango se compara con el promedio; POSICION: con el lugar frente a las variables del mismo tipo.
SELECT he.codigo, v.nombre AS variable, v.criterio_clasificacion, he.valor_clasificado, he.rango_minimo, he.rango_maximo
FROM conocimiento.hechos_perfil he
JOIN conocimiento.variables_perfil v ON v.id_variable = he.id_variable
ORDER BY v.id_variable, he.rango_minimo;

-- C5. Preguntas que mide cada variable del perfil (las de interés tienen tres ítems RIASEC)
SELECT v.codigo AS variable, v.nombre, COUNT(p.id_pregunta) AS preguntas,
       STRING_AGG(p.codigo, ', ' ORDER BY p.orden) AS codigos
FROM conocimiento.variables_perfil v
JOIN conocimiento.preguntas_cuestionario_vocacional p ON p.id_variable = v.id_variable
GROUP BY v.id_variable, v.codigo, v.nombre ORDER BY v.id_variable;

-- C6. Hechos, aportes y grado de coincidencia de una evaluación registrada (ejemplo: evaluación 1)
SELECT h.codigo AS hipotesis, h.programa_academico, g.codigo_regla, he.codigo AS hecho, g.peso, ha.grado,
       ROUND(g.peso * ha.grado, 4) AS aporte
FROM transaccional.hechos_aspirante ha
JOIN conocimiento.granulos_hecho_hipotesis g ON g.id_hecho = ha.id_hecho AND g.activo
JOIN conocimiento.hipotesis_programas h ON h.id_hipotesis = g.id_hipotesis
JOIN conocimiento.hechos_perfil he ON he.id_hecho = ha.id_hecho
WHERE ha.id_evaluacion = 1
ORDER BY h.codigo, aporte DESC;
