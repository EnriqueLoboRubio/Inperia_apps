CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    contrasena TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('profesional', 'interno', 'administrador'))
);

CREATE TABLE IF NOT EXISTS preguntas (
    id INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    texto TEXT NOT NULL,
    cantidad_niveles INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pregunta INTEGER NOT NULL REFERENCES preguntas(id) ON DELETE RESTRICT,
    titulo TEXT NOT NULL,
    plantilla TEXT NOT NULL,
    descripcion TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    activo SMALLINT NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_pregunta, version)
);

CREATE TABLE IF NOT EXISTS internos (
    num_rc INTEGER PRIMARY KEY,
    id_usuario INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    situacion_legal TEXT CHECK (situacion_legal IN ('provisional', 'condenado', 'libertad_condicional')),
    delito TEXT,
    condena DOUBLE PRECISION,
    fecha_nac DATE NOT NULL,
    fecha_ingreso DATE,
    modulo TEXT,
    lugar_nacimiento TEXT,
    nombre_contacto_emergencia TEXT,
    relacion_contacto_emergencia TEXT,
    numero_contacto_emergencia TEXT
);

CREATE TABLE IF NOT EXISTS profesionales (
    id_usuario INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    num_colegiado TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_interno INTEGER NOT NULL REFERENCES internos(num_rc) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('familiar', 'medico', 'educativo', 'laboral', 'defuncion', 'juridico')),
    motivo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    urgencia TEXT NOT NULL CHECK (urgencia IN ('normal', 'importante', 'urgente')),
    fecha_creacion DATE NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    hora_salida TIME NOT NULL,
    hora_llegada TIME NOT NULL,
    destino TEXT NOT NULL,
    provincia TEXT NOT NULL,
    direccion TEXT NOT NULL,
    cod_pos TEXT NOT NULL,
    nombre_cp TEXT NOT NULL,
    telf_cp TEXT NOT NULL,
    relacion_cp TEXT NOT NULL,
    direccion_cp TEXT NOT NULL,
    nombre_cs TEXT NOT NULL,
    telf_cs TEXT NOT NULL,
    relacion_cs TEXT NOT NULL,
    docs INTEGER NOT NULL,
    compromiso INTEGER NOT NULL,
    observaciones TEXT NOT NULL,
    conclusiones_profesional TEXT,
    id_profesional INTEGER REFERENCES profesionales(id_usuario) ON DELETE SET NULL,
    estado TEXT NOT NULL CHECK (estado IN ('iniciada', 'pendiente', 'aceptada', 'rechazada', 'cancelada'))
);

CREATE TABLE IF NOT EXISTS entrevistas (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_interno INTEGER NOT NULL REFERENCES internos(num_rc) ON DELETE CASCADE,
    id_solicitud INTEGER NOT NULL REFERENCES solicitudes(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    puntuacion_ia DOUBLE PRECISION,
    puntuacion_profesional DOUBLE PRECISION,
    estado_evaluacion_ia TEXT NOT NULL DEFAULT 'sin evaluación'
        CHECK (estado_evaluacion_ia IN ('sin evaluación', 'evaluando', 'evaluada'))
);

CREATE TABLE IF NOT EXISTS respuestas (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_entrevista INTEGER NOT NULL REFERENCES entrevistas(id) ON DELETE CASCADE,
    id_pregunta INTEGER NOT NULL REFERENCES preguntas(id) ON DELETE RESTRICT,
    texto_respuesta TEXT,
    ruta_audio TEXT,
    nivel_ia INTEGER,
    analisis_ia TEXT,
    nivel_profesional INTEGER
);

CREATE TABLE IF NOT EXISTS comentarios_pre (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_respuesta INTEGER NOT NULL REFERENCES respuestas(id) ON DELETE CASCADE,
    id_profesional INTEGER NOT NULL REFERENCES profesionales(id_usuario) ON DELETE RESTRICT,
    comentario TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS comentarios_ia_ent (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_entrevista INTEGER NOT NULL UNIQUE REFERENCES entrevistas(id) ON DELETE CASCADE,
    comentario_ia TEXT,
    fecha_ia TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comentarios_entrevista_mensajes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_entrevista INTEGER NOT NULL REFERENCES entrevistas(id) ON DELETE CASCADE,
    id_profesional INTEGER NOT NULL REFERENCES profesionales(id_usuario) ON DELETE RESTRICT,
    comentario TEXT NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS ponderaciones_riesgo (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pregunta INTEGER NOT NULL REFERENCES preguntas(id) ON DELETE CASCADE,
    nivel INTEGER NOT NULL,
    valor DOUBLE PRECISION NOT NULL,
    UNIQUE (id_pregunta, nivel)
);

CREATE INDEX IF NOT EXISTS idx_sol_prof_estado_id ON solicitudes(id_profesional, estado, id DESC);
CREATE INDEX IF NOT EXISTS idx_sol_prof_id ON solicitudes(id_profesional, id DESC);
CREATE INDEX IF NOT EXISTS idx_sol_interno_id ON solicitudes(id_interno, id DESC);
CREATE INDEX IF NOT EXISTS idx_sol_interno_estado ON solicitudes(id_interno, estado);
CREATE INDEX IF NOT EXISTS idx_sol_sin_prof_id ON solicitudes(id DESC) WHERE id_profesional IS NULL;

CREATE INDEX IF NOT EXISTS idx_ent_solicitud ON entrevistas(id_solicitud);
CREATE INDEX IF NOT EXISTS idx_resp_entrevista_pregunta ON respuestas(id_entrevista, id_pregunta);
CREATE INDEX IF NOT EXISTS idx_resp_entrevista ON respuestas(id_entrevista);
CREATE INDEX IF NOT EXISTS idx_coment_pre_respuesta ON comentarios_pre(id_respuesta);
CREATE INDEX IF NOT EXISTS idx_coment_ia_ent_entrevista ON comentarios_ia_ent(id_entrevista);
CREATE INDEX IF NOT EXISTS idx_coment_mensajes_entrevista ON comentarios_entrevista_mensajes(id_entrevista);
