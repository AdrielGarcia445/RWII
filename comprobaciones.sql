-- Vista completa de solicitudes con estado de firmas
SELECT 
    s.numero_expediente,
    s.estado_codigo,
    srv.nombre as servicio,
    srv.requiere_dncd,
    u.name as solicitante,
    u.email as email_solicitante,
    
    -- Certificado
    c.numero_certificado,
    c.estado as certificado_estado,
    c.fecha_emision,
    
    -- Firma Dirección
    dir.name as firmante_direccion,
    c.fecha_emision as fecha_firma_direccion,
    CASE 
        WHEN c.firma_digital_direccion IS NOT NULL THEN '✓ Firmado'
        ELSE '✗ Pendiente'
    END as estado_firma_direccion,
    
    -- Firma DNCD
    dncd.name as firmante_dncd,
    c.fecha_firma_dncd,
    CASE 
        WHEN c.firma_digital_dncd IS NOT NULL THEN '✓ Firmado'
        WHEN srv.requiere_dncd THEN '⏳ Pendiente'
        ELSE 'N/A'
    END as estado_firma_dncd,
    
    -- Workflow
    sw.public_access_id as workflow_id,
    sw.status as workflow_status,
    sw.creation_date as workflow_creado,
    sw.completion_date as workflow_completado,
    
    -- Fechas
    s.fecha_creacion,
    s.fecha_actualizacion
    
FROM solicitudes s
LEFT JOIN catalogo_servicios srv ON s.servicio_id = srv.id
LEFT JOIN usuarios u ON s.usuario_id = u.id
LEFT JOIN certificados c ON s.certificado_id = c.id
LEFT JOIN usuarios dir ON c.firmante_direccion_id = dir.id
LEFT JOIN usuarios dncd ON c.firmante_dncd_id = dncd.id
LEFT JOIN signature_workflows sw ON sw.solicitud_id = s.id

ORDER BY s.fecha_creacion DESC;



-- Detalles completos del workflow por solicitud
SELECT 
    s.numero_expediente,
    sw.public_access_id as workflow_id,
    sw.status as workflow_status,
    sw.reference,
    
    -- Líneas del workflow
    sal.line_number as linea,
    sal.status as linea_status,
    sal.started_date as linea_iniciada,
    sal.completed_date as linea_completada,
    
    -- Acciones de firma
    sa.action_type as tipo_accion,
    sa.status as accion_status,
    u.name as firmante,
    u.rol_codigo as rol_firmante,
    sa.action_date as fecha_firma,
    
    -- Notificaciones
    CASE WHEN sa.notification_sent THEN '✓ Enviada' ELSE '✗ No enviada' END as notificacion

FROM solicitudes s
JOIN signature_workflows sw ON sw.solicitud_id = s.id
LEFT JOIN signature_addressee_lines sal ON sal.workflow_id = sw.id
LEFT JOIN signature_addressee_groups sag ON sag.addressee_line_id = sal.id
LEFT JOIN signature_actions sa ON sa.addressee_group_id = sag.id
LEFT JOIN usuarios u ON sa.user_id = u.id

ORDER BY s.numero_expediente, sal.line_number, sa.created_at;


-- Log de auditoría de todas las firmas
SELECT 
    s.numero_expediente,
    sw.public_access_id as workflow_id,
    sal.event_type as evento,
    u.name as usuario,
    u.rol_codigo as rol,
    sal.event_data,
    sal.ip_address,
    sal.timestamp as fecha_evento

FROM signature_audit_log sal
LEFT JOIN signature_workflows sw ON sal.workflow_id = sw.id
LEFT JOIN solicitudes s ON sw.solicitud_id = s.id
LEFT JOIN usuarios u ON sal.user_id = u.id

ORDER BY sal.timestamp DESC;


