-- ================================================================================
-- SCHEMA: Sistema de Firmas Digitales - Tipo Adobe Sign
-- Compatible con estándar de firmas electrónicas avanzadas
-- ================================================================================

-- Tabla principal: Workflows de firma
CREATE TABLE signature_workflows (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id uuid REFERENCES solicitudes(id) ON DELETE CASCADE,
    certificado_id uuid REFERENCES certificados(id) ON DELETE CASCADE,
    public_access_id varchar(20) UNIQUE NOT NULL,
    reference varchar(100),
    subject text,
    message text,
    status varchar(50) NOT NULL DEFAULT 'NOT_STARTED',
    -- Estados: NOT_STARTED, IN_PROGRESS, COMPLETED, REJECTED, EXPIRED
    creation_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    init_date timestamp,
    expiration_date timestamp,
    send_date timestamp,
    completion_date timestamp,
    sender_user_id uuid REFERENCES usuarios(id) NOT NULL,
    callback_code varchar(100),
    workflow_data jsonb,
    -- JSON completo del workflow para auditoría
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas frecuentes
CREATE INDEX idx_signature_workflows_solicitud ON signature_workflows(solicitud_id);
CREATE INDEX idx_signature_workflows_certificado ON signature_workflows(certificado_id);
CREATE INDEX idx_signature_workflows_status ON signature_workflows(status);
CREATE INDEX idx_signature_workflows_public_access ON signature_workflows(public_access_id);

-- Tabla: Líneas de destinatarios (secuencia de firmas)
CREATE TABLE signature_addressee_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES signature_workflows(id) ON DELETE CASCADE NOT NULL,
    line_number integer NOT NULL,
    -- Orden de ejecución (1, 2, 3...)
    status varchar(50) NOT NULL DEFAULT 'NEW',
    -- Estados: NEW, IN_PROGRESS, COMPLETED, REJECTED
    started_date timestamp,
    completed_date timestamp,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workflow_id, line_number)
);

CREATE INDEX idx_addressee_lines_workflow ON signature_addressee_lines(workflow_id);
CREATE INDEX idx_addressee_lines_status ON signature_addressee_lines(status);

-- Tabla: Grupos de firmantes dentro de cada línea
CREATE TABLE signature_addressee_groups (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    addressee_line_id uuid REFERENCES signature_addressee_lines(id) ON DELETE CASCADE NOT NULL,
    group_number integer NOT NULL,
    -- Orden dentro de la línea
    is_or_group boolean DEFAULT false,
    -- Si TRUE, solo uno del grupo necesita firmar
    status varchar(50) NOT NULL DEFAULT 'NEW',
    -- Estados: NEW, IN_PROGRESS, COMPLETED, REJECTED
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(addressee_line_id, group_number)
);

CREATE INDEX idx_addressee_groups_line ON signature_addressee_groups(addressee_line_id);

-- Tabla: Acciones individuales de firma/aprobación
CREATE TABLE signature_actions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    addressee_group_id uuid REFERENCES signature_addressee_groups(id) ON DELETE CASCADE NOT NULL,
    user_id uuid REFERENCES usuarios(id) NOT NULL,
    action_type varchar(50) NOT NULL,
    -- Tipos: SIGN, APPROVAL, VIEW, CERTIFY
    status varchar(50) NOT NULL DEFAULT 'NEW',
    -- Estados: NEW, SIGNED, APPROVED, REJECTED, DELEGATED
    action_date timestamp,
    reject_type varchar(100),
    -- Tipo de rechazo si aplica
    reject_reason text,
    -- Razón detallada del rechazo
    signature_data jsonb,
    -- Datos completos de la firma electrónica
    -- Estructura: {
    --   "timestamp": "ISO8601",
    --   "user_id": "uuid",
    --   "user_name": "string",
    --   "user_email": "string",
    --   "signature_type": "ELECTRONIC|ADVANCED|QUALIFIED",
    --   "certificate_hash": "SHA256",
    --   "document_hash": "SHA256",
    --   "ip_address": "xxx.xxx.xxx.xxx",
    --   "user_agent": "string",
    --   "geolocation": {"lat": 0, "lng": 0},
    --   "biometric_data": {...} (opcional)
    -- }
    notification_sent boolean DEFAULT false,
    notification_date timestamp,
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signature_actions_group ON signature_actions(addressee_group_id);
CREATE INDEX idx_signature_actions_user ON signature_actions(user_id);
CREATE INDEX idx_signature_actions_status ON signature_actions(status);

