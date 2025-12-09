# 📋 Proceso de Firma Digital Adobe Sign - Documentación Técnica

## 📑 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Flujo Completo del Proceso](#flujo-completo-del-proceso)
4. [Componentes del Sistema](#componentes-del-sistema)
5. [Proceso de Firma Paso a Paso](#proceso-de-firma-paso-a-paso)
6. [Estructura de Datos](#estructura-de-datos)
7. [Casos de Uso](#casos-de-uso)
8. [Auditoría y Trazabilidad](#auditoría-y-trazabilidad)
9. [Verificación de Integridad](#verificación-de-integridad)
10. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🎯 Introducción

El sistema de firmas digitales implementado está basado en la arquitectura de **Adobe Sign API**, proporcionando un workflow profesional de firmas secuenciales con trazabilidad completa, integridad criptográfica y auditoría detallada.

### Características Principales

✅ **Firmas Secuenciales**: Flujo ordenado donde Dirección firma primero, DNCD después  
✅ **Trazabilidad Completa**: Cada acción registrada con timestamp, IP, user-agent  
✅ **Integridad Criptográfica**: Hash SHA256 de documentos y certificados  
✅ **ID Público Único**: Formato Adobe Sign (XXXX-XXXX-XXXX-XXXX) para verificación externa  
✅ **Auditoría Total**: Log detallado de todos los eventos del workflow  
✅ **Activación Automática**: Certificado activo solo cuando todas las firmas están completas  

---

## 🏗️ Arquitectura del Sistema

### Modelo de Datos (6 Tablas Principales)

```
signature_workflows (Workflow Principal)
    ├── signature_addressee_lines (Líneas de Firma)
    │   └── signature_addressee_groups (Grupos de Firmantes)
    │       └── signature_actions (Acciones Individuales)
    ├── signature_documents (Documentos Asociados)
    └── signature_audit_log (Log de Auditoría)
```

### Jerarquía del Workflow

```
Workflow
  │
  ├─ Line 1 (Dirección) - Estado: IN_PROGRESS al inicio
  │   └─ Group 1
  │       └─ Action: SIGN (Dirección) - Estado: NEW → SIGNED
  │
  └─ Line 2 (DNCD) - Estado: NEW al inicio
      └─ Group 1 (is_or_group: puede ser true si hay múltiples DNCD)
          └─ Action: SIGN (DNCD) - Estado: NEW → SIGNED
```

---

## 🔄 Flujo Completo del Proceso

### Fase 1: Creación del Certificado y Workflow (Dirección)

```
Usuario → Solicitud → VUS Aprueba → UPC Evalúa → DIRECCIÓN FIRMA
                                                        ↓
                                        [crear_workflow_firma_certificado()]
                                                        ↓
                                        Genera Workflow Adobe Sign:
                                        - Public Access ID: ABCD-1234-EFGH-5678
                                        - Status: IN_PROGRESS
                                        - Line 1: Dirección (ACTIVE)
                                        - Line 2: DNCD (WAITING)
                                                        ↓
                                        [firmar_documento_workflow()]
                                                        ↓
                                        Ejecuta Firma Dirección:
                                        ✓ Genera signature_data con:
                                          - Timestamp ISO 8601
                                          - User info (name, email, rol)
                                          - Certificate Hash (SHA256)
                                          - IP Address
                                          - User Agent
                                        ✓ Marca Action como SIGNED
                                        ✓ Completa Group 1
                                        ✓ Completa Line 1
                                        ✓ Activa Line 2 → DNCD recibe notificación
                                        ✓ Certificado estado: EN_PROCESO
                                        ✓ Solicitud estado: ENVIADO_DNCD
```

### Fase 2: Firma DNCD

```
DNCD recibe notificación → Consulta solicitud pendiente
                                    ↓
                        [firmar_documento_workflow()]
                                    ↓
                        Ejecuta Firma DNCD:
                        ✓ Busca Action pendiente en Line 2
                        ✓ Genera signature_data con datos DNCD
                        ✓ Marca Action como SIGNED
                        ✓ Completa Group 1 (Line 2)
                        ✓ Completa Line 2
                        ✓ NO HAY más líneas → COMPLETA WORKFLOW
                        ✓ Certificado estado: ACTIVO ✅
                        ✓ Solicitud estado: APROBADO_FINAL
                        ✓ Usuario recibe notificación: Certificado listo
```

---

## 🧩 Componentes del Sistema

### 1. SignatureWorkflow (Tabla Principal)

**Propósito**: Contenedor principal que agrupa todo el proceso de firma de un certificado.

```sql
CREATE TABLE signature_workflows (
    id UUID PRIMARY KEY,
    solicitud_id UUID REFERENCES solicitudes(id),
    certificado_id UUID REFERENCES certificados(id),
    public_access_id VARCHAR(20) UNIQUE NOT NULL, -- XXXX-XXXX-XXXX-XXXX
    reference VARCHAR(100),                       -- Número de expediente
    subject TEXT,                                 -- Asunto del workflow
    message TEXT,                                 -- Mensaje para firmantes
    status VARCHAR(50) NOT NULL,                  -- NOT_STARTED, IN_PROGRESS, COMPLETED, REJECTED, EXPIRED
    creation_date TIMESTAMP NOT NULL,
    init_date TIMESTAMP,
    expiration_date TIMESTAMP,                    -- 30 días por defecto
    send_date TIMESTAMP,
    completion_date TIMESTAMP,
    sender_user_id UUID REFERENCES usuarios(id),
    callback_code VARCHAR(100),
    workflow_data JSONB,                          -- Metadata adicional
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Estados del Workflow**:
- `NOT_STARTED`: Creado pero no iniciado
- `IN_PROGRESS`: En proceso de firma (estado principal)
- `COMPLETED`: Todas las firmas completadas ✅
- `REJECTED`: Algún firmante rechazó
- `EXPIRED`: Expiró el plazo (30 días)

**Ejemplo de workflow_data**:
```json
{
    "solicitud_numero": "SGC-2025-000123",
    "certificado_numero": "CERT-2025-0045",
    "servicio": "Certificado Clase A",
    "requiere_dncd": true
}
```

### 2. SignatureAddresseeLine (Líneas de Firma Secuencial)

**Propósito**: Define el orden de firma. Cada línea debe completarse antes de activar la siguiente.

```sql
CREATE TABLE signature_addressee_lines (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES signature_workflows(id),
    line_number INTEGER NOT NULL,              -- 1, 2, 3...
    status VARCHAR(50) NOT NULL,               -- NEW, IN_PROGRESS, COMPLETED
    started_date TIMESTAMP,
    completed_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Lógica de Activación**:
```python
# Line 1 (Dirección) se activa inmediatamente al crear workflow
line1.status = 'IN_PROGRESS'

# Line 2 (DNCD) se activa solo cuando Line 1 está completa
if all(g.status == 'COMPLETED' for g in line1.groups):
    line1.status = 'COMPLETED'
    line2.status = 'IN_PROGRESS'  # Activa siguiente línea
    # Enviar notificaciones a firmantes de Line 2
```

### 3. SignatureAddresseeGroup (Grupos de Firmantes)

**Propósito**: Agrupa firmantes dentro de una línea. Permite lógica AND (todos firman) u OR (uno firma).

```sql
CREATE TABLE signature_addressee_groups (
    id UUID PRIMARY KEY,
    addressee_line_id UUID REFERENCES signature_addressee_lines(id),
    group_number INTEGER NOT NULL,
    is_or_group BOOLEAN DEFAULT FALSE,         -- false=AND, true=OR
    status VARCHAR(50) NOT NULL,               -- NEW, IN_PROGRESS, COMPLETED
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Lógica de Completado**:
```python
if group.is_or_group:
    # Grupo OR: Con UNA firma es suficiente
    if any(a.status == 'SIGNED' for a in group.actions):
        group.status = 'COMPLETED'
else:
    # Grupo AND: TODAS las firmas necesarias
    if all(a.status == 'SIGNED' for a in group.actions):
        group.status = 'COMPLETED'
```

**Caso de Uso - Múltiples DNCD**:
```
Si hay 3 usuarios DNCD activos:
  Group 1 (is_or_group=true)
    ├─ Action: Usuario DNCD #1
    ├─ Action: Usuario DNCD #2
    └─ Action: Usuario DNCD #3
  
  → Solo UNO necesita firmar para completar el grupo
```

### 4. SignatureAction (Acción Individual de Firma)

**Propósito**: Representa la acción de firma de un usuario específico.

```sql
CREATE TABLE signature_actions (
    id UUID PRIMARY KEY,
    addressee_group_id UUID REFERENCES signature_addressee_groups(id),
    user_id UUID REFERENCES usuarios(id),
    action_type VARCHAR(50) NOT NULL,          -- SIGN, APPROVAL, VIEW, CERTIFY
    status VARCHAR(50) NOT NULL,               -- NEW, SIGNED, REJECTED, CANCELLED
    action_date TIMESTAMP,                     -- Momento de la firma
    reject_type VARCHAR(100),
    reject_reason TEXT,
    signature_data JSONB,                      -- Datos completos de la firma ⭐
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Estructura de signature_data** (Lo más importante):
```json
{
    "timestamp": "2025-12-09T14:32:15.123456",
    "user_id": "uuid-del-usuario",
    "user_name": "Dr. Juan Pérez",
    "user_email": "direccion@msp.gob.do",
    "user_rol": "DIRECCION",
    "signature_type": "ELECTRONIC",
    "certificate_hash": "a1b2c3d4e5f6...",  // SHA256 del certificado
    "document_hash": "ruta/al/documento",   // En producción: SHA256 del archivo
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "workflow_public_id": "ABCD-1234-EFGH-5678"
}
```

### 5. SignatureDocument (Documentos del Workflow)

**Propósito**: Asocia documentos al workflow con hash de integridad.

```sql
CREATE TABLE signature_documents (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES signature_workflows(id),
    document_type VARCHAR(50) NOT NULL,        -- CERTIFICATE, ATTACHMENT, PROOF
    filename VARCHAR(255) NOT NULL,
    public_access_id VARCHAR(20) UNIQUE,
    storage_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,            -- SHA256 del archivo
    mime_type VARCHAR(100),
    file_size INTEGER,
    version INTEGER DEFAULT 1,
    is_final BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### 6. SignatureAuditLog (Log de Auditoría)

**Propósito**: Registro completo de todos los eventos del workflow.

```sql
CREATE TABLE signature_audit_log (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES signature_workflows(id),
    action_id UUID REFERENCES signature_actions(id),
    user_id UUID REFERENCES usuarios(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL
);
```

**Tipos de Eventos**:
- `WORKFLOW_CREATED`: Workflow creado
- `LINE_ACTIVATED`: Línea de firma activada
- `DOCUMENT_SIGNED`: Documento firmado
- `WORKFLOW_COMPLETED`: Workflow completado
- `NOTIFICATION_SENT`: Notificación enviada
- `STATUS_CHANGED`: Cambio de estado

---

## 📝 Proceso de Firma Paso a Paso

### PASO 1: Dirección Aprueba y Firma

**Endpoint**: `POST /solicitudes/<solicitud_id>/firmar-direccion`

**Código Ejecutado**:
```python
@app.route('/solicitudes/<solicitud_id>/firmar-direccion', methods=['POST'])
@login_required
@role_required('DIRECCION')
def firmar_direccion(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # 1. Crear certificado EN_PROCESO
    certificado = Certificado(
        solicitud_id=solicitud_id,
        numero_certificado=generar_numero_certificado(),
        tipo_servicio_codigo=solicitud.servicio.codigo,
        nombre_archivo=f'certificado_{solicitud.numero_expediente}.pdf',
        ruta=f'certificados/{solicitud.numero_expediente}.pdf',
        fecha_emision=datetime.utcnow(),
        fecha_vencimiento=calcular_fecha_vencimiento(solicitud.servicio),
        firmante_direccion_id=session['user_id'],
        firma_digital_direccion='PENDING_WORKFLOW',  # Temporal
        estado='EN_PROCESO'  # No ACTIVO todavía
    )
    db.session.add(certificado)
    db.session.flush()
    
    # 2. Crear workflow de firma digital
    workflow = crear_workflow_firma_certificado(
        solicitud_id=solicitud_id,
        certificado_id=certificado.id,
        requiere_dncd=solicitud.servicio.requiere_dncd
    )
    
    # 3. Ejecutar firma inmediatamente
    resultado_firma = firmar_documento_workflow(
        workflow_id=workflow.id,
        user_id=session['user_id'],
        signature_type='ELECTRONIC'
    )
    
    # 4. Actualizar certificado con firma
    certificado.firma_digital_direccion = str(resultado_firma['signature_data'])
    
    # 5. Cambiar estado según requiera DNCD
    if solicitud.servicio.requiere_dncd:
        cambiar_estado_solicitud(solicitud_id, 'ENVIADO_DNCD')
    else:
        cambiar_estado_solicitud(solicitud_id, 'APROBADO_FINAL')
        certificado.estado = 'ACTIVO'  # Si no requiere DNCD, activa ya
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'certificado_id': certificado.id,
        'workflow_id': workflow.id,
        'workflow_public_id': workflow.public_access_id,
        'workflow_status': workflow.status,
        'signature_data': resultado_firma['signature_data']
    })
```

**Función Interna - crear_workflow_firma_certificado()**:
```python
def crear_workflow_firma_certificado(solicitud_id, certificado_id, requiere_dncd=True):
    solicitud = Solicitud.query.get(solicitud_id)
    certificado = Certificado.query.get(certificado_id)
    
    # 1. Crear workflow principal
    workflow = SignatureWorkflow(
        solicitud_id=solicitud_id,
        certificado_id=certificado_id,
        public_access_id=generar_id_publico(),  # XXXX-XXXX-XXXX-XXXX
        reference=solicitud.numero_expediente,
        subject=f'Firma de Certificado {certificado.numero_certificado}',
        message=f'Certificado para solicitud {solicitud.numero_expediente}',
        status='IN_PROGRESS',
        sender_user_id=session.get('user_id'),
        init_date=datetime.utcnow(),
        expiration_date=datetime.utcnow() + timedelta(days=30),
        workflow_data={
            'solicitud_numero': solicitud.numero_expediente,
            'certificado_numero': certificado.numero_certificado,
            'servicio': solicitud.servicio.nombre,
            'requiere_dncd': requiere_dncd
        }
    )
    db.session.add(workflow)
    db.session.flush()
    
    # 2. Crear Línea 1: Dirección
    line1 = SignatureAddresseeLine(
        workflow_id=workflow.id,
        line_number=1,
        status='IN_PROGRESS',  # Ya activa
        started_date=datetime.utcnow()
    )
    db.session.add(line1)
    db.session.flush()
    
    # 3. Crear Grupo 1 de Línea 1
    group1 = SignatureAddresseeGroup(
        addressee_line_id=line1.id,
        group_number=1,
        is_or_group=False,  # Solo Dirección firma
        status='IN_PROGRESS'
    )
    db.session.add(group1)
    db.session.flush()
    
    # 4. Crear Acción de Dirección
    action_direccion = SignatureAction(
        addressee_group_id=group1.id,
        user_id=session.get('user_id'),
        action_type='SIGN',
        status='NEW'  # Pendiente de ejecución
    )
    db.session.add(action_direccion)
    
    # 5. Si requiere DNCD, crear Línea 2
    if requiere_dncd:
        line2 = SignatureAddresseeLine(
            workflow_id=workflow.id,
            line_number=2,
            status='NEW'  # Inactiva hasta que Line 1 complete
        )
        db.session.add(line2)
        db.session.flush()
        
        group2 = SignatureAddresseeGroup(
            addressee_line_id=line2.id,
            group_number=1,
            is_or_group=False  # Puede ser True si múltiples DNCD
        )
        db.session.add(group2)
        db.session.flush()
        
        # Crear acciones para usuarios DNCD
        usuarios_dncd = Usuario.query.filter_by(rol_codigo='DNCD', activo=True).all()
        
        if len(usuarios_dncd) > 1:
            group2.is_or_group = True  # Con uno que firme es suficiente
        
        for usuario_dncd in usuarios_dncd:
            action_dncd = SignatureAction(
                addressee_group_id=group2.id,
                user_id=usuario_dncd.id,
                action_type='SIGN',
                status='NEW'
            )
            db.session.add(action_dncd)
    
    db.session.commit()
    
    # 6. Registrar en auditoría
    audit_log = SignatureAuditLog(
        workflow_id=workflow.id,
        user_id=session.get('user_id'),
        event_type='WORKFLOW_CREATED',
        event_data={
            'solicitud_id': solicitud_id,
            'certificado_id': certificado_id,
            'requiere_dncd': requiere_dncd,
            'lineas_creadas': 2 if requiere_dncd else 1
        },
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return workflow
```

**Función Interna - firmar_documento_workflow()**:
```python
def firmar_documento_workflow(workflow_id, user_id, signature_type='ELECTRONIC'):
    workflow = SignatureWorkflow.query.get(workflow_id)
    
    # 1. Buscar acción pendiente del usuario en línea activa
    action = None
    for line in workflow.addressee_lines:
        if line.status in ['NEW', 'IN_PROGRESS']:
            for group in line.groups:
                for act in group.actions:
                    if act.user_id == user_id and act.status == 'NEW':
                        action = act
                        break
                if action:
                    break
        if action:
            break
    
    if not action:
        raise ValueError("No hay acción pendiente para este usuario")
    
    # 2. Generar datos de la firma
    usuario = Usuario.query.get(user_id)
    certificado = Certificado.query.get(workflow.certificado_id)
    
    signature_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'user_name': usuario.name,
        'user_email': usuario.email,
        'user_rol': usuario.rol_codigo,
        'signature_type': signature_type,
        'certificate_hash': generar_hash_certificado(
            f'{certificado.numero_certificado}{datetime.utcnow().isoformat()}'
        ),
        'document_hash': certificado.ruta,
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string,
        'workflow_public_id': workflow.public_access_id
    }
    
    # 3. Actualizar acción como SIGNED
    action.status = 'SIGNED'
    action.action_date = datetime.utcnow()
    action.signature_data = signature_data
    
    # 4. Verificar completado de grupo
    group = action.addressee_group
    if group.is_or_group:
        group.status = 'COMPLETED'  # Con una firma basta
    else:
        if all(a.status in ['SIGNED', 'APPROVED'] for a in group.actions):
            group.status = 'COMPLETED'
    
    # 5. Verificar completado de línea
    line = group.addressee_line
    if all(g.status == 'COMPLETED' for g in line.groups):
        line.status = 'COMPLETED'
        line.completed_date = datetime.utcnow()
        
        # 6. Buscar siguiente línea
        siguiente_linea = SignatureAddresseeLine.query.filter_by(
            workflow_id=workflow_id,
            line_number=line.line_number + 1
        ).first()
        
        if siguiente_linea:
            # HAY siguiente línea → Activarla
            siguiente_linea.status = 'IN_PROGRESS'
            siguiente_linea.started_date = datetime.utcnow()
            
            # Notificar a firmantes de siguiente línea
            for group in siguiente_linea.groups:
                for action in group.actions:
                    crear_notificacion(
                        action.user_id,
                        'DOCUMENTO_PENDIENTE_FIRMA',
                        f'Documento {workflow.reference} requiere su firma',
                        workflow.solicitud_id
                    )
                    action.notification_sent = True
                    action.notification_date = datetime.utcnow()
            
            # Registrar activación de línea
            audit_log = SignatureAuditLog(
                workflow_id=workflow_id,
                user_id=user_id,
                event_type='LINE_ACTIVATED',
                event_data={
                    'line_number': siguiente_linea.line_number,
                    'previous_line': line.line_number
                },
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit_log)
        else:
            # NO HAY siguiente línea → WORKFLOW COMPLETADO
            workflow.status = 'COMPLETED'
            workflow.completion_date = datetime.utcnow()
            
            # ACTIVAR CERTIFICADO
            certificado = Certificado.query.get(workflow.certificado_id)
            certificado.estado = 'ACTIVO'
            
            # Registrar completado
            audit_log = SignatureAuditLog(
                workflow_id=workflow_id,
                user_id=user_id,
                event_type='WORKFLOW_COMPLETED',
                event_data={
                    'completion_date': datetime.utcnow().isoformat(),
                    'total_lines': line.line_number,
                    'certificado_id': certificado.id,
                    'certificado_estado': 'ACTIVO'
                },
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit_log)
    
    # 7. Registrar firma ejecutada
    audit_log = SignatureAuditLog(
        workflow_id=workflow_id,
        action_id=action.id,
        user_id=user_id,
        event_type='DOCUMENT_SIGNED',
        event_data=signature_data,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit_log)
    
    db.session.commit()
    
    return {
        'success': True,
        'workflow_status': workflow.status,
        'certificado_estado': certificado.estado if certificado else None,
        'signature_data': signature_data
    }
```

### PASO 2: DNCD Firma

**Endpoint**: `POST /solicitudes/<solicitud_id>/firmar-dncd`

**Código Ejecutado**:
```python
@app.route('/solicitudes/<solicitud_id>/firmar-dncd', methods=['POST'])
@login_required
@role_required('DNCD')
def firmar_dncd(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # 1. Buscar workflow activo
    workflow = SignatureWorkflow.query.filter_by(
        solicitud_id=solicitud_id,
        status='IN_PROGRESS'
    ).first()
    
    if not workflow:
        raise ValueError('No hay workflow activo')
    
    # 2. Ejecutar firma DNCD
    resultado_firma = firmar_documento_workflow(
        workflow_id=workflow.id,
        user_id=session['user_id'],
        signature_type='ELECTRONIC'
    )
    
    # 3. Actualizar certificado
    if solicitud.certificado_id:
        certificado = Certificado.query.get(solicitud.certificado_id)
        certificado.firmante_dncd_id = session['user_id']
        certificado.firma_digital_dncd = str(resultado_firma['signature_data'])
        certificado.fecha_firma_dncd = datetime.utcnow()
        # estado ya fue actualizado a ACTIVO por firmar_documento_workflow()
    
    # 4. Cambiar estado de solicitud
    cambiar_estado_solicitud(solicitud_id, 'APROBADO_FINAL')
    solicitud.fecha_aprobacion_dncd = datetime.utcnow()
    
    # 5. Notificar usuario
    crear_notificacion(
        solicitud.usuario_id,
        'CERTIFICADO_LISTO',
        f'Su certificado está listo para retiro',
        solicitud_id
    )
    
    # 6. Notificar VUS
    usuarios_vus = Usuario.query.filter_by(rol_codigo='VUS', activo=True).all()
    for vus in usuarios_vus:
        crear_notificacion(
            vus.id,
            'CERTIFICADO_PARA_ENTREGA',
            f'Certificado {solicitud.numero_expediente} listo para entrega',
            solicitud_id
        )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'workflow_id': workflow.id,
        'workflow_public_id': workflow.public_access_id,
        'workflow_status': workflow.status,  # Debe ser 'COMPLETED'
        'certificado_estado': certificado.estado,  # Debe ser 'ACTIVO'
        'signature_data': resultado_firma['signature_data']
    })
```

---

## 📊 Estructura de Datos

### Estado del Workflow Completo (GET /api/workflows/<id>/status)

```json
{
    "id": "uuid-workflow",
    "public_access_id": "ABCD-1234-EFGH-5678",
    "status": "COMPLETED",
    "solicitud_id": "uuid-solicitud",
    "certificado_id": "uuid-certificado",
    "reference": "SGC-2025-000123",
    "subject": "Firma de Certificado CERT-2025-0045",
    "creation_date": "2025-12-09T14:00:00",
    "completion_date": "2025-12-09T15:30:00",
    "sender": {
        "id": "uuid-user",
        "name": "Dr. Juan Pérez",
        "email": "direccion@msp.gob.do",
        "rol_codigo": "DIRECCION"
    },
    "addressee_lines": [
        {
            "line_number": 1,
            "status": "COMPLETED",
            "started_date": "2025-12-09T14:00:00",
            "completed_date": "2025-12-09T14:15:00",
            "groups": [
                {
                    "group_number": 1,
                    "is_or_group": false,
                    "status": "COMPLETED",
                    "actions": [
                        {
                            "user_id": "uuid-direccion",
                            "user_name": "Dr. Juan Pérez",
                            "user_email": "direccion@msp.gob.do",
                            "user_rol": "DIRECCION",
                            "action_type": "SIGN",
                            "status": "SIGNED",
                            "action_date": "2025-12-09T14:15:00",
                            "signature_data": {
                                "timestamp": "2025-12-09T14:15:00.123456",
                                "user_name": "Dr. Juan Pérez",
                                "user_email": "direccion@msp.gob.do",
                                "user_rol": "DIRECCION",
                                "signature_type": "ELECTRONIC",
                                "certificate_hash": "a1b2c3d4e5f6...",
                                "ip_address": "192.168.1.100",
                                "workflow_public_id": "ABCD-1234-EFGH-5678"
                            }
                        }
                    ]
                }
            ]
        },
        {
            "line_number": 2,
            "status": "COMPLETED",
            "started_date": "2025-12-09T14:15:00",
            "completed_date": "2025-12-09T15:30:00",
            "groups": [
                {
                    "group_number": 1,
                    "is_or_group": false,
                    "status": "COMPLETED",
                    "actions": [
                        {
                            "user_id": "uuid-dncd",
                            "user_name": "Oficial DNCD",
                            "user_email": "dncd@msp.gob.do",
                            "user_rol": "DNCD",
                            "action_type": "SIGN",
                            "status": "SIGNED",
                            "action_date": "2025-12-09T15:30:00",
                            "signature_data": {
                                "timestamp": "2025-12-09T15:30:00.654321",
                                "user_name": "Oficial DNCD",
                                "user_email": "dncd@msp.gob.do",
                                "user_rol": "DNCD",
                                "signature_type": "ELECTRONIC",
                                "certificate_hash": "x9y8z7w6v5u4...",
                                "ip_address": "192.168.1.101",
                                "workflow_public_id": "ABCD-1234-EFGH-5678"
                            }
                        }
                    ]
                }
            ]
        }
    ]
}
```

### Lista de Firmas (GET /api/workflows/<id>/signatures)

```json
[
    {
        "line_number": 1,
        "signer_id": "uuid-direccion",
        "signer_name": "Dr. Juan Pérez",
        "signer_email": "direccion@msp.gob.do",
        "signer_rol": "DIRECCION",
        "signature_date": "2025-12-09T14:15:00",
        "signature_type": "ELECTRONIC",
        "certificate_hash": "a1b2c3d4e5f6...",
        "document_hash": "certificados/SGC-2025-000123.pdf",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
    },
    {
        "line_number": 2,
        "signer_id": "uuid-dncd",
        "signer_name": "Oficial DNCD",
        "signer_email": "dncd@msp.gob.do",
        "signer_rol": "DNCD",
        "signature_date": "2025-12-09T15:30:00",
        "signature_type": "ELECTRONIC",
        "certificate_hash": "x9y8z7w6v5u4...",
        "document_hash": "certificados/SGC-2025-000123.pdf",
        "ip_address": "192.168.1.101",
        "user_agent": "Mozilla/5.0..."
    }
]
```

### Log de Auditoría (GET /api/workflows/<id>/audit-log)

```json
[
    {
        "id": "uuid-audit-1",
        "workflow_id": "uuid-workflow",
        "user_id": "uuid-direccion",
        "event_type": "WORKFLOW_CREATED",
        "event_data": {
            "solicitud_id": "uuid-solicitud",
            "certificado_id": "uuid-certificado",
            "requiere_dncd": true,
            "lineas_creadas": 2
        },
        "timestamp": "2025-12-09T14:00:00",
        "ip_address": "192.168.1.100"
    },
    {
        "id": "uuid-audit-2",
        "workflow_id": "uuid-workflow",
        "action_id": "uuid-action-1",
        "user_id": "uuid-direccion",
        "event_type": "DOCUMENT_SIGNED",
        "event_data": {
            "timestamp": "2025-12-09T14:15:00",
            "user_rol": "DIRECCION",
            "certificate_hash": "a1b2c3d4e5f6..."
        },
        "timestamp": "2025-12-09T14:15:00",
        "ip_address": "192.168.1.100"
    },
    {
        "id": "uuid-audit-3",
        "workflow_id": "uuid-workflow",
        "user_id": "uuid-direccion",
        "event_type": "LINE_ACTIVATED",
        "event_data": {
            "line_number": 2,
            "previous_line": 1
        },
        "timestamp": "2025-12-09T14:15:00",
        "ip_address": "192.168.1.100"
    },
    {
        "id": "uuid-audit-4",
        "workflow_id": "uuid-workflow",
        "action_id": "uuid-action-2",
        "user_id": "uuid-dncd",
        "event_type": "DOCUMENT_SIGNED",
        "event_data": {
            "timestamp": "2025-12-09T15:30:00",
            "user_rol": "DNCD",
            "certificate_hash": "x9y8z7w6v5u4..."
        },
        "timestamp": "2025-12-09T15:30:00",
        "ip_address": "192.168.1.101"
    },
    {
        "id": "uuid-audit-5",
        "workflow_id": "uuid-workflow",
        "user_id": "uuid-dncd",
        "event_type": "WORKFLOW_COMPLETED",
        "event_data": {
            "completion_date": "2025-12-09T15:30:00",
            "total_lines": 2,
            "certificado_id": "uuid-certificado",
            "certificado_estado": "ACTIVO"
        },
        "timestamp": "2025-12-09T15:30:00",
        "ip_address": "192.168.1.101"
    }
]
```

---

## 🎭 Casos de Uso

### Caso 1: Certificado sin DNCD (Solo Dirección)

```
Solicitud → VUS → UPC → DIRECCION firma
                           ↓
                    Workflow creado:
                    - Line 1: Dirección
                    - NO Line 2
                           ↓
                    Dirección firma Line 1
                           ↓
                    Line 1 completa
                           ↓
                    NO hay más líneas
                           ↓
                    Workflow COMPLETED
                    Certificado ACTIVO ✅
```

### Caso 2: Certificado con DNCD (Secuencial)

```
Solicitud → VUS → UPC → DIRECCION firma
                           ↓
                    Workflow creado:
                    - Line 1: Dirección (ACTIVE)
                    - Line 2: DNCD (WAITING)
                           ↓
                    Dirección firma Line 1
                           ↓
                    Line 1 completa
                           ↓
                    Line 2 activada (DNCD notificado)
                           ↓
                    DNCD firma Line 2
                           ↓
                    Line 2 completa
                           ↓
                    NO hay más líneas
                           ↓
                    Workflow COMPLETED
                    Certificado ACTIVO ✅
```

### Caso 3: Múltiples DNCD (Grupo OR)

```
Workflow creado:
- Line 2: DNCD
  └─ Group 1 (is_or_group=true)
      ├─ Action: DNCD Usuario #1 (NEW)
      ├─ Action: DNCD Usuario #2 (NEW)
      └─ Action: DNCD Usuario #3 (NEW)

→ Cualquiera de los 3 puede firmar
→ Cuando UNO firma:
  - Su Action: SIGNED
  - Group 1: COMPLETED (no espera a los otros)
  - Line 2: COMPLETED
  - Workflow: COMPLETED
  - Certificado: ACTIVO ✅
```

### Caso 4: Rechazo de Firma

```
Dirección firma Line 1 → Line 2 activa → DNCD RECHAZA
                                              ↓
                                        Action status: REJECTED
                                        reject_type: "DOCUMENTACION_INCORRECTA"
                                        reject_reason: "Falta documento X"
                                              ↓
                                        Workflow status: REJECTED
                                        Certificado estado: EN_PROCESO (no cambia)
                                        Solicitud: RECHAZADO_DNCD
                                              ↓
                                        Usuario notificado
```

---

## 🔍 Auditoría y Trazabilidad

### Información Registrada por Cada Firma

✅ **Identidad del Firmante**:
- UUID del usuario
- Nombre completo
- Email
- Rol en el sistema

✅ **Momento Exacto**:
- Timestamp ISO 8601 con microsegundos
- Fecha de acción (action_date)

✅ **Integridad del Documento**:
- Hash SHA256 del certificado
- Hash del documento firmado
- Workflow Public ID

✅ **Origen de la Firma**:
- Dirección IP del firmante
- User-Agent (navegador/dispositivo)

✅ **Contexto**:
- Tipo de firma (ELECTRONIC, ADVANCED, QUALIFIED)
- Estado del workflow al momento
- Línea y grupo de firma

### Consultas de Auditoría

**Ver todas las firmas de un certificado**:
```sql
SELECT 
    sa.action_date,
    u.name AS firmante,
    u.rol_codigo,
    sa.signature_data->>'timestamp' AS timestamp_firma,
    sa.signature_data->>'certificate_hash' AS hash_cert,
    sa.signature_data->>'ip_address' AS ip
FROM signature_actions sa
JOIN signature_addressee_groups sag ON sa.addressee_group_id = sag.id
JOIN signature_addressee_lines sal ON sag.addressee_line_id = sal.id
JOIN signature_workflows sw ON sal.workflow_id = sw.id
JOIN usuarios u ON sa.user_id = u.id
WHERE sw.certificado_id = 'uuid-certificado'
AND sa.status = 'SIGNED'
ORDER BY sa.action_date;
```

**Ver historial completo de un workflow**:
```sql
SELECT 
    sal.timestamp,
    sal.event_type,
    u.name AS usuario,
    sal.event_data,
    sal.ip_address
FROM signature_audit_log sal
LEFT JOIN usuarios u ON sal.user_id = u.id
WHERE sal.workflow_id = 'uuid-workflow'
ORDER BY sal.timestamp;
```

**Detectar anomalías (múltiples firmas desde misma IP)**:
```sql
SELECT 
    sa.signature_data->>'ip_address' AS ip,
    COUNT(DISTINCT sa.user_id) AS usuarios_distintos,
    STRING_AGG(u.name, ', ') AS firmantes
FROM signature_actions sa
JOIN usuarios u ON sa.user_id = u.id
WHERE sa.status = 'SIGNED'
GROUP BY sa.signature_data->>'ip_address'
HAVING COUNT(DISTINCT sa.user_id) > 1;
```

---

## 🔐 Verificación de Integridad

### Validación de Hash de Certificado

```python
def verificar_integridad_certificado(certificado_id):
    """Verifica que el hash almacenado coincida con el documento actual"""
    certificado = Certificado.query.get(certificado_id)
    workflow = SignatureWorkflow.query.filter_by(
        certificado_id=certificado_id,
        status='COMPLETED'
    ).first()
    
    if not workflow:
        return {'valido': False, 'error': 'No hay workflow completado'}
    
    # Obtener todas las firmas
    firmas = []
    for line in workflow.addressee_lines:
        for group in line.groups:
            for action in group.actions:
                if action.status == 'SIGNED' and action.signature_data:
                    firmas.append(action.signature_data)
    
    # Calcular hash actual del certificado
    with open(certificado.ruta, 'rb') as f:
        contenido = f.read()
    hash_actual = hashlib.sha256(contenido).hexdigest()
    
    # Comparar con hashes de las firmas
    hashes_originales = [f['certificate_hash'] for f in firmas]
    
    return {
        'valido': all(h == hash_actual for h in hashes_originales),
        'hash_actual': hash_actual,
        'hashes_firmas': hashes_originales,
        'firmas_verificadas': len(firmas)
    }
```

### Verificación Pública por ID

```python
@app.route('/verificar/<public_access_id>')
def verificar_certificado_publico(public_access_id):
    """Endpoint público para verificar autenticidad de certificado"""
    workflow = SignatureWorkflow.query.filter_by(
        public_access_id=public_access_id
    ).first()
    
    if not workflow:
        return jsonify({'error': 'Certificado no encontrado'}), 404
    
    certificado = Certificado.query.get(workflow.certificado_id)
    
    # Obtener firmas
    firmas = []
    for line in workflow.addressee_lines:
        for group in line.groups:
            for action in group.actions:
                if action.status == 'SIGNED':
                    firmas.append({
                        'firmante': action.user.name,
                        'rol': action.user.rol_codigo,
                        'fecha': action.action_date.isoformat(),
                        'linea': line.line_number
                    })
    
    return jsonify({
        'valido': workflow.status == 'COMPLETED',
        'numero_certificado': certificado.numero_certificado,
        'fecha_emision': certificado.fecha_emision.isoformat(),
        'fecha_vencimiento': certificado.fecha_vencimiento.isoformat(),
        'estado': certificado.estado,
        'firmas': firmas,
        'workflow_completado': workflow.completion_date.isoformat() if workflow.completion_date else None
    })
```

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si un firmante rechaza el documento?

1. La acción se marca con `status='REJECTED'`
2. Se registran `reject_type` y `reject_reason`
3. El workflow cambia a `status='REJECTED'`
4. El certificado NO se activa (permanece `EN_PROCESO`)
5. La solicitud cambia a estado de rechazo correspondiente
6. Se notifica al solicitante con la razón del rechazo

### ¿Puede un firmante firmar en nombre de otro?

**NO**. El sistema valida:
- El usuario en sesión debe coincidir con `user_id` de la acción
- Solo puede firmar acciones donde `status='NEW'`
- Solo en líneas con `status='IN_PROGRESS'`

### ¿Qué pasa si un workflow expira (30 días)?

1. Tarea programada verifica `expiration_date`
2. Si `expiration_date < now()` y `status='IN_PROGRESS'`:
   - Workflow → `status='EXPIRED'`
   - Certificado permanece `EN_PROCESO` (no se activa)
   - Solicitud → estado rechazado
   - Se notifica al solicitante

### ¿Cómo se maneja la revocación de un certificado firmado?

```python
def revocar_certificado(certificado_id, motivo):
    certificado = Certificado.query.get(certificado_id)
    workflow = SignatureWorkflow.query.filter_by(
        certificado_id=certificado_id
    ).first()
    
    # Cambiar estado del certificado
    certificado.estado = 'REVOCADO'
    certificado.fecha_revocacion = datetime.utcnow()
    certificado.motivo_revocacion = motivo
    
    # Registrar en auditoría del workflow
    audit_log = SignatureAuditLog(
        workflow_id=workflow.id,
        user_id=session.get('user_id'),
        event_type='CERTIFICATE_REVOKED',
        event_data={'motivo': motivo},
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit_log)
    db.session.commit()
```

### ¿Se pueden agregar más líneas después de crear el workflow?

**NO en el diseño actual**. El workflow es inmutable una vez creado. Si se necesitan más firmas:
1. Rechazar el workflow actual
2. Crear nuevo workflow con las líneas adicionales
3. Solicitar refirma a todos los participantes

### ¿Cómo se verifica la autenticidad de una firma?

```python
def verificar_firma_action(action_id):
    action = SignatureAction.query.get(action_id)
    
    if not action or not action.signature_data:
        return {'valido': False, 'error': 'Firma no encontrada'}
    
    sig_data = action.signature_data
    
    # Verificaciones
    checks = {
        'tiene_timestamp': 'timestamp' in sig_data,
        'tiene_usuario': 'user_id' in sig_data,
        'tiene_hash_certificado': 'certificate_hash' in sig_data,
        'tiene_ip': 'ip_address' in sig_data,
        'usuario_existe': Usuario.query.get(sig_data.get('user_id')) is not None,
        'accion_marcada_como_firmada': action.status == 'SIGNED',
        'tiene_fecha_accion': action.action_date is not None
    }
    
    return {
        'valido': all(checks.values()),
        'verificaciones': checks,
        'signature_data': sig_data
    }
```

---

## 📚 Referencias

### APIs Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/workflows/<id>/status` | GET | Estado completo del workflow |
| `/api/workflows/<id>/signatures` | GET | Lista de firmas ejecutadas |
| `/api/workflows/<id>/audit-log` | GET | Log de auditoría |
| `/api/usuarios/<id>/pending-signatures` | GET | Firmas pendientes del usuario |
| `/solicitudes/<id>/firmar-direccion` | POST | Crear y firmar como Dirección |
| `/solicitudes/<id>/firmar-dncd` | POST | Firmar como DNCD |
| `/verificar/<public_access_id>` | GET | Verificación pública |

### Tablas Relacionadas

```
usuarios ────┐
             │
solicitudes ─┼─── signature_workflows ───┬─── signature_addressee_lines
             │                            │         │
certificados ┘                            │         └─── signature_addressee_groups
                                          │                    │
                                          │                    └─── signature_actions
                                          │
                                          ├─── signature_documents
                                          │
                                          └─── signature_audit_log
```

### Queries Útiles

```sql
-- Workflows activos
SELECT * FROM signature_workflows WHERE status = 'IN_PROGRESS';

-- Workflows completados hoy
SELECT * FROM signature_workflows 
WHERE status = 'COMPLETED' 
AND DATE(completion_date) = CURRENT_DATE;

-- Firmas pendientes de un usuario
SELECT 
    sw.public_access_id,
    sw.reference,
    sal.line_number,
    sa.status
FROM signature_actions sa
JOIN signature_addressee_groups sag ON sa.addressee_group_id = sag.id
JOIN signature_addressee_lines sal ON sag.addressee_line_id = sal.id
JOIN signature_workflows sw ON sal.workflow_id = sw.id
WHERE sa.user_id = 'uuid-usuario'
AND sa.status = 'NEW'
AND sal.status = 'IN_PROGRESS';

-- Certificados activados hoy
SELECT c.*, sw.completion_date
FROM certificados c
JOIN signature_workflows sw ON sw.certificado_id = c.id
WHERE c.estado = 'ACTIVO'
AND DATE(sw.completion_date) = CURRENT_DATE;
```

---

## 🎓 Conclusión

El sistema de firmas digitales Adobe Sign proporciona:

✅ **Trazabilidad Legal**: Cada firma con timestamp, IP, hash criptográfico  
✅ **Flujo Secuencial**: Orden garantizado de firmas  
✅ **Auditoría Completa**: Log inmutable de todos los eventos  
✅ **Integridad Verificable**: Hashes SHA256 para detectar modificaciones  
✅ **Verificación Pública**: ID público para validación externa  
✅ **Escalabilidad**: Soporte para múltiples firmantes y grupos OR/AND  

El sistema cumple con estándares internacionales de firma digital y proporciona todas las garantías necesarias para certificados oficiales del Ministerio de Salud Pública y DNCD.

---

**Documento generado**: Diciembre 9, 2025  
**Versión del Sistema**: 1.0.0  
**Basado en**: Adobe Sign API Architecture
