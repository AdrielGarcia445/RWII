SELECT
    w.id AS workflow_id,
    w.public_access_id,
    w.status AS workflow_status,

    c.numero_certificado,
    s.numero_expediente,

    COUNT(DISTINCT l.id) AS total_lines,
    COUNT(DISTINCT CASE WHEN l.status = 'COMPLETED' THEN l.id END) AS completed_lines,

    COUNT(DISTINCT a.id) AS total_signature_actions,
    COUNT(DISTINCT CASE WHEN a.status = 'SIGNED' THEN a.id END) AS signed_actions,

    BOOL_AND(
        (a.signature_data::jsonb ? 'document_hash')
        AND (a.signature_data::jsonb ? 'certificate_hash')
        AND (a.signature_data::jsonb ? 'timestamp')
        AND (a.signature_data::jsonb ? 'user_id')
    ) AS signatures_have_cryptographic_data,

    MAX(sd.file_hash) AS final_document_hash,
    BOOL_OR(sd.is_final) AS has_final_signed_document,

    COUNT(DISTINCT al.id) AS audit_events,

    CASE
        WHEN w.status = 'COMPLETED'
         AND COUNT(DISTINCT l.id) = COUNT(DISTINCT CASE WHEN l.status = 'COMPLETED' THEN l.id END)
         AND COUNT(DISTINCT a.id) = COUNT(DISTINCT CASE WHEN a.status = 'SIGNED' THEN a.id END)
         AND BOOL_AND(
              (a.signature_data::jsonb ? 'document_hash')
              AND (a.signature_data::jsonb ? 'certificate_hash')
              AND (a.signature_data::jsonb ? 'timestamp')
              AND (a.signature_data::jsonb ? 'user_id')
         )
         AND BOOL_OR(sd.is_final)
         AND COUNT(DISTINCT al.id) > 0
        THEN 'VERIFIED'
        ELSE 'NOT_VERIFIED'
    END AS verification_result

FROM signature_workflows w
JOIN solicitudes s ON s.id = w.solicitud_id
JOIN certificados c ON c.id = w.certificado_id
JOIN signature_addressee_lines l ON l.workflow_id = w.id
JOIN signature_addressee_groups g ON g.addressee_line_id = l.id
JOIN signature_actions a ON a.addressee_group_id = g.id
LEFT JOIN signature_documents sd
       ON sd.workflow_id = w.id
      AND sd.document_type = 'SIGNED_OUTPUT'
LEFT JOIN signature_audit_log al
       ON al.workflow_id = w.id

GROUP BY
    w.id,
    w.public_access_id,
    w.status,
    c.numero_certificado,
    s.numero_expediente;