-- Tabla: Documentos asociados al workflow
CREATE TABLE signature_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES signature_workflows(id) ON DELETE CASCADE NOT NULL,
    document_type varchar(50) NOT NULL,
    -- Tipos: TO_SIGN, ANNEX, SIGNED_OUTPUT
    filename varchar(255) NOT NULL,
    public_access_id varchar(20) UNIQUE,
    storage_path varchar(500) NOT NULL,
    -- Ruta en Supabase Storage
    file_hash varchar(64) NOT NULL,
    -- SHA256 del archivo para verificación de integridad
    mime_type varchar(100),
    file_size integer,
    -- Tamaño en bytes
    version integer DEFAULT 1,
    -- Versión del documento (se incrementa con cada firma)
    is_final boolean DEFAULT false,
    -- Indica si es la versión final firmada
    created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signature_documents_workflow ON signature_documents(workflow_id);
CREATE INDEX idx_signature_documents_type ON signature_documents(document_type);
CREATE INDEX idx_signature_documents_public_access ON signature_documents(public_access_id);

-- Tabla de auditoría específica para firmas
CREATE TABLE signature_audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES signature_workflows(id) ON DELETE CASCADE,
    action_id uuid REFERENCES signature_actions(id) ON DELETE SET NULL,
    user_id uuid REFERENCES usuarios(id),
    event_type varchar(100) NOT NULL,
    -- Tipos: WORKFLOW_CREATED, SIGNATURE_REQUESTED, SIGNED, REJECTED, VIEWED, DOWNLOADED, etc.
    event_data jsonb,
    ip_address varchar(45),
    user_agent text,
    timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signature_audit_workflow ON signature_audit_log(workflow_id);
CREATE INDEX idx_signature_audit_user ON signature_audit_log(user_id);
CREATE INDEX idx_signature_audit_timestamp ON signature_audit_log(timestamp);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_signature_workflows_updated_at BEFORE UPDATE ON signature_workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signature_addressee_lines_updated_at BEFORE UPDATE ON signature_addressee_lines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signature_addressee_groups_updated_at BEFORE UPDATE ON signature_addressee_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signature_actions_updated_at BEFORE UPDATE ON signature_actions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signature_documents_updated_at BEFORE UPDATE ON signature_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentación
COMMENT ON TABLE signature_workflows IS 'Workflows de firma electrónica - Compatible con Adobe Sign API';
COMMENT ON TABLE signature_addressee_lines IS 'Líneas secuenciales de firmantes (Línea 1: Dirección, Línea 2: DNCD)';
COMMENT ON TABLE signature_addressee_groups IS 'Grupos de firmantes dentro de cada línea (permite firmas paralelas u opcionales)';
COMMENT ON TABLE signature_actions IS 'Acciones individuales de firma con datos completos para auditoría';
COMMENT ON TABLE signature_documents IS 'Documentos a firmar y documentos firmados con control de versiones';
COMMENT ON TABLE signature_audit_log IS 'Log de auditoría completo de todas las acciones del workflow';

-- ================================================================================
-- FUNCIONES AUXILIARES
-- ================================================================================

-- Función para generar public_access_id único
CREATE OR REPLACE FUNCTION generate_public_access_id(length integer DEFAULT 16)
RETURNS varchar AS $$
DECLARE
    chars varchar := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result varchar := '';
    i integer;
