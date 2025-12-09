-- ================================================================================
-- DATOS INICIALES: Sistema de Gestión de Sustancias Controladas
-- Ejecutar DESPUÉS de crear el esquema (schema.sql)
-- ================================================================================

------------------------------------------------------------
-- INSERTAR ROLES DEL SISTEMA
------------------------------------------------------------

INSERT INTO roles (codigo, nombre) VALUES
('USUARIO', 'Usuario/Solicitante'),
('VUS', 'Ventanilla Única de Servicios'),
('TECNICO_UPC', 'Técnico de Productos Controlados'),
('ENCARGADO_UPC', 'Encargado de Unidad UPC'),
('DIRECCION', 'Dirección/Management'),
('DNCD', 'DNCD - Verificación Externa'),
('ADMIN', 'Administrador del Sistema');

------------------------------------------------------------
-- INSERTAR ESTADOS DE SOLICITUD
------------------------------------------------------------

INSERT INTO estados_solicitud (codigo, descripcion) VALUES
('PENDIENTE_PAGO', 'Usuario debe pagar'),
('EN_REVISION_VUS', 'Ventanilla Única revisa cumplimiento formal'),
('DEVUELTO_VUS', 'No cumple requisitos iniciales'),
('EN_EVALUACION_UPC', 'Técnico UPC evalúa'),
('DEVUELTO_UPC', 'Técnico devuelve para correcciones'),
('RECHAZADO_UPC', 'Técnico rechaza - necesita firma Dirección'),
('PENDIENTE_FIRMA_RECHAZO', 'Esperando firma de comunicación de rechazo'),
('RECHAZADO_FINAL', 'Rechazo firmado por Dirección'),
('APROBADO_UPC', 'Aprobado por técnico'),
('PENDIENTE_FIRMA_DIRECCION', 'Esperando firma Dirección'),
('FIRMADO_DIRECCION', 'Firmado por Dirección'),
('EN_DNCD', 'Enviado a DNCD para verificación'),
('APROBADO_DNCD', 'DNCD aprueba y firma'),
('LISTO_RETIRO', 'Usuario puede retirar certificado'),
('ENTREGADO', 'Certificado entregado'),
('CANCELADO', 'Solicitud cancelada');

------------------------------------------------------------
-- INSERTAR CATÁLOGO DE SERVICIOS
------------------------------------------------------------

INSERT INTO catalogo_servicios (codigo, nombre, descripcion, costo, tiempo_estimado_dias, activo, requiere_dncd) VALUES
(
  'CLASE_A',
  'Certificado de Inscripción de Drogas Controladas Clase A',
  'Certificado para manejo de drogas controladas clase A según Ley 50-88',
  1000.00,
  15,
  true,
  true
),
(
  'CLASE_B_PRIVADO',
  'Certificado de Inscripción Clase B - Establecimientos Privados',
  'Certificado para establecimientos de salud privados',
  800.00,
  10,
  true,
  false
),
(
  'CLASE_B_PUBLICO',
  'Certificado de Inscripción Clase B - Hospitales Públicos',
  'Certificado para hospitales públicos',
  500.00,
  10,
  true,
  false
),
(
  'IMPORTACION_MATERIA_PRIMA',
  'Permiso de Importación de Materia Prima',
  'Permiso para importación de materias primas controladas',
  1500.00,
  20,
  true,
  true
),
(
  'IMPORTACION_MEDICAMENTOS',
  'Permiso de Importación de Medicamentos',
  'Permiso para importación de medicamentos controlados',
  1200.00,
  15,
  true,
  true
);

------------------------------------------------------------
-- INSERTAR USUARIOS DE PRUEBA
-- NOTA: Contraseñas hasheadas con bcrypt
-- Contraseña para todos: "password123"
-- Hash bcrypt: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC
------------------------------------------------------------

-- Usuario Admin
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, activo) VALUES
('Admin Sistema', 'admin@msp.gob.do', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'ADMIN', 'STAFF', true);

