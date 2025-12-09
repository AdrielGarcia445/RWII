-- ================================================================================
-- ESQUEMA DE BASE DE DATOS: Sistema de Gestión de Sustancias Controladas
-- Ministerio de Salud Pública y DNCD
-- ================================================================================

-- Habilitar extensión para gen_random_uuid (PostgreSQL)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- OPCIONAL: borrar tablas si ya existen (para recrear el esquema completo)
DROP TABLE IF EXISTS
  auditoria,
  notificaciones,
  historial_estados_solicitud,
  observaciones_solicitud,
  evaluaciones_tecnicas_upc,
  documentos,
  solicitudes,
  certificados,
  requisitos_por_servicio,
  configuracion_sistema,
  usuarios,
  catalogo_servicios,
  estados_solicitud,
  roles
CASCADE;

------------------------------------------------------------
-- TABLAS BASE
------------------------------------------------------------

CREATE TABLE roles (
  id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo  varchar UNIQUE NOT NULL,
  nombre  varchar NOT NULL
);

CREATE TABLE estados_solicitud (
  codigo       varchar PRIMARY KEY,
  descripcion  varchar NOT NULL
);

CREATE TABLE catalogo_servicios (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo               varchar UNIQUE NOT NULL,
  nombre               varchar NOT NULL,
  descripcion          text,
  costo                numeric(12, 2),
  tiempo_estimado_dias int,
  activo               boolean DEFAULT true,
  requiere_dncd        boolean DEFAULT false
);

