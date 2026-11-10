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

-- C2. Resumen de gránulos por hipótesis (las 24 hipótesis)
SELECT hipotesis, programa_academico,
       COUNT(*)               AS numero_granulos,
       SUM(peso)              AS peso_maximo,
       STRING_AGG(variable || ' = ' || valor_hecho, '; ' ORDER BY regla) AS hechos
FROM conocimiento.vw_granulos_por_hipotesis
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

-- C4. Rangos de clasificación de hechos (reglas RC) almacenados como datos
SELECT he.codigo, v.nombre AS variable, he.valor_clasificado, he.rango_minimo, he.rango_maximo
FROM conocimiento.hechos_perfil he
JOIN conocimiento.variables_perfil v ON v.id_variable = he.id_variable
ORDER BY v.id_variable, he.rango_minimo DESC NULLS LAST;