-- Resumen ejecutivo del estado de firmas
SELECT 
    s.numero_expediente,
    s.estado_codigo,
    
    -- Totales
    COUNT(DISTINCT sw.id) as total_workflows,
    COUNT(DISTINCT sal.id) as total_lineas,
    COUNT(DISTINCT sa.id) as total_acciones,
    
    -- Estados
    COUNT(CASE WHEN sa.status = 'SIGNED' THEN 1 END) as firmas_completadas,
    COUNT(CASE WHEN sa.status = 'NEW' THEN 1 END) as firmas_pendientes,
    
    -- Workflow
    MAX(sw.status) as workflow_status,
    MAX(sw.completion_date) as workflow_completado_el,
    
    -- Certificado
    MAX(c.estado) as certificado_estado

FROM solicitudes s
LEFT JOIN signature_workflows sw ON sw.solicitud_id = s.id
LEFT JOIN signature_addressee_lines sal ON sal.workflow_id = sw.id
LEFT JOIN signature_addressee_groups sag ON sag.addressee_line_id = sal.id
LEFT JOIN signature_actions sa ON sa.addressee_group_id = sag.id
LEFT JOIN certificados c ON s.certificado_id = c.id

GROUP BY s.id, s.numero_expediente, s.estado_codigo
ORDER BY s.fecha_creacion DESC;


-- Qué usuarios tienen firmas pendientes
SELECT 
    u.name as usuario,
    u.rol_codigo as rol,
    u.email,
    s.numero_expediente,
    s.estado_codigo,
    c.numero_certificado,
    sal.line_number as linea,
    sa.status as estado_accion,
    CASE 
        WHEN sa.notification_sent THEN 
            'Notificado el ' || TO_CHAR(sa.notification_date, 'DD/MM/YYYY HH24:MI')
        ELSE 'Sin notificar'
    END as notificacion,
    sw.expiration_date as vence_el

FROM signature_actions sa
JOIN signature_addressee_groups sag ON sa.addressee_group_id = sag.id
JOIN signature_addressee_lines sal ON sag.addressee_line_id = sal.id
JOIN signature_workflows sw ON sal.workflow_id = sw.id
JOIN solicitudes s ON sw.solicitud_id = s.id
JOIN certificados c ON s.certificado_id = c.id
JOIN usuarios u ON sa.user_id = u.id

WHERE sa.status = 'NEW'
AND sal.status = 'IN_PROGRESS'

ORDER BY sw.expiration_date, u.rol_codigo;


-- Cambiar 'SGC-2025-000001' por el número de expediente que quieras ver
SELECT 
    'SOLICITUD' as tipo,
    s.numero_expediente as referencia,
    s.estado_codigo as estado,
    s.fecha_creacion as fecha,
    '' as detalles
FROM solicitudes s
WHERE s.numero_expediente = 'SGC-2025-000001'

UNION ALL

SELECT 
    'HISTORIAL ESTADO' as tipo,
    hes.estado_codigo as referencia,
    u.name as estado,
    hes.fecha,
    hes.comentario as detalles
FROM historial_estados_solicitud hes
JOIN solicitudes s ON hes.solicitud_id = s.id
LEFT JOIN usuarios u ON hes.usuario_id = u.id
WHERE s.numero_expediente = 'SGC-2025-000001'

UNION ALL

SELECT 
    'WORKFLOW' as tipo,
    sw.public_access_id as referencia,
    sw.status as estado,
    sw.creation_date as fecha,
    'Líneas: ' || (SELECT COUNT(*) FROM signature_addressee_lines WHERE workflow_id = sw.id) as detalles
FROM signature_workflows sw
JOIN solicitudes s ON sw.solicitud_id = s.id
WHERE s.numero_expediente = 'SGC-2025-000001'

UNION ALL

SELECT 
    'FIRMA' as tipo,
    u.name || ' (' || u.rol_codigo || ')' as referencia,
    sa.status as estado,
    sa.action_date as fecha,
    'Línea ' || sal.line_number as detalles
FROM signature_actions sa
JOIN signature_addressee_groups sag ON sa.addressee_group_id = sag.id
JOIN signature_addressee_lines sal ON sag.addressee_line_id = sal.id
JOIN signature_workflows sw ON sal.workflow_id = sw.id
JOIN solicitudes s ON sw.solicitud_id = s.id
JOIN usuarios u ON sa.user_id = u.id
WHERE s.numero_expediente = 'SGC-2025-000001'

ORDER BY fecha DESC;