-- =====================================================================
--  Sistema Experto de Apoyo a la Orientación Académica
--  Base de datos única (PostgreSQL 16): conocimiento + transaccional
--  Ambos esquemas se unen por la tabla conocimiento.hipotesis_programas
-- =====================================================================
DROP SCHEMA IF EXISTS transaccional CASCADE;
DROP SCHEMA IF EXISTS conocimiento CASCADE;
CREATE SCHEMA conocimiento;
CREATE SCHEMA transaccional;

-- ---------------------------------------------------------------------
--  ESQUEMA conocimiento  (base de conocimiento del sistema experto)
-- ---------------------------------------------------------------------
CREATE TABLE conocimiento.ingenieros_conocimiento (
    id_ingeniero        SERIAL PRIMARY KEY,
    documento           VARCHAR(20)  NOT NULL UNIQUE,
    nombres             VARCHAR(80)  NOT NULL,
    apellidos           VARCHAR(80)  NOT NULL,
    correo              VARCHAR(120) NOT NULL UNIQUE,
    contrasena_hash     VARCHAR(255) NOT NULL,
    fecha_registro      TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE TABLE conocimiento.hipotesis_programas (
    id_hipotesis        SERIAL PRIMARY KEY,
    codigo              VARCHAR(5)   NOT NULL UNIQUE,          -- H01 ... H24
    programa_academico  VARCHAR(100) NOT NULL UNIQUE,
    descripcion         VARCHAR(300),
    activa              BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE conocimiento.variables_perfil (
    id_variable         SERIAL PRIMARY KEY,
    codigo              VARCHAR(10)  NOT NULL UNIQUE,          -- DES-LM, INT-I, EST
    nombre              VARCHAR(80)  NOT NULL UNIQUE,          -- Desempeño Lógico-Matemática
    tipo_variable       VARCHAR(10)  NOT NULL CHECK (tipo_variable IN ('AREA','INTERES','ESTILO')),
    tipo_respuesta      VARCHAR(10)  NOT NULL CHECK (tipo_respuesta IN ('NUMERICA','OPCION'))
);

CREATE TABLE conocimiento.preguntas_cuestionario_vocacional (
    id_pregunta         SERIAL PRIMARY KEY,
    id_variable         INT          NOT NULL UNIQUE REFERENCES conocimiento.variables_perfil(id_variable),
    enunciado           VARCHAR(300) NOT NULL,
    valor_minimo        NUMERIC(5,2),
    valor_maximo        NUMERIC(5,2),
    orden               SMALLINT     NOT NULL UNIQUE,
    activa              BOOLEAN      NOT NULL DEFAULT TRUE
);

-- Un hecho es (variable, valor). Para variables numéricas guarda el rango de clasificación (reglas RC).
CREATE TABLE conocimiento.hechos_perfil (
    id_hecho            SERIAL PRIMARY KEY,
    codigo              VARCHAR(12)  NOT NULL UNIQUE,          -- DES-LM-ALT
    id_variable         INT          NOT NULL REFERENCES conocimiento.variables_perfil(id_variable),
    valor_clasificado   VARCHAR(20)  NOT NULL,                 -- Alto, Medio, Bajo, Independiente, Equipo
    rango_minimo        NUMERIC(6,2),
    rango_maximo        NUMERIC(6,2),
    UNIQUE (id_variable, valor_clasificado),
    CHECK ((rango_minimo IS NULL AND rango_maximo IS NULL) OR rango_minimo <= rango_maximo)
);

-- Gránulo de conocimiento (reglas RG): un hecho -> una hipótesis con un peso
CREATE TABLE conocimiento.granulos_hecho_hipotesis (
    id_granulo          SERIAL PRIMARY KEY,
    codigo_regla        VARCHAR(6)   NOT NULL UNIQUE,          -- RG-01 ... RG-72
    id_hecho            INT          NOT NULL REFERENCES conocimiento.hechos_perfil(id_hecho),
    id_hipotesis        INT          NOT NULL REFERENCES conocimiento.hipotesis_programas(id_hipotesis),
    peso                NUMERIC(3,2) NOT NULL CHECK (peso >= 0.00 AND peso <= 1.00),
    activo              BOOLEAN      NOT NULL DEFAULT TRUE,
    id_ingeniero        INT          REFERENCES conocimiento.ingenieros_conocimiento(id_ingeniero),
    fecha_modificacion  TIMESTAMP    NOT NULL DEFAULT now(),
    UNIQUE (id_hecho, id_hipotesis)
);

-- Reglas de resultado no concluyente (RN): SI cantidad de hechos (tipo_variable, valor) <operador> cantidad ENTONCES marcar
CREATE TABLE conocimiento.reglas_resultado_no_concluyente (
    id_regla_resultado_no_concluyente SERIAL PRIMARY KEY,
    codigo_regla        VARCHAR(6)   NOT NULL UNIQUE,          -- RN-01 ... RN-03
    descripcion         VARCHAR(200) NOT NULL,
    tipo_variable       VARCHAR(10)  NOT NULL CHECK (tipo_variable IN ('AREA','INTERES','ESTILO')),
    valor_hecho         VARCHAR(20)  NOT NULL,
    operador            VARCHAR(2)   NOT NULL CHECK (operador IN ('=','>=')),
    cantidad            SMALLINT     NOT NULL CHECK (cantidad > 0),
    activa              BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
--  ESQUEMA transaccional  (operación del sistema)
-- ---------------------------------------------------------------------
CREATE TABLE transaccional.aspirantes (
    id_aspirante        SERIAL PRIMARY KEY,
    documento           VARCHAR(20)  NOT NULL UNIQUE,
    nombres             VARCHAR(80)  NOT NULL,
    apellidos           VARCHAR(80)  NOT NULL,
    correo              VARCHAR(120) NOT NULL UNIQUE,
    contrasena_hash     VARCHAR(255) NOT NULL,
    fecha_registro      TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE TABLE transaccional.evaluaciones_vocacionales (
    id_evaluacion       SERIAL PRIMARY KEY,
    id_aspirante        INT          NOT NULL REFERENCES transaccional.aspirantes(id_aspirante),
    fecha_evaluacion    TIMESTAMP    NOT NULL DEFAULT now(),
    resultado_no_concluyente BOOLEAN NOT NULL DEFAULT FALSE
);

-- Respuesta del aspirante y hecho derivado (RF-02)
CREATE TABLE transaccional.respuestas_aspirante (
    id_respuesta        SERIAL PRIMARY KEY,
    id_evaluacion       INT          NOT NULL REFERENCES transaccional.evaluaciones_vocacionales(id_evaluacion),
    id_pregunta         INT          NOT NULL REFERENCES conocimiento.preguntas_cuestionario_vocacional(id_pregunta),
    valor_numerico      NUMERIC(6,2),
    valor_opcion        VARCHAR(20),
    id_hecho            INT          NOT NULL REFERENCES conocimiento.hechos_perfil(id_hecho),
    UNIQUE (id_evaluacion, id_pregunta),
    CHECK ((valor_numerico IS NULL) <> (valor_opcion IS NULL))
);

-- Tabla de contabilización de coincidencias (RF-03)
CREATE TABLE transaccional.contabilizacion_coincidencias_hipotesis (
    id_evaluacion       INT          NOT NULL REFERENCES transaccional.evaluaciones_vocacionales(id_evaluacion),
    id_hipotesis        INT          NOT NULL REFERENCES conocimiento.hipotesis_programas(id_hipotesis),
    numero_coincidencias SMALLINT    NOT NULL CHECK (numero_coincidencias > 0),
    suma_pesos          NUMERIC(6,2) NOT NULL CHECK (suma_pesos >= 0),
    probabilidad        NUMERIC(7,4) NOT NULL CHECK (probabilidad BETWEEN 0 AND 100),
    PRIMARY KEY (id_evaluacion, id_hipotesis)
);

-- Las cinco hipótesis presentadas al aspirante (RF-03)
CREATE TABLE transaccional.resultado_cinco_hipotesis (
    id_evaluacion       INT          NOT NULL REFERENCES transaccional.evaluaciones_vocacionales(id_evaluacion),
    posicion            SMALLINT     NOT NULL CHECK (posicion BETWEEN 1 AND 5),
    id_hipotesis        INT          NOT NULL REFERENCES conocimiento.hipotesis_programas(id_hipotesis),
    probabilidad        NUMERIC(7,4) NOT NULL,
    PRIMARY KEY (id_evaluacion, posicion),
    UNIQUE (id_evaluacion, id_hipotesis)
);

-- Reglas de resultado no concluyente que se cumplieron en una evaluación
CREATE TABLE transaccional.marcas_resultado_no_concluyente (
    id_evaluacion       INT          NOT NULL REFERENCES transaccional.evaluaciones_vocacionales(id_evaluacion),
    id_regla_resultado_no_concluyente INT      NOT NULL REFERENCES conocimiento.reglas_resultado_no_concluyente(id_regla_resultado_no_concluyente),
    PRIMARY KEY (id_evaluacion, id_regla_resultado_no_concluyente)
);

-- ---------------------------------------------------------------------
--  Inmutabilidad de las evaluaciones (RNF-04)
-- ---------------------------------------------------------------------
CREATE FUNCTION transaccional.impedir_cambios() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Las evaluaciones registradas no se modifican ni se eliminan (RNF-04)';
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_evaluaciones_inmutables BEFORE UPDATE OR DELETE ON transaccional.evaluaciones_vocacionales
    FOR EACH ROW EXECUTE FUNCTION transaccional.impedir_cambios();
CREATE TRIGGER trg_respuestas_inmutables BEFORE UPDATE OR DELETE ON transaccional.respuestas_aspirante
    FOR EACH ROW EXECUTE FUNCTION transaccional.impedir_cambios();
CREATE TRIGGER trg_contabilizacion_inmutable BEFORE UPDATE OR DELETE ON transaccional.contabilizacion_coincidencias_hipotesis
    FOR EACH ROW EXECUTE FUNCTION transaccional.impedir_cambios();
CREATE TRIGGER trg_resultado_inmutable BEFORE UPDATE OR DELETE ON transaccional.resultado_cinco_hipotesis
    FOR EACH ROW EXECUTE FUNCTION transaccional.impedir_cambios();
CREATE TRIGGER trg_marcas_inmutables BEFORE UPDATE OR DELETE ON transaccional.marcas_resultado_no_concluyente
    FOR EACH ROW EXECUTE FUNCTION transaccional.impedir_cambios();

-- Índice para la consulta granular por hecho (RNF-03)
CREATE INDEX idx_granulos_hecho_hipotesis ON conocimiento.granulos_hecho_hipotesis (id_hecho) WHERE activo;