-- Usuario VUS
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, activo) VALUES
('Usuario VUS', 'vus@msp.gob.do', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'VUS', 'STAFF', true);

-- Técnico UPC
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, activo) VALUES
('Técnico UPC', 'tecnico@msp.gob.do', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'TECNICO_UPC', 'STAFF', true);

-- Encargado UPC
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, activo) VALUES
('Encargado UPC', 'encargado@msp.gob.do', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'ENCARGADO_UPC', 'STAFF', true);

-- Dirección
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, activo) VALUES
('Director MSP', 'direccion@msp.gob.do', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'DIRECCION', 'STAFF', true);

-- Usuario DNCD
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, activo) VALUES
('Usuario DNCD', 'usuario@dncd.gob.do', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'DNCD', 'STAFF', true);

-- Usuario Regular (Profesional)
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, documento_identidad, activo) VALUES
('Juan Pérez', 'juan.perez@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'USUARIO', 'PROFESIONAL', '001-0000000-0', true);

-- Usuario Empresarial
INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, razon_social, rnc, representante_legal, activo) VALUES
('María García', 'maria.garcia@empresa.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC', 'USUARIO', 'EMPRESARIAL', 'Farmacia Central SRL', '131-00000-0', 'María García', true);

------------------------------------------------------------
-- INSERTAR REQUISITOS POR SERVICIO (Ejemplos)
------------------------------------------------------------

-- Requisitos para CLASE_A
INSERT INTO requisitos_por_servicio (servicio_id, nombre, descripcion, obligatorio, tipo_documento, orden)
SELECT 
  id,
  'Copia de Cédula',
  'Copia de cédula de identidad del solicitante',
  true,
  'pdf',
  1
FROM catalogo_servicios WHERE codigo = 'CLASE_A';

INSERT INTO requisitos_por_servicio (servicio_id, nombre, descripcion, obligatorio, tipo_documento, orden)
SELECT 
  id,
  'Título Profesional',
  'Copia del título profesional del responsable técnico',
  true,
  'pdf',
  2
FROM catalogo_servicios WHERE codigo = 'CLASE_A';

INSERT INTO requisitos_por_servicio (servicio_id, nombre, descripcion, obligatorio, tipo_documento, orden)
SELECT 
  id,
  'Registro Mercantil',
  'Copia del registro mercantil de la empresa',
  true,
  'pdf',
  3
FROM catalogo_servicios WHERE codigo = 'CLASE_A';

-- Requisitos para CLASE_B_PRIVADO
INSERT INTO requisitos_por_servicio (servicio_id, nombre, descripcion, obligatorio, tipo_documento, orden)
SELECT 
  id,
  'Licencia Sanitaria',
  'Copia de la licencia sanitaria del establecimiento',
  true,
  'pdf',
  1
FROM catalogo_servicios WHERE codigo = 'CLASE_B_PRIVADO';

INSERT INTO requisitos_por_servicio (servicio_id, nombre, descripcion, obligatorio, tipo_documento, orden)
SELECT 
  id,
  'Plano de Instalaciones',
  'Plano arquitectónico de las instalaciones',
  true,
  'pdf',
  2
FROM catalogo_servicios WHERE codigo = 'CLASE_B_PRIVADO';

------------------------------------------------------------
-- CONFIGURACIÓN DEL SISTEMA
------------------------------------------------------------

INSERT INTO configuracion_sistema (clave, valor) VALUES
('extensiones_permitidas', '["pdf", "jpg", "jpeg", "png", "doc", "docx"]'::jsonb),
('tamano_maximo_archivo_mb', '16'::jsonb),
('dias_alerta_vencimiento', '[30, 15, 7, 1]'::jsonb),
('email_notificaciones', '"notificaciones@msp.gob.do"'::jsonb),
('tiempo_sesion_minutos', '120'::jsonb);

------------------------------------------------------------
-- CREAR VISTA PARA ESTADÍSTICAS
------------------------------------------------------------