BEGIN
    FOR i IN 1..length LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
        IF i % 4 = 0 AND i < length THEN
            result := result || '-';
        END IF;
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Vista para consultar estado completo de workflows
CREATE OR REPLACE VIEW v_workflow_status AS
SELECT 
    w.id as workflow_id,
    w.solicitud_id,
    w.certificado_id,
    w.public_access_id,
    w.subject,
    w.status as workflow_status,
    w.creation_date,
    w.completion_date,
    s.numero_expediente,
    c.numero_certificado,
    COUNT(DISTINCT l.id) as total_lines,
    COUNT(DISTINCT CASE WHEN l.status = 'COMPLETED' THEN l.id END) as completed_lines,
    COUNT(DISTINCT a.id) as total_actions,
    COUNT(DISTINCT CASE WHEN a.status = 'SIGNED' THEN a.id END) as signed_actions,
    COUNT(DISTINCT CASE WHEN a.status = 'REJECTED' THEN a.id END) as rejected_actions
FROM signature_workflows w
LEFT JOIN solicitudes s ON w.solicitud_id = s.id
LEFT JOIN certificados c ON w.certificado_id = c.id
LEFT JOIN signature_addressee_lines l ON w.id = l.workflow_id
LEFT JOIN signature_addressee_groups g ON l.id = g.addressee_line_id
LEFT JOIN signature_actions a ON g.id = a.addressee_group_id
GROUP BY w.id, s.numero_expediente, c.numero_certificado;

-- Vista para consultar firmas pendientes por usuario
CREATE OR REPLACE VIEW v_pending_signatures AS
SELECT 
    a.id as action_id,
    a.user_id,
    u.name as user_name,
    u.email as user_email,
    w.id as workflow_id,
    w.public_access_id,
    w.subject,
    w.solicitud_id,
    s.numero_expediente,
    l.line_number,
    g.group_number,
    a.action_type,
    a.status,
    w.expiration_date,
    CASE 
        WHEN w.expiration_date < CURRENT_TIMESTAMP THEN true 
        ELSE false 
    END as is_expired
FROM signature_actions a
JOIN usuarios u ON a.user_id = u.id
JOIN signature_addressee_groups g ON a.addressee_group_id = g.id
JOIN signature_addressee_lines l ON g.addressee_line_id = l.id
JOIN signature_workflows w ON l.workflow_id = w.id
LEFT JOIN solicitudes s ON w.solicitud_id = s.id
WHERE a.status = 'NEW'
  AND l.status IN ('NEW', 'IN_PROGRESS')
  AND w.status IN ('NOT_STARTED', 'IN_PROGRESS')
ORDER BY w.creation_date ASC, l.line_number ASC;

-- ================================================================================
-- DATOS DE EJEMPLO (Comentados - descomentar para testing)
-- ================================================================================

/*
-- Ejemplo: Workflow de firma para certificado Clase A (requiere Dirección + DNCD)

-- 1. Crear workflow
INSERT INTO signature_workflows (
    solicitud_id, 
    public_access_id, 
    subject, 
    message,
    status,
    sender_user_id,
    expiration_date
) VALUES (
    'solicitud-uuid-aqui',
    generate_public_access_id(),
    'Firma de Certificado Clase A - Expediente SGC-2025-000001',
    'Certificado requiere firma de Dirección y aprobación de DNCD',
    'IN_PROGRESS',
    'usuario-direccion-uuid',
    CURRENT_TIMESTAMP + INTERVAL '30 days'
);

-- 2. Línea 1: Dirección firma
INSERT INTO signature_addressee_lines (workflow_id, line_number, status)
VALUES ('workflow-uuid', 1, 'IN_PROGRESS');

INSERT INTO signature_addressee_groups (addressee_line_id, group_number, is_or_group)
VALUES ('line-1-uuid', 1, false);

INSERT INTO signature_actions (addressee_group_id, user_id, action_type, status)
VALUES ('group-1-uuid', 'usuario-direccion-uuid', 'SIGN', 'NEW');

-- 3. Línea 2: DNCD firma
INSERT INTO signature_addressee_lines (workflow_id, line_number, status)
VALUES ('workflow-uuid', 2, 'NEW');

INSERT INTO signature_addressee_groups (addressee_line_id, group_number, is_or_group)
VALUES ('line-2-uuid', 1, false);

INSERT INTO signature_actions (addressee_group_id, user_id, action_type, status)
VALUES ('group-2-uuid', 'usuario-dncd-uuid', 'SIGN', 'NEW');
*/