CREATE TABLE usuarios (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                 varchar NOT NULL,
  email                varchar UNIQUE NOT NULL,
  password_hash        varchar NOT NULL,
  rol_codigo           varchar NOT NULL REFERENCES roles (codigo),
  tipo_usuario         varchar NOT NULL,
  documento_identidad  varchar,
  telefono             varchar,
  direccion            varchar,
  razon_social         varchar,
  rnc                  varchar,
  representante_legal  varchar,
  activo               boolean DEFAULT true,
  fecha_registro       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE configuracion_sistema (
  clave varchar PRIMARY KEY,
  valor jsonb NOT NULL
);

------------------------------------------------------------
-- SERVICIOS Y REQUISITOS
------------------------------------------------------------

CREATE TABLE requisitos_por_servicio (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  servicio_id   uuid NOT NULL REFERENCES catalogo_servicios (id),
  nombre        varchar NOT NULL,
  descripcion   text,
  obligatorio   boolean,
  tipo_documento varchar,
  orden         int
);

------------------------------------------------------------
-- CERTIFICADOS
------------------------------------------------------------

CREATE TABLE certificados (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  solicitud_id              uuid,
  numero_certificado        varchar UNIQUE NOT NULL,
  tipo_servicio_codigo      varchar NOT NULL REFERENCES catalogo_servicios (codigo),
  nombre_archivo            varchar NOT NULL,
  ruta                      varchar NOT NULL,
  fecha_emision             timestamptz NOT NULL DEFAULT now(),
  fecha_vencimiento         timestamptz NOT NULL,
  firmante_direccion_id     uuid NOT NULL REFERENCES usuarios (id),
  firma_digital_direccion   text NOT NULL,
  firmante_dncd_id          uuid REFERENCES usuarios (id),
  firma_digital_dncd        text,
  fecha_firma_dncd          timestamptz,
  estado                    varchar NOT NULL
);

------------------------------------------------------------
-- SOLICITUDES
------------------------------------------------------------

CREATE TABLE solicitudes (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  numero_expediente       varchar UNIQUE NOT NULL,
  usuario_id              uuid NOT NULL REFERENCES usuarios (id),
  servicio_id             uuid NOT NULL REFERENCES catalogo_servicios (id),
  estado_codigo           varchar NOT NULL REFERENCES estados_solicitud (codigo),
  fecha_creacion          timestamptz NOT NULL DEFAULT now(),
  fecha_actualizacion     timestamptz NOT NULL DEFAULT now(),
  pagado                  boolean DEFAULT false,
  monto_pagado            numeric(12, 2) DEFAULT 0,
  metodo_pago             varchar,
  referencia_pago         varchar,
  asignado_a_id           uuid REFERENCES usuarios (id),
  fecha_asignacion_upc    timestamptz,
  fecha_reasignacion      timestamptz,
  fecha_entrega           timestamptz,
  tipo_entrega            varchar,
  receptor_certificado    varchar,
  fecha_aprobacion        timestamptz,
  fecha_recepcion_dncd    timestamptz,
  fecha_aprobacion_dncd   timestamptz,
  fecha_resubmision       timestamptz,
  fecha_rechazo           timestamptz,
  datos_formulario        jsonb,
  certificado_id          uuid REFERENCES certificados (id)
);

------------------------------------------------------------
-- DOCUMENTOS
------------------------------------------------------------

CREATE TABLE documentos (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  solicitud_id     uuid REFERENCES solicitudes (id) ON DELETE CASCADE,
  certificado_id   uuid REFERENCES certificados (id),
  origen           varchar NOT NULL,
  tipo             varchar NOT NULL,
  nombre_original  varchar,
  nombre_storage   varchar NOT NULL,
  ruta             varchar NOT NULL,
  fecha_subida     timestamptz NOT NULL DEFAULT now(),
  firmante_id      uuid REFERENCES usuarios (id),
  firma_digital    text
);

------------------------------------------------------------
-- EVALUACIONES TÉCNICAS
------------------------------------------------------------

CREATE TABLE evaluaciones_tecnicas_upc (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  solicitud_id  uuid NOT NULL REFERENCES solicitudes (id),
  tecnico_id    uuid NOT NULL REFERENCES usuarios (id),
  aprobado      boolean,
  checklist     jsonb,
  observaciones text,
  fecha         timestamptz NOT NULL DEFAULT now()
);

------------------------------------------------------------
-- OBSERVACIONES Y HISTORIAL
------------------------------------------------------------

CREATE TABLE observaciones_solicitud (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  solicitud_id uuid NOT NULL REFERENCES solicitudes (id),
  fecha       timestamptz NOT NULL DEFAULT now(),
  usuario_id  uuid NOT NULL REFERENCES usuarios (id),
  rol_codigo  varchar NOT NULL REFERENCES roles (codigo),
  tipo        varchar NOT NULL,
  texto       text,
  checklist   jsonb
);

CREATE TABLE historial_estados_solicitud (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  solicitud_id  uuid NOT NULL REFERENCES solicitudes (id),
  estado_codigo varchar NOT NULL REFERENCES estados_solicitud (codigo),
  usuario_id    uuid REFERENCES usuarios (id),
  fecha         timestamptz NOT NULL DEFAULT now(),
  comentario    text
);

------------------------------------------------------------
-- NOTIFICACIONES Y AUDITORÍA
------------------------------------------------------------

CREATE TABLE notificaciones (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id     uuid NOT NULL REFERENCES usuarios (id),
  solicitud_id   uuid REFERENCES solicitudes (id),
  tipo           varchar NOT NULL,
  mensaje        text NOT NULL,
  fecha          timestamptz NOT NULL DEFAULT now(),
  leida          boolean DEFAULT false,
  fecha_lectura  timestamptz
);

CREATE TABLE auditoria (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  solicitud_id uuid REFERENCES solicitudes (id),
  usuario_id  uuid REFERENCES usuarios (id),
  accion      varchar NOT NULL,
  detalles    text,
  "timestamp" timestamptz NOT NULL DEFAULT now()
);

------------------------------------------------------------
-- ÍNDICES
------------------------------------------------------------

CREATE INDEX idx_solicitudes_estado_servicio
  ON solicitudes USING btree (estado_codigo, servicio_id);

CREATE INDEX idx_solicitudes_usuario
  ON solicitudes USING btree (usuario_id);

CREATE INDEX idx_solicitudes_fecha_creacion
  ON solicitudes USING btree (fecha_creacion);

CREATE INDEX idx_certificados_estado_vencimiento
  ON certificados USING btree (estado, fecha_vencimiento);

CREATE INDEX idx_notificaciones_usuario_leida
  ON notificaciones USING btree (usuario_id, leida);

CREATE INDEX idx_auditoria_timestamp
  ON auditoria USING btree ("timestamp");

CREATE INDEX idx_auditoria_solicitud
  ON auditoria USING btree (solicitud_id);

------------------------------------------------------------
-- COMENTARIOS EN TABLAS
------------------------------------------------------------

COMMENT ON TABLE roles IS 'Roles del sistema (USUARIO, VUS, TECNICO_UPC, DIRECCION, DNCD, ADMIN)';
COMMENT ON TABLE estados_solicitud IS 'Estados posibles del flujo de trabajo de solicitudes';
COMMENT ON TABLE catalogo_servicios IS 'Catálogo administrable de servicios disponibles';
COMMENT ON TABLE usuarios IS 'Usuarios del sistema (profesionales, empresariales y staff)';
COMMENT ON TABLE solicitudes IS 'Solicitudes de certificados y permisos';
COMMENT ON TABLE documentos IS 'Documentos adjuntos a solicitudes y certificados';
COMMENT ON TABLE certificados IS 'Certificados y permisos emitidos con firmas digitales';
COMMENT ON TABLE auditoria IS 'Registro completo de auditoría del sistema';
COMMENT ON TABLE notificaciones IS 'Notificaciones enviadas a usuarios';

-- ================================================================================
-- FIN DEL ESQUEMA
-- ================================================================================