CREATE OR REPLACE VIEW vista_estadisticas_solicitudes AS
SELECT 
  estado_codigo,
  es.descripcion as estado_descripcion,
  COUNT(*) as total_solicitudes,
  COUNT(CASE WHEN s.pagado = true THEN 1 END) as solicitudes_pagadas,
  AVG(EXTRACT(DAY FROM (s.fecha_actualizacion - s.fecha_creacion))) as dias_promedio_proceso
FROM solicitudes s
JOIN estados_solicitud es ON s.estado_codigo = es.codigo
GROUP BY estado_codigo, es.descripcion;

CREATE OR REPLACE VIEW vista_usuarios_activos AS
SELECT 
  r.codigo as rol_codigo,
  r.nombre as rol_nombre,
  COUNT(*) as total_usuarios,
  COUNT(CASE WHEN u.activo = true THEN 1 END) as usuarios_activos
FROM usuarios u
JOIN roles r ON u.rol_codigo = r.codigo
GROUP BY r.codigo, r.nombre;

------------------------------------------------------------
-- FUNCIONES ÚTILES
------------------------------------------------------------

-- Función para generar número de expediente
CREATE OR REPLACE FUNCTION generar_numero_expediente()
RETURNS VARCHAR AS $$
DECLARE
  year_actual INTEGER;
  correlativo INTEGER;
  numero VARCHAR;
BEGIN
  year_actual := EXTRACT(YEAR FROM CURRENT_DATE);
  
  SELECT COALESCE(MAX(CAST(SUBSTRING(numero_expediente FROM 9) AS INTEGER)), 0) + 1
  INTO correlativo
  FROM solicitudes
  WHERE numero_expediente LIKE 'EXP-' || year_actual || '-%';
  
  numero := 'EXP-' || year_actual || '-' || LPAD(correlativo::TEXT, 5, '0');
  RETURN numero;
END;
$$ LANGUAGE plpgsql;

-- Función para verificar certificados próximos a vencer
CREATE OR REPLACE FUNCTION certificados_proximos_vencer(dias_antelacion INTEGER DEFAULT 30)
RETURNS TABLE (
  certificado_id UUID,
  numero_certificado VARCHAR,
  usuario_email VARCHAR,
  dias_restantes INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    c.id,
    c.numero_certificado,
    u.email,
    EXTRACT(DAY FROM (c.fecha_vencimiento - CURRENT_DATE))::INTEGER as dias_restantes
  FROM certificados c
  JOIN solicitudes s ON c.solicitud_id = s.id
  JOIN usuarios u ON s.usuario_id = u.id
  WHERE c.estado = 'VIGENTE'
    AND c.fecha_vencimiento BETWEEN CURRENT_DATE AND CURRENT_DATE + (dias_antelacion || ' days')::INTERVAL
  ORDER BY c.fecha_vencimiento;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================
-- VERIFICAR DATOS INSERTADOS
-- ================================================================================

SELECT 'Roles creados: ' || COUNT(*)::TEXT FROM roles;
SELECT 'Estados creados: ' || COUNT(*)::TEXT FROM estados_solicitud;
SELECT 'Servicios creados: ' || COUNT(*)::TEXT FROM catalogo_servicios;
SELECT 'Usuarios creados: ' || COUNT(*)::TEXT FROM usuarios;
SELECT 'Requisitos creados: ' || COUNT(*)::TEXT FROM requisitos_por_servicio;

-- ================================================================================
-- CREDENCIALES DE PRUEBA
-- ================================================================================

/*
USUARIOS DE PRUEBA - Contraseña para todos: "password123"

Admin:         admin@msp.gob.do
VUS:           vus@msp.gob.do
Técnico UPC:   tecnico@msp.gob.do
Encargado UPC: encargado@msp.gob.do
Dirección:     direccion@msp.gob.do
DNCD:          usuario@dncd.gob.do
Usuario:       juan.perez@example.com
Empresa:       maria.garcia@empresa.com
*/

-- ================================================================================
-- FIN DE DATOS INICIALES
-- ================================================================================
