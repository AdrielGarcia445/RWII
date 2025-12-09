"""
Sistema de Gestión de Sustancias Controladas
Backend Flask MVP con PostgreSQL (Supabase)
Ministerio de Salud Pública y DNCD
"""

import os
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_sqlalchemy import SQLAlchemy
from supabase import Client, create_client
from werkzeug.security import check_password_hash, generate_password_hash

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.eticqhvvggccomubtgdf:intec1234567890@aws-1-us-east-2.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)

# Configuración de Supabase Storage
SUPABASE_URL = "https://eticqhvvggccomubtgdf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV0aWNxaHZ2Z2djY29tdWJ0Z2RmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDQzMjI2OCwiZXhwIjoyMDgwMDA4MjY4fQ.MbaxV6qYjIr_HHFP0eVW80GrizXijNuuddw_-BWOyNg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
STORAGE_BUCKET = "documentos"

def inicializar_bucket_storage():
    """Crear bucket de Supabase Storage si no existe"""
    try:
        # Intentar listar buckets existentes
        buckets_response = supabase.storage.list_buckets()
        
        # Verificar si el bucket ya existe
        bucket_exists = False
        if hasattr(buckets_response, '__iter__'):
            for bucket in buckets_response:
                if hasattr(bucket, 'name') and bucket.name == STORAGE_BUCKET:
                    bucket_exists = True
                    break
                elif isinstance(bucket, dict) and bucket.get('name') == STORAGE_BUCKET:
                    bucket_exists = True
                    break
        
        if not bucket_exists:
            # Intentar crear bucket público
            try:
                supabase.storage.create_bucket(
                    STORAGE_BUCKET,
                    options={"public": True}
                )
                print(f"✅ Bucket '{STORAGE_BUCKET}' creado en Supabase Storage")
            except Exception as create_error:
                # Si falla, probablemente ya existe
                print(f"✅ Bucket '{STORAGE_BUCKET}' probablemente ya existe en Supabase Storage")
        else:
            print(f"✅ Bucket '{STORAGE_BUCKET}' ya existe en Supabase Storage")
    except Exception as e:
        # No fallar el inicio del servidor si hay problemas con el bucket
        print(f"⚠️  Advertencia al inicializar bucket: {str(e)}")
        print(f"⚠️  El bucket '{STORAGE_BUCKET}' debe crearse manualmente en Supabase Dashboard")


# ============================================================================
# MODELOS DE BASE DE DATOS
# ============================================================================

class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo = db.Column(db.String, unique=True, nullable=False)
    nombre = db.Column(db.String, nullable=False)

class EstadoSolicitud(db.Model):
    __tablename__ = 'estados_solicitud'
    codigo = db.Column(db.String, primary_key=True)
    descripcion = db.Column(db.String, nullable=False)

class CatalogoServicio(db.Model):
    __tablename__ = 'catalogo_servicios'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo = db.Column(db.String, unique=True, nullable=False)
    nombre = db.Column(db.String, nullable=False)
    descripcion = db.Column(db.Text)
    costo = db.Column(db.Numeric(12, 2))
    tiempo_estimado_dias = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=True)
    requiere_dncd = db.Column(db.Boolean, default=False)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    rol_codigo = db.Column(db.String, db.ForeignKey('roles.codigo'), nullable=False)
    tipo_usuario = db.Column(db.String, nullable=False)  # PROFESIONAL, EMPRESARIAL
    documento_identidad = db.Column(db.String)
    telefono = db.Column(db.String)
    direccion = db.Column(db.String)
    razon_social = db.Column(db.String)
    rnc = db.Column(db.String)
    representante_legal = db.Column(db.String)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    rol = db.relationship('Rol', backref='usuarios')

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    numero_expediente = db.Column(db.String, unique=True, nullable=False)
    usuario_id = db.Column(db.String, db.ForeignKey('usuarios.id'), nullable=False)
    servicio_id = db.Column(db.String, db.ForeignKey('catalogo_servicios.id'), nullable=False)
    estado_codigo = db.Column(db.String, db.ForeignKey('estados_solicitud.codigo'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pagado = db.Column(db.Boolean, default=False)
    monto_pagado = db.Column(db.Numeric(12, 2), default=0)
    metodo_pago = db.Column(db.String)
    referencia_pago = db.Column(db.String)
    asignado_a_id = db.Column(db.String, db.ForeignKey('usuarios.id'))
    fecha_asignacion_upc = db.Column(db.DateTime)
    fecha_reasignacion = db.Column(db.DateTime)
    fecha_entrega = db.Column(db.DateTime)
    tipo_entrega = db.Column(db.String)
    receptor_certificado = db.Column(db.String)
    fecha_aprobacion = db.Column(db.DateTime)
    fecha_recepcion_dncd = db.Column(db.DateTime)
    fecha_aprobacion_dncd = db.Column(db.DateTime)
    fecha_resubmision = db.Column(db.DateTime)
    fecha_rechazo = db.Column(db.DateTime)
    datos_formulario = db.Column(db.JSON)
    certificado_id = db.Column(db.String, db.ForeignKey('certificados.id'))
    
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='solicitudes')
    servicio = db.relationship('CatalogoServicio', backref='solicitudes')
    estado = db.relationship('EstadoSolicitud', backref='solicitudes')
    asignado_a = db.relationship('Usuario', foreign_keys=[asignado_a_id])

class Certificado(db.Model):
    __tablename__ = 'certificados'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = db.Column(db.String)
    numero_certificado = db.Column(db.String, unique=True, nullable=False)
    tipo_servicio_codigo = db.Column(db.String, db.ForeignKey('catalogo_servicios.codigo'), nullable=False)
    nombre_archivo = db.Column(db.String, nullable=False)
    ruta = db.Column(db.String, nullable=False)
    fecha_emision = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.DateTime, nullable=False)
    firmante_direccion_id = db.Column(db.String, db.ForeignKey('usuarios.id'), nullable=False)
    firma_digital_direccion = db.Column(db.Text, nullable=False)
    firmante_dncd_id = db.Column(db.String, db.ForeignKey('usuarios.id'))
    firma_digital_dncd = db.Column(db.Text)
    fecha_firma_dncd = db.Column(db.DateTime)
    estado = db.Column(db.String, nullable=False)

class Documento(db.Model):
    __tablename__ = 'documentos'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = db.Column(db.String, db.ForeignKey('solicitudes.id'))
    certificado_id = db.Column(db.String, db.ForeignKey('certificados.id'))
    origen = db.Column(db.String, nullable=False)
    tipo = db.Column(db.String, nullable=False)
    nombre_original = db.Column(db.String)
    nombre_storage = db.Column(db.String, nullable=False)
    ruta = db.Column(db.String, nullable=False)
    fecha_subida = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    firmante_id = db.Column(db.String, db.ForeignKey('usuarios.id'))
    firma_digital = db.Column(db.Text)

class EvaluacionTecnicaUPC(db.Model):
    __tablename__ = 'evaluaciones_tecnicas_upc'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = db.Column(db.String, db.ForeignKey('solicitudes.id'), nullable=False)
    tecnico_id = db.Column(db.String, db.ForeignKey('usuarios.id'), nullable=False)
    aprobado = db.Column(db.Boolean)
    checklist = db.Column(db.JSON)
    observaciones = db.Column(db.Text)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    solicitud = db.relationship('Solicitud', backref='evaluaciones')
    tecnico = db.relationship('Usuario', backref='evaluaciones')

class ObservacionSolicitud(db.Model):
    __tablename__ = 'observaciones_solicitud'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = db.Column(db.String, db.ForeignKey('solicitudes.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_id = db.Column(db.String, db.ForeignKey('usuarios.id'), nullable=False)
    rol_codigo = db.Column(db.String, db.ForeignKey('roles.codigo'), nullable=False)
    tipo = db.Column(db.String, nullable=False)
    texto = db.Column(db.Text)
    checklist = db.Column(db.JSON)

class HistorialEstadoSolicitud(db.Model):
    __tablename__ = 'historial_estados_solicitud'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = db.Column(db.String, db.ForeignKey('solicitudes.id'), nullable=False)
    estado_codigo = db.Column(db.String, db.ForeignKey('estados_solicitud.codigo'), nullable=False)
    usuario_id = db.Column(db.String, db.ForeignKey('usuarios.id'))
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comentario = db.Column(db.Text)
    
    estado = db.relationship('EstadoSolicitud')

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = db.Column(db.String, db.ForeignKey('usuarios.id'), nullable=False)
    solicitud_id = db.Column(db.String, db.ForeignKey('solicitudes.id'))
    tipo = db.Column(db.String, nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    leida = db.Column(db.Boolean, default=False)
    fecha_lectura = db.Column(db.DateTime)

class Auditoria(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = db.Column(db.String, db.ForeignKey('solicitudes.id'))
    usuario_id = db.Column(db.String, db.ForeignKey('usuarios.id'))
    accion = db.Column(db.String, nullable=False)
    detalles = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# ============================================================================
# MODELOS DE FIRMAS DIGITALES (Adobe Sign Compatible)
# ============================================================================

class SignatureWorkflow(db.Model):
    __tablename__ = 'signature_workflows'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = db.Column(db.String, db.ForeignKey('solicitudes.id'))
    certificado_id = db.Column(db.String, db.ForeignKey('certificados.id'))
    public_access_id = db.Column(db.String(20), unique=True, nullable=False)
    reference = db.Column(db.String(100))
    subject = db.Column(db.Text)
    message = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='NOT_STARTED')
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    init_date = db.Column(db.DateTime)
    expiration_date = db.Column(db.DateTime)
    send_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    sender_user_id = db.Column(db.String, db.ForeignKey('usuarios.id'), nullable=False)
    callback_code = db.Column(db.String(100))
    workflow_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    solicitud = db.relationship('Solicitud', backref='signature_workflows')
    certificado = db.relationship('Certificado', backref='signature_workflows')
    sender = db.relationship('Usuario', foreign_keys=[sender_user_id])
    addressee_lines = db.relationship('SignatureAddresseeLine', backref='workflow', cascade='all, delete-orphan', order_by='SignatureAddresseeLine.line_number')

class SignatureAddresseeLine(db.Model):
    __tablename__ = 'signature_addressee_lines'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = db.Column(db.String, db.ForeignKey('signature_workflows.id'), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='NEW')
    started_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    groups = db.relationship('SignatureAddresseeGroup', backref='addressee_line', cascade='all, delete-orphan', order_by='SignatureAddresseeGroup.group_number')

class SignatureAddresseeGroup(db.Model):
    __tablename__ = 'signature_addressee_groups'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    addressee_line_id = db.Column(db.String, db.ForeignKey('signature_addressee_lines.id'), nullable=False)
    group_number = db.Column(db.Integer, nullable=False)
    is_or_group = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), nullable=False, default='NEW')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    actions = db.relationship('SignatureAction', backref='addressee_group', cascade='all, delete-orphan')

class SignatureAction(db.Model):
    __tablename__ = 'signature_actions'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    addressee_group_id = db.Column(db.String, db.ForeignKey('signature_addressee_groups.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('usuarios.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='NEW')
    action_date = db.Column(db.DateTime)
    reject_type = db.Column(db.String(100))
    reject_reason = db.Column(db.Text)
    signature_data = db.Column(db.JSON)
    notification_sent = db.Column(db.Boolean, default=False)
    notification_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('Usuario', backref='signature_actions')

class SignatureDocument(db.Model):
    __tablename__ = 'signature_documents'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = db.Column(db.String, db.ForeignKey('signature_workflows.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    public_access_id = db.Column(db.String(20), unique=True)
    storage_path = db.Column(db.String(500), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    version = db.Column(db.Integer, default=1)
    is_final = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    workflow = db.relationship('SignatureWorkflow', backref='documents')

class SignatureAuditLog(db.Model):
    __tablename__ = 'signature_audit_log'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = db.Column(db.String, db.ForeignKey('signature_workflows.id'))
    action_id = db.Column(db.String, db.ForeignKey('signature_actions.id'))
    user_id = db.Column(db.String, db.ForeignKey('usuarios.id'))
    event_type = db.Column(db.String(100), nullable=False)
    event_data = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# ============================================================================
# DECORADORES Y UTILIDADES
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'rol_codigo' not in session or session['rol_codigo'] not in roles:
                return jsonify({'error': 'No tiene permisos para esta acción'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def registrar_auditoria(accion, solicitud_id=None, detalles=None):
    """Registra una acción en la auditoría"""
    auditoria = Auditoria(
        solicitud_id=solicitud_id,
        usuario_id=session.get('user_id'),
        accion=accion,
        detalles=detalles
    )
    db.session.add(auditoria)
    db.session.commit()

def crear_notificacion(usuario_id, tipo, mensaje, solicitud_id=None):
    """Crea una notificación para un usuario"""
    notificacion = Notificacion(
        usuario_id=usuario_id,
        solicitud_id=solicitud_id,
        tipo=tipo,
        mensaje=mensaje
    )
    db.session.add(notificacion)
    db.session.commit()

def generar_numero_expediente():
    """Genera un número de expediente único"""
    year = datetime.now().year
    count = Solicitud.query.filter(
        db.func.extract('year', Solicitud.fecha_creacion) == year
    ).count() + 1
    return f"SGC-{year}-{count:06d}"

def cambiar_estado_solicitud(solicitud_id, nuevo_estado, comentario=None):
    """Cambia el estado de una solicitud y registra el historial"""
    solicitud = Solicitud.query.get(solicitud_id)
    if solicitud:
        solicitud.estado_codigo = nuevo_estado
        solicitud.fecha_actualizacion = datetime.utcnow()
        
        historial = HistorialEstadoSolicitud(
            solicitud_id=solicitud_id,
            estado_codigo=nuevo_estado,
            usuario_id=session.get('user_id'),
            comentario=comentario
        )
        db.session.add(historial)
        db.session.commit()
        return True
    return False

# ============================================================================
# UTILIDADES DE FIRMA DIGITAL
# ============================================================================

def generar_id_publico(longitud=16):
    """Genera un ID público único tipo Adobe Sign (XXXX-XXXX-XXXX-XXXX)"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    segments = []
    for _ in range(4):
        segment = ''.join(random.choices(chars, k=4))
        segments.append(segment)
    return '-'.join(segments)

def generar_hash_certificado(data):
    """Genera hash SHA256 de datos para firma digital"""
    import hashlib
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def crear_workflow_firma_certificado(solicitud_id, certificado_id, requiere_dncd=True):
    """
    Crea un workflow de firma digital tipo Adobe Sign
    
    Estructura:
    - Línea 1: Dirección firma primero
    - Línea 2: DNCD firma después (solo si requiere_dncd=True)
    """
    solicitud = Solicitud.query.get(solicitud_id)
    certificado = Certificado.query.get(certificado_id)
    
    if not solicitud or not certificado:
        raise ValueError("Solicitud o certificado no encontrado")
    
    # Crear workflow principal
    workflow = SignatureWorkflow(
        solicitud_id=solicitud_id,
        certificado_id=certificado_id,
        public_access_id=generar_id_publico(),
        reference=solicitud.numero_expediente,
        subject=f'Firma de Certificado {certificado.numero_certificado}',
        message=f'Certificado para solicitud {solicitud.numero_expediente} - {solicitud.servicio.nombre}',
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
    
    # Línea 1: Firma de Dirección
    line1 = SignatureAddresseeLine(
        workflow_id=workflow.id,
        line_number=1,
        status='IN_PROGRESS',
        started_date=datetime.utcnow()
    )
    db.session.add(line1)
    db.session.flush()
    
    group1 = SignatureAddresseeGroup(
        addressee_line_id=line1.id,
        group_number=1,
        is_or_group=False,
        status='IN_PROGRESS'
    )
    db.session.add(group1)
    db.session.flush()
    
    action_direccion = SignatureAction(
        addressee_group_id=group1.id,
        user_id=session.get('user_id'),
        action_type='SIGN',
        status='NEW'
    )
    db.session.add(action_direccion)
    
    # Línea 2: Firma de DNCD (solo si requiere)
    if requiere_dncd:
        line2 = SignatureAddresseeLine(
            workflow_id=workflow.id,
            line_number=2,
            status='NEW'
        )
        db.session.add(line2)
        db.session.flush()
        
        group2 = SignatureAddresseeGroup(
            addressee_line_id=line2.id,
            group_number=1,
            is_or_group=False
        )
        db.session.add(group2)
        db.session.flush()
        
        # Obtener usuarios DNCD activos
        usuarios_dncd = Usuario.query.filter_by(rol_codigo='DNCD', activo=True).all()
        
        # Crear acción para cada usuario DNCD (grupo OR - solo uno necesita firmar)
        if len(usuarios_dncd) > 1:
            group2.is_or_group = True
        
        for usuario_dncd in usuarios_dncd:
            action_dncd = SignatureAction(
                addressee_group_id=group2.id,
                user_id=usuario_dncd.id,
                action_type='SIGN',
                status='NEW'
            )
            db.session.add(action_dncd)
    
    db.session.commit()
    
    # Registrar en auditoría de firmas
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
        ip_address=request.remote_addr if request else None,
        user_agent=request.user_agent.string if request else None
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return workflow

def firmar_documento_workflow(workflow_id, user_id, signature_type='ELECTRONIC'):
    """
    Ejecuta la firma de un documento en el workflow
    
    Proceso:
    1. Busca acción pendiente del usuario
    2. Genera datos de la firma (timestamp, hash, IP, etc.)
    3. Actualiza acción como SIGNED
    4. Verifica si el grupo está completo
    5. Verifica si la línea está completa
    6. Si es última línea, marca workflow como COMPLETED y certificado como ACTIVO
    7. Si hay siguiente línea, la activa y notifica a firmantes
    """
    workflow = SignatureWorkflow.query.get(workflow_id)
    if not workflow:
        raise ValueError("Workflow no encontrado")
    
    # Buscar acción pendiente del usuario en la línea actual
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
        raise ValueError("No hay acción de firma pendiente para este usuario en el workflow")
    
    # Generar datos de la firma
    usuario = Usuario.query.get(user_id)
    certificado = Certificado.query.get(workflow.certificado_id)
    
    signature_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'user_name': usuario.name,
        'user_email': usuario.email,
        'user_rol': usuario.rol_codigo,
        'signature_type': signature_type,
        'certificate_hash': generar_hash_certificado(f'{certificado.numero_certificado}{datetime.utcnow().isoformat()}'),
        'document_hash': certificado.ruta,  # En producción, calcular hash del archivo real
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.user_agent.string if request else None,
        'workflow_public_id': workflow.public_access_id
    }
    
    # Actualizar acción
    action.status = 'SIGNED'
    action.action_date = datetime.utcnow()
    action.signature_data = signature_data
    
    # Actualizar grupo
    group = action.addressee_group
    if group.is_or_group:
        # Grupo OR: con una firma es suficiente
        group.status = 'COMPLETED'
    else:
        # Grupo AND: todas las acciones deben estar firmadas
        if all(a.status in ['SIGNED', 'APPROVED'] for a in group.actions):
            group.status = 'COMPLETED'
    
    # Actualizar línea
    line = group.addressee_line
    if all(g.status == 'COMPLETED' for g in line.groups):
        line.status = 'COMPLETED'
        line.completed_date = datetime.utcnow()
        
        # Verificar si hay siguiente línea
        siguiente_linea = SignatureAddresseeLine.query.filter_by(
            workflow_id=workflow_id,
            line_number=line.line_number + 1
        ).first()
        
        if siguiente_linea:
            # Activar siguiente línea
            siguiente_linea.status = 'IN_PROGRESS'
            siguiente_linea.started_date = datetime.utcnow()
            
            # Notificar a firmantes de la siguiente línea
            for group in siguiente_linea.groups:
                for act in group.actions:
                    crear_notificacion(
                        act.user_id,
                        'FIRMA_PENDIENTE',
                        f'Tiene una firma pendiente para el certificado {certificado.numero_certificado}',
                        workflow.solicitud_id
                    )
                    act.notification_sent = True
                    act.notification_date = datetime.utcnow()
            
            # Auditoría: siguiente línea activada
            audit_log = SignatureAuditLog(
                workflow_id=workflow_id,
                user_id=user_id,
                event_type='LINE_COMPLETED_NEXT_ACTIVATED',
                event_data={
                    'completed_line': line.line_number,
                    'activated_line': siguiente_linea.line_number
                },
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string if request else None
            )
            db.session.add(audit_log)
        else:
            # Última línea completada → workflow completo
            workflow.status = 'COMPLETED'
            workflow.completion_date = datetime.utcnow()
            
            # Activar certificado
            if certificado:
                certificado.estado = 'ACTIVO'
            
            # Auditoría: workflow completado
            audit_log = SignatureAuditLog(
                workflow_id=workflow_id,
                user_id=user_id,
                event_type='WORKFLOW_COMPLETED',
                event_data={
                    'certificado_id': certificado.id if certificado else None,
                    'total_firmas': sum(len(g.actions) for l in workflow.addressee_lines for g in l.groups)
                },
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string if request else None
            )
            db.session.add(audit_log)
    
    # Auditoría: firma ejecutada
    audit_log = SignatureAuditLog(
        workflow_id=workflow_id,
        action_id=action.id,
        user_id=user_id,
        event_type='DOCUMENT_SIGNED',
        event_data=signature_data,
        ip_address=request.remote_addr if request else None,
        user_agent=request.user_agent.string if request else None
    )
    db.session.add(audit_log)
    
    db.session.commit()
    
    return {
        'success': True,
        'workflow_status': workflow.status,
        'certificado_estado': certificado.estado if certificado else None,
        'signature_data': signature_data
    }

# ============================================================================
# RUTAS DE AUTENTICACIÓN
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        usuario = Usuario.query.filter_by(email=email, activo=True).first()
        
        if usuario and check_password_hash(usuario.password_hash, password):
            session['user_id'] = usuario.id
            session['name'] = usuario.name
            session['rol_codigo'] = usuario.rol_codigo
            session['tipo_usuario'] = usuario.tipo_usuario
            
            registrar_auditoria('LOGIN', detalles=f'Usuario {email} inició sesión')
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            return redirect(url_for('dashboard'))
        
        if request.is_json:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        return render_template('login.html', error='Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    registrar_auditoria('LOGOUT', detalles=f'Usuario cerró sesión')
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Validar que el email no exista
        if Usuario.query.filter_by(email=data.get('email')).first():
            if request.is_json:
                return jsonify({'error': 'El email ya está registrado'}), 400
            return render_template('register.html', error='El email ya está registrado')
        
        # Crear nuevo usuario
        usuario = Usuario(
            name=data.get('name'),
            email=data.get('email'),
            password_hash=generate_password_hash(data.get('password')),
            rol_codigo='USUARIO',  # Por defecto
            tipo_usuario=data.get('tipo_usuario', 'PROFESIONAL'),
            documento_identidad=data.get('documento_identidad'),
            telefono=data.get('telefono'),
            direccion=data.get('direccion'),
            razon_social=data.get('razon_social'),
            rnc=data.get('rnc'),
            representante_legal=data.get('representante_legal')
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        registrar_auditoria('REGISTRO_USUARIO', detalles=f'Nuevo usuario registrado: {usuario.email}')
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Usuario registrado exitosamente'})
        return redirect(url_for('login'))
    
    return render_template('register.html')

# ============================================================================
# RUTAS DEL DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    rol = session.get('rol_codigo')
    
    if rol == 'USUARIO':
        solicitudes = Solicitud.query.filter_by(usuario_id=session['user_id']).order_by(
            Solicitud.fecha_creacion.desc()
        ).all()
        return render_template('dashboard.html', solicitudes=solicitudes)
    elif rol == 'VUS':
        # Redirigir a dashboard especializado de VUS
        return redirect(url_for('vus_dashboard'))
    elif rol == 'TECNICO_UPC':
        solicitudes = Solicitud.query.filter(
            Solicitud.estado_codigo.in_(['EN_EVALUACION', 'ASIGNADO_UPC'])
        ).order_by(Solicitud.fecha_creacion.desc()).all()
    elif rol == 'ENCARGADO_UPC':
        # El encargado ve todas las solicitudes de UPC (asignadas, en evaluación y aprobadas)
        solicitudes = Solicitud.query.filter(
            Solicitud.estado_codigo.in_(['ASIGNADO_UPC', 'EN_EVALUACION', 'APROBADO_UPC'])
        ).order_by(Solicitud.fecha_creacion.desc()).all()
    elif rol == 'DIRECCION':
        solicitudes = Solicitud.query.filter(
            Solicitud.estado_codigo.in_(['APROBADO_UPC', 'PENDIENTE_FIRMA_DIRECCION'])
        ).order_by(Solicitud.fecha_creacion.desc()).all()
    elif rol == 'DNCD':
        solicitudes = Solicitud.query.filter(
            Solicitud.estado_codigo.in_(['ENVIADO_DNCD', 'PENDIENTE_FIRMA_DNCD'])
        ).order_by(Solicitud.fecha_creacion.desc()).all()
    else:
        solicitudes = Solicitud.query.order_by(Solicitud.fecha_creacion.desc()).all()
    
    return render_template('dashboard.html', solicitudes=solicitudes)

# ============================================================================
# RUTAS DE SOLICITUDES
# ============================================================================

@app.route('/solicitudes/nueva', methods=['GET', 'POST'])
@login_required
@role_required('USUARIO')
def nueva_solicitud():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        solicitud = Solicitud(
            numero_expediente=generar_numero_expediente(),
            usuario_id=session['user_id'],
            servicio_id=data.get('servicio_id'),
            estado_codigo='RECIBIDO',
            datos_formulario=data.get('datos_formulario'),
            pagado=data.get('pagado', False),
            monto_pagado=data.get('monto_pagado', 0),
            referencia_pago=data.get('referencia_pago')
        )
        
        db.session.add(solicitud)
        db.session.commit()
        
        # Registrar historial
        historial = HistorialEstadoSolicitud(
            solicitud_id=solicitud.id,
            estado_codigo='RECIBIDO',
            usuario_id=session['user_id']
        )
        db.session.add(historial)
        
        registrar_auditoria('CREAR_SOLICITUD', solicitud.id, f'Solicitud {solicitud.numero_expediente} creada')
        
        # Procesar archivos adjuntos si existen
        if 'documentos' in request.files:
            archivos = request.files.getlist('documentos')
            for archivo in archivos:
                if archivo and archivo.filename:
                    # Validar extensión
                    extensiones_permitidas = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
                    extension = archivo.filename.rsplit('.', 1)[1].lower() if '.' in archivo.filename else ''
                    
                    if extension in extensiones_permitidas:
                        try:
                            # Generar nombre único
                            nombre_storage = f"solicitud_{solicitud.id}/{str(uuid.uuid4())}.{extension}"
                            
                            # Leer contenido del archivo
                            file_content = archivo.read()
                            
                            # Subir a Supabase Storage
                            supabase.storage.from_(STORAGE_BUCKET).upload(
                                path=nombre_storage,
                                file=file_content,
                                file_options={"content-type": archivo.content_type or "application/octet-stream"}
                            )
                            
                            # Obtener URL pública
                            file_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(nombre_storage)
                            
                            # Registrar documento en BD
                            documento = Documento(
                                solicitud_id=solicitud.id,
                                origen='USUARIO',
                                tipo='DOCUMENTO_SOPORTE',
                                nombre_original=archivo.filename,
                                nombre_storage=nombre_storage,
                                ruta=file_url
                            )
                            db.session.add(documento)
                            
                        except Exception as e:
                            print(f"Error al subir documento {archivo.filename}: {str(e)}")
            
            # Guardar todos los documentos
            db.session.commit()
        
        # Notificar a VUS
        usuarios_vus = Usuario.query.filter_by(rol_codigo='VUS', activo=True).all()
        for vus in usuarios_vus:
            crear_notificacion(
                vus.id,
                'NUEVA_SOLICITUD',
                f'Nueva solicitud {solicitud.numero_expediente} recibida',
                solicitud.id
            )
        
        if request.is_json:
            return jsonify({'success': True, 'solicitud_id': solicitud.id, 'numero_expediente': solicitud.numero_expediente})
        return redirect(url_for('ver_solicitud', solicitud_id=solicitud.id))
    
    servicios = CatalogoServicio.query.filter_by(activo=True).all()
    return render_template('nueva_solicitud.html', servicios=servicios)

@app.route('/solicitudes/<solicitud_id>')
@login_required
def ver_solicitud(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # Verificar permisos
    if session['rol_codigo'] == 'USUARIO' and solicitud.usuario_id != session['user_id']:
        return jsonify({'error': 'No tiene permisos para ver esta solicitud'}), 403
    
    historial = HistorialEstadoSolicitud.query.filter_by(
        solicitud_id=solicitud_id
    ).order_by(HistorialEstadoSolicitud.fecha.desc()).all()
    
    observaciones = ObservacionSolicitud.query.filter_by(
        solicitud_id=solicitud_id
    ).order_by(ObservacionSolicitud.fecha.desc()).all()
    
    documentos = Documento.query.filter_by(solicitud_id=solicitud_id).all()
    
    return render_template(
        'ver_solicitud.html',
        solicitud=solicitud,
        historial=historial,
        observaciones=observaciones,
        documentos=documentos
    )

# ============================================================================
# RUTAS DE EVALUACIÓN (VUS)
# ============================================================================

@app.route('/vus/solicitudes')
@login_required
@role_required('VUS')
def vus_dashboard():
    """Dashboard especializado para Ventanilla Única"""
    estado_filtro = request.args.get('estado')
    
    # Solicitudes que VUS debe revisar
    query = Solicitud.query.filter(
        Solicitud.estado_codigo.in_(['RECIBIDO', 'DEVUELTO_VUS'])
    )
    
    if estado_filtro:
        query = query.filter_by(estado_codigo=estado_filtro)
    
    solicitudes = query.order_by(Solicitud.fecha_creacion.desc()).all()
    
    # Estadísticas
    pendientes = Solicitud.query.filter_by(estado_codigo='RECIBIDO').count()
    devueltas = Solicitud.query.filter_by(estado_codigo='DEVUELTO_VUS').count()
    
    # Aprobadas hoy por VUS
    from datetime import date
    aprobadas_hoy = HistorialEstadoSolicitud.query.filter(
        HistorialEstadoSolicitud.estado_codigo == 'ASIGNADO_UPC',
        db.func.date(HistorialEstadoSolicitud.fecha) == date.today()
    ).count()
    
    # Certificados listos para entrega
    para_entrega = Solicitud.query.filter_by(estado_codigo='APROBADO_FINAL').count()
    
    return render_template('vus/dashboard.html', 
                         solicitudes=solicitudes,
                         pendientes=pendientes,
                         devueltas=devueltas,
                         aprobadas_hoy=aprobadas_hoy,
                         para_entrega=para_entrega)

def obtener_requisitos_por_servicio(codigo_servicio):
    """Retorna los requisitos específicos según el tipo de servicio"""
    requisitos = {
        'CERT_CLASE_A': {
            'tipo': 'Certificado Clase A - Profesionales de Salud',
            'validez': '3 años',
            'costo': 'RD$ 150.00',
            'campos_requeridos': [
                {'campo': 'profesion', 'nombre': 'Profesión (Médico/Veterinario/Odontólogo)'},
                {'campo': 'cedula_profesional', 'nombre': 'Cédula de Identidad'},
                {'campo': 'numero_exequatur', 'nombre': 'Número de Exequátur'},
                {'campo': 'universidad', 'nombre': 'Universidad de Graduación'}
            ],
            'documentos_requeridos': [
                'Copia de cédula de identidad',
                'Copia del título universitario',
                'Copia del exequátur',
                'Comprobante de pago RD$150.00 (BanReservas)'
            ]
        },
        'CERT_CLASE_B_PRIVADO': {
            'tipo': 'Certificado Clase B - Establecimientos Privados',
            'validez': '1 año',
            'costo': 'RD$ 500.00 por actividad',
            'campos_requeridos': [
                {'campo': 'tipo_establecimiento', 'nombre': 'Tipo de Establecimiento'},
                {'campo': 'nombre_establecimiento', 'nombre': 'Nombre del Establecimiento'},
                {'campo': 'rnc_establecimiento', 'nombre': 'RNC del Establecimiento'},
                {'campo': 'direccion_establecimiento', 'nombre': 'Dirección del Establecimiento'},
                {'campo': 'nombre_representante', 'nombre': 'Nombre del Representante Legal'},
                {'campo': 'cedula_representante', 'nombre': 'Cédula del Representante Legal'},
                {'campo': 'nombre_director', 'nombre': 'Nombre del Director Técnico'},
                {'campo': 'cedula_director', 'nombre': 'Cédula del Director Técnico'},
                {'campo': 'exequatur_director', 'nombre': 'Exequátur del Director Técnico'}
            ],
            'documentos_requeridos': [
                'Cédulas del representante legal y director técnico',
                'Títulos universitarios',
                'Exequátur del director técnico',
                'Permiso de habilitación vigente del establecimiento',
                'Estatutos de la empresa (si aplica)',
                'Comprobante de pago RD$500.00 por cada actividad'
            ]
        },
        'CERT_CLASE_B_PUBLICO': {
            'tipo': 'Certificado Clase B - Instituciones Públicas',
            'validez': '1 año',
            'costo': 'Exonerado',
            'campos_requeridos': [
                {'campo': 'nombre_institucion', 'nombre': 'Nombre de la Institución'},
                {'campo': 'direccion_institucion', 'nombre': 'Dirección de la Institución'},
                {'campo': 'nombre_representante_pub', 'nombre': 'Nombre del Representante'},
                {'campo': 'cargo_representante', 'nombre': 'Cargo del Representante'},
                {'campo': 'cedula_representante_pub', 'nombre': 'Cédula del Representante'},
                {'campo': 'nombre_farmaceutico', 'nombre': 'Nombre del Farmacéutico Responsable'},
                {'campo': 'cedula_farmaceutico', 'nombre': 'Cédula del Farmacéutico'},
                {'campo': 'exequatur_farmaceutico', 'nombre': 'Exequátur del Farmacéutico'}
            ],
            'documentos_requeridos': [
                'Cédulas del representante y farmacéutico responsable',
                'Títulos universitarios',
                'Exequátur del farmacéutico',
                'Certificado de habilitación (si está disponible)'
            ]
        },
        'PERMISO_IMP_MATERIA_PRIMA': {
            'tipo': 'Permiso de Importación de Materia Prima',
            'validez': '180 días',
            'costo': 'Gratuito',
            'campos_requeridos': [
                {'campo': 'nombre_importador', 'nombre': 'Nombre del Importador'},
                {'campo': 'nombre_exportador', 'nombre': 'Nombre del Exportador'},
                {'campo': 'pais_origen', 'nombre': 'País de Origen'},
                {'campo': 'sustancia_controlada', 'nombre': 'Sustancia Controlada'},
                {'campo': 'cantidad_importacion', 'nombre': 'Cantidad a Importar'},
                {'campo': 'puerto_entrada', 'nombre': 'Puerto de Entrada'},
                {'campo': 'via_transporte', 'nombre': 'Vía de Transporte'}
            ],
            'documentos_requeridos': [
                'Carta de solicitud firmada',
                'Factura proforma',
                'Autorización de DNCD',
                'Factura comercial (Fase 2)',
                'Certificados de análisis (Fase 2)',
                'Certificados de BPM - productos semielaborados (Fase 2)',
                'Certificado de libre venta - productos semielaborados (Fase 2)'
            ]
        },
        'PERMISO_IMP_MEDICAMENTOS': {
            'tipo': 'Permiso de Importación de Medicamentos con Sustancia Controlada',
            'validez': '180 días',
            'costo': 'Gratuito',
            'campos_requeridos': [
                {'campo': 'nombre_importador_med', 'nombre': 'Nombre del Importador'},
                {'campo': 'nombre_exportador_med', 'nombre': 'Nombre del Exportador'},
                {'campo': 'pais_origen_med', 'nombre': 'País de Origen'},
                {'campo': 'nombre_medicamento', 'nombre': 'Nombre del Medicamento'},
                {'campo': 'sustancia_controlada_med', 'nombre': 'Sustancia Controlada'},
                {'campo': 'presentacion', 'nombre': 'Presentación'},
                {'campo': 'cantidad_medicamento', 'nombre': 'Cantidad a Importar'},
                {'campo': 'registro_sanitario', 'nombre': 'Número de Registro Sanitario'},
                {'campo': 'numero_clase_b', 'nombre': 'Número de Certificado Clase B Vigente'},
                {'campo': 'puerto_entrada_med', 'nombre': 'Puerto de Entrada'},
                {'campo': 'via_transporte_med', 'nombre': 'Vía de Transporte'}
            ],
            'documentos_requeridos': [
                'Carta de solicitud firmada',
                'Certificado Clase B vigente',
                'Registro Sanitario del medicamento',
                'Factura proforma',
                'Autorización de DNCD'
            ]
        }
    }
    
    return requisitos.get(codigo_servicio, {
        'tipo': 'Servicio General',
        'validez': 'Variable',
        'costo': 'Variable',
        'campos_requeridos': [],
        'documentos_requeridos': []
    })

@app.route('/vus/solicitudes/<solicitud_id>/revisar')
@login_required
@role_required('VUS')
def vus_revisar_solicitud(solicitud_id):
    """Página de revisión detallada de solicitud para VUS"""
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # Verificar que esté en estado que VUS puede revisar
    if solicitud.estado_codigo not in ['RECIBIDO', 'DEVUELTO_VUS']:
        return redirect(url_for('vus_dashboard'))
    
    documentos = Documento.query.filter_by(solicitud_id=solicitud_id).all()
    
    # Obtener requisitos específicos del servicio
    requisitos = obtener_requisitos_por_servicio(solicitud.servicio.codigo)
    
    # Verificar cumplimiento de campos requeridos
    datos_formulario = solicitud.datos_formulario or {}
    
    # Asegurarse de que datos_formulario sea un diccionario
    if isinstance(datos_formulario, str):
        try:
            import json
            datos_formulario = json.loads(datos_formulario)
        except:
            datos_formulario = {}
    elif not isinstance(datos_formulario, dict):
        datos_formulario = {}
    
    campos_cumplidos = []
    campos_faltantes = []
    
    # Verificar que requisitos tenga la estructura correcta
    if isinstance(requisitos, dict) and 'campos_requeridos' in requisitos:
        for campo in requisitos['campos_requeridos']:
            # Asegurarse de que campo sea un diccionario
            if isinstance(campo, dict):
                nombre_campo = campo.get('campo', '')
                valor = datos_formulario.get(nombre_campo, '')
                if valor and str(valor).strip():
                    campos_cumplidos.append(campo)
                else:
                    campos_faltantes.append(campo)
    
    return render_template('vus/revisar_solicitud.html', 
                         solicitud=solicitud,
                         documentos=documentos,
                         requisitos=requisitos,
                         campos_cumplidos=campos_cumplidos,
                         campos_faltantes=campos_faltantes,
                         datos_formulario=datos_formulario)

@app.route('/solicitudes/<solicitud_id>/evaluar-vus', methods=['POST'])
@login_required
@role_required('VUS')
def evaluar_vus(solicitud_id):
    data = request.get_json() if request.is_json else request.form
    cumple = data.get('cumple') == 'true' or data.get('cumple') is True
    observaciones_texto = data.get('observaciones', '')
    checklist_data = data.get('checklist', {})
    
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    if cumple:
        cambiar_estado_solicitud(solicitud_id, 'ASIGNADO_UPC', 'Documentación conforme - Enviado a UPC')
        
        # Crear observación con checklist de verificación
        observacion = ObservacionSolicitud(
            solicitud_id=solicitud_id,
            usuario_id=session['user_id'],
            rol_codigo='VUS',
            tipo='APROBACION_VUS',
            texto=observaciones_texto or 'Documentación verificada y conforme',
            checklist=checklist_data
        )
        db.session.add(observacion)
        
        # Notificar a técnicos UPC
        tecnicos_upc = Usuario.query.filter_by(rol_codigo='TECNICO_UPC', activo=True).all()
        for tecnico in tecnicos_upc:
            crear_notificacion(
                tecnico.id,
                'SOLICITUD_ASIGNADA',
                f'Solicitud {solicitud.numero_expediente} asignada para evaluación técnica',
                solicitud_id
            )
        
        # Notificar al usuario
        crear_notificacion(
            solicitud.usuario_id,
            'SOLICITUD_APROBADA_VUS',
            f'Su solicitud {solicitud.numero_expediente} ha sido aprobada por Ventanilla Única y enviada a evaluación técnica',
            solicitud_id
        )
    else:
        if not observaciones_texto.strip():
            return jsonify({'success': False, 'error': 'Debe proporcionar observaciones para devolver la solicitud'}), 400
        
        cambiar_estado_solicitud(solicitud_id, 'DEVUELTO_VUS', 'Documentación incompleta - Requiere correcciones')
        
        # Crear observación con detalles de lo que falta
        observacion = ObservacionSolicitud(
            solicitud_id=solicitud_id,
            usuario_id=session['user_id'],
            rol_codigo='VUS',
            tipo='DEVOLUCION',
            texto=observaciones_texto
        )
        db.session.add(observacion)
        
        # Notificar al usuario
        crear_notificacion(
            solicitud.usuario_id,
            'SOLICITUD_DEVUELTA',
            f'Su solicitud {solicitud.numero_expediente} ha sido devuelta. Favor revisar observaciones y completar la documentación faltante.',
            solicitud_id
        )
    
    db.session.commit()
    registrar_auditoria(
        'EVALUAR_VUS', 
        solicitud_id, 
        f'Evaluación VUS: {"Aprobado - Enviado a UPC" if cumple else "Devuelto al usuario"}. Observaciones: {observaciones_texto[:100]}'
    )
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('dashboard'))

# ============================================================================
# RUTAS DE EVALUACIÓN TÉCNICA (UPC)
# ============================================================================

@app.route('/solicitudes/<solicitud_id>/evaluar-upc', methods=['POST'])
@login_required
@role_required('TECNICO_UPC', 'ENCARGADO_UPC')
def evaluar_upc(solicitud_id):
    data = request.get_json() if request.is_json else request.form
    aprobado = data.get('aprobado') == 'true' or data.get('aprobado') is True
    
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # Crear evaluación técnica
    evaluacion = EvaluacionTecnicaUPC(
        solicitud_id=solicitud_id,
        tecnico_id=session['user_id'],
        aprobado=aprobado,
        checklist=data.get('checklist'),
        observaciones=data.get('observaciones')
    )
    db.session.add(evaluacion)
    
    if aprobado:
        cambiar_estado_solicitud(solicitud_id, 'APROBADO_UPC', 'Evaluación técnica aprobada')
        solicitud.fecha_aprobacion = datetime.utcnow()
        
        # Notificar a Dirección
        directores = Usuario.query.filter_by(rol_codigo='DIRECCION', activo=True).all()
        for director in directores:
            crear_notificacion(
                director.id,
                'PENDIENTE_FIRMA',
                f'Solicitud {solicitud.numero_expediente} aprobada por UPC - Pendiente de firma',
                solicitud_id
            )
    else:
        cambiar_estado_solicitud(solicitud_id, 'RECHAZADO_UPC', 'Solicitud no cumple requisitos técnicos')
        solicitud.fecha_rechazo = datetime.utcnow()
        
        # Notificar al usuario
        crear_notificacion(
            solicitud.usuario_id,
            'SOLICITUD_RECHAZADA',
            f'Su solicitud {solicitud.numero_expediente} ha sido rechazada. Revisar observaciones.',
            solicitud_id
        )
    
    db.session.commit()
    registrar_auditoria('EVALUAR_UPC', solicitud_id, f'Evaluación UPC: {"Aprobado" if aprobado else "Rechazado"}')
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('dashboard'))

# ============================================================================
# RUTAS DE FIRMA Y APROBACIÓN (DIRECCIÓN)
# ============================================================================

@app.route('/solicitudes/<solicitud_id>/firmar-dncd', methods=['POST'])
@login_required
@role_required('DNCD')
def firmar_dncd(solicitud_id):
    """Firma de DNCD usando workflow de firma digital tipo Adobe Sign"""
    data = request.get_json() if request.is_json else request.form
    
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # Verificar que esté en estado correcto
    if solicitud.estado_codigo not in ['ENVIADO_DNCD', 'PENDIENTE_FIRMA_DNCD']:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Estado de solicitud no válido'}), 400
        return redirect(url_for('dashboard'))
    
    try:
        # 1. Buscar workflow activo para esta solicitud
        workflow = SignatureWorkflow.query.filter_by(
            solicitud_id=solicitud_id,
            status='IN_PROGRESS'
        ).first()
        
        if not workflow:
            raise ValueError('No hay workflow de firma activo para esta solicitud')
        
        # 2. Ejecutar firma DNCD en el workflow
        resultado_firma = firmar_documento_workflow(
            workflow_id=workflow.id,
            user_id=session['user_id'],
            signature_type='ELECTRONIC'
        )
        
        # 3. Actualizar certificado con datos de firma DNCD
        if solicitud.certificado_id:
            certificado = Certificado.query.get(solicitud.certificado_id)
            if certificado:
                certificado.firmante_dncd_id = session['user_id']
                certificado.firma_digital_dncd = str(resultado_firma['signature_data'])
                certificado.fecha_firma_dncd = datetime.utcnow()
                # El estado del certificado ya fue actualizado a ACTIVO por firmar_documento_workflow()
        
        # 4. Cambiar estado de solicitud
        cambiar_estado_solicitud(solicitud_id, 'APROBADO_FINAL', 'Aprobado y firmado por DNCD')
        solicitud.fecha_aprobacion_dncd = datetime.utcnow()
        
        # 5. Notificar al usuario
        crear_notificacion(
            solicitud.usuario_id,
            'CERTIFICADO_LISTO',
            f'Su certificado está listo para retiro en Ventanilla Única',
            solicitud_id
        )
        
        # 6. Notificar a VUS para entrega
        usuarios_vus = Usuario.query.filter_by(rol_codigo='VUS', activo=True).all()
        for vus in usuarios_vus:
            crear_notificacion(
                vus.id,
                'CERTIFICADO_PARA_ENTREGA',
                f'Certificado {solicitud.numero_expediente} listo para entrega',
                solicitud_id
            )
        
        db.session.commit()
        registrar_auditoria('FIRMAR_DNCD', solicitud_id, f'Solicitud firmada por DNCD - Workflow {workflow.public_access_id}')
        
        if request.is_json:
            return jsonify({
                'success': True,
                'workflow_id': workflow.id,
                'workflow_public_id': workflow.public_access_id,
                'workflow_status': workflow.status,
                'certificado_estado': certificado.estado if certificado else None,
                'signature_data': resultado_firma['signature_data']
            })
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return redirect(url_for('dashboard'))

# ============================================================================
# RUTAS DE ENTREGA (VUS)
# ============================================================================

@app.route('/solicitudes/<solicitud_id>/entregar', methods=['POST'])
@login_required
@role_required('VUS')
def entregar_certificado(solicitud_id):
    data = request.get_json() if request.is_json else request.form
    
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    cambiar_estado_solicitud(solicitud_id, 'ENTREGADO', 'Certificado entregado')
    solicitud.fecha_entrega = datetime.utcnow()
    solicitud.tipo_entrega = data.get('tipo_entrega', 'FISICA')
    solicitud.receptor_certificado = data.get('receptor_certificado')
    
    db.session.commit()
    registrar_auditoria('ENTREGAR_CERTIFICADO', solicitud_id, f'Certificado entregado a {data.get("receptor_certificado")}')
    
    # Notificar al usuario
    crear_notificacion(
        solicitud.usuario_id,
        'CERTIFICADO_ENTREGADO',
        f'Su certificado {solicitud.numero_expediente} ha sido entregado',
        solicitud_id
    )
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('dashboard'))

# ============================================================================
# RUTAS DE RESUBMISIÓN
# ============================================================================

@app.route('/solicitudes/<solicitud_id>/resubmitir', methods=['POST'])
@login_required
@role_required('USUARIO')
def resubmitir_solicitud(solicitud_id):
    data = request.get_json() if request.is_json else request.form
    
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # Verificar que sea el propietario
    if solicitud.usuario_id != session['user_id']:
        return jsonify({'error': 'No tiene permisos para resubmitir esta solicitud'}), 403
    
    # Verificar que esté en estado devuelto o rechazado
    if solicitud.estado_codigo not in ['DEVUELTO_VUS', 'RECHAZADO_UPC']:
        return jsonify({'error': 'Esta solicitud no puede ser resubmitida'}), 400
    
    cambiar_estado_solicitud(solicitud_id, 'RECIBIDO', 'Solicitud resubmitida con correcciones')
    solicitud.fecha_resubmision = datetime.utcnow()
    solicitud.datos_formulario = data.get('datos_formulario', solicitud.datos_formulario)
    
    db.session.commit()
    registrar_auditoria('RESUBMITIR_SOLICITUD', solicitud_id, 'Solicitud resubmitida')
    
    # Notificar a VUS
    usuarios_vus = Usuario.query.filter_by(rol_codigo='VUS', activo=True).all()
    for vus in usuarios_vus:
        crear_notificacion(
            vus.id,
            'SOLICITUD_RESUBMITIDA',
            f'Solicitud {solicitud.numero_expediente} resubmitida para revisión',
            solicitud_id
        )
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('ver_solicitud', solicitud_id=solicitud_id))

# ============================================================================
# API DE CONSULTAS
# ============================================================================

@app.route('/api/solicitudes')
@login_required
def api_solicitudes():
    """API para listar solicitudes según rol"""
    rol = session.get('rol_codigo')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    estado = request.args.get('estado')
    
    query = Solicitud.query
    
    if rol == 'USUARIO':
        query = query.filter_by(usuario_id=session['user_id'])
    elif rol == 'VUS':
        query = query.filter(Solicitud.estado_codigo.in_(['RECIBIDO', 'DEVUELTO_VUS', 'ENTREGADO']))
    elif rol == 'TECNICO_UPC':
        query = query.filter(Solicitud.estado_codigo.in_(['ASIGNADO_UPC', 'EN_EVALUACION']))
    elif rol == 'DIRECCION':
        query = query.filter(Solicitud.estado_codigo.in_(['APROBADO_UPC', 'PENDIENTE_FIRMA_DIRECCION']))
    elif rol == 'DNCD':
        query = query.filter(Solicitud.estado_codigo.in_(['ENVIADO_DNCD', 'PENDIENTE_FIRMA_DNCD']))
    
    if estado:
        query = query.filter_by(estado_codigo=estado)
    
    pagination = query.order_by(Solicitud.fecha_creacion.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    solicitudes = [{
        'id': s.id,
        'numero_expediente': s.numero_expediente,
        'servicio': s.servicio.nombre,
        'estado': s.estado.descripcion,
        'fecha_creacion': s.fecha_creacion.isoformat(),
        'usuario': s.usuario.name
    } for s in pagination.items]
    
    return jsonify({
        'solicitudes': solicitudes,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/api/servicios')
def api_servicios():
    """API para listar servicios disponibles"""
    servicios = CatalogoServicio.query.filter_by(activo=True).all()
    
    return jsonify([{
        'id': s.id,
        'codigo': s.codigo,
        'nombre': s.nombre,
        'descripcion': s.descripcion,
        'costo': float(s.costo) if s.costo else 0,
        'tiempo_estimado_dias': s.tiempo_estimado_dias,
        'requiere_dncd': s.requiere_dncd
    } for s in servicios])

@app.route('/api/notificaciones')
@login_required
def api_notificaciones():
    """API para obtener notificaciones del usuario"""
    notificaciones = Notificacion.query.filter_by(
        usuario_id=session['user_id']
    ).order_by(Notificacion.fecha.desc()).limit(50).all()
    
    return jsonify([{
        'id': n.id,
        'tipo': n.tipo,
        'mensaje': n.mensaje,
        'fecha': n.fecha.isoformat(),
        'leida': n.leida,
        'solicitud_id': n.solicitud_id
    } for n in notificaciones])

@app.route('/api/notificaciones/<notificacion_id>/marcar-leida', methods=['POST'])
@login_required
def marcar_notificacion_leida(notificacion_id):
    """Marca una notificación como leída"""
    notificacion = Notificacion.query.get_or_404(notificacion_id)
    
    if notificacion.usuario_id != session['user_id']:
        return jsonify({'error': 'No tiene permisos'}), 403
    
    notificacion.leida = True
    notificacion.fecha_lectura = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/estadisticas')
@login_required
@role_required('ADMIN', 'DIRECCION')
def api_estadisticas():
    """API para obtener estadísticas del sistema"""
    from sqlalchemy import func

    # Estadísticas generales
    total_solicitudes = Solicitud.query.count()
    solicitudes_pendientes = Solicitud.query.filter(
        ~Solicitud.estado_codigo.in_(['ENTREGADO', 'RECHAZADO_UPC'])
    ).count()
    
    # Por estado
    por_estado = db.session.query(
        EstadoSolicitud.descripcion,
        func.count(Solicitud.id)
    ).join(Solicitud).group_by(EstadoSolicitud.descripcion).all()
    
    # Por servicio
    por_servicio = db.session.query(
        CatalogoServicio.nombre,
        func.count(Solicitud.id)
    ).join(Solicitud).group_by(CatalogoServicio.nombre).all()
    
    # Tiempo promedio de procesamiento
    solicitudes_completadas = Solicitud.query.filter_by(estado_codigo='ENTREGADO').all()
    if solicitudes_completadas:
        tiempos = [(s.fecha_entrega - s.fecha_creacion).days for s in solicitudes_completadas if s.fecha_entrega]
        tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
    else:
        tiempo_promedio = 0
    
    return jsonify({
        'total_solicitudes': total_solicitudes,
        'solicitudes_pendientes': solicitudes_pendientes,
        'por_estado': dict(por_estado),
        'por_servicio': dict(por_servicio),
        'tiempo_promedio_dias': round(tiempo_promedio, 2)
    })

# ============================================================================
# RUTAS DE ADMINISTRACIÓN
# ============================================================================

@app.route('/admin/usuarios')
@login_required
@role_required('ADMIN')
def admin_usuarios():
    """Panel de administración de usuarios"""
    usuarios = Usuario.query.order_by(Usuario.fecha_registro.desc()).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@app.route('/admin/usuarios/<usuario_id>/activar', methods=['POST'])
@login_required
@role_required('ADMIN')
def activar_usuario(usuario_id):
    """Activa o desactiva un usuario"""
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.activo = not usuario.activo
    db.session.commit()
    
    registrar_auditoria('CAMBIAR_ESTADO_USUARIO', detalles=f'Usuario {usuario.email} {"activado" if usuario.activo else "desactivado"}')
    
    return jsonify({'success': True, 'activo': usuario.activo})

@app.route('/admin/usuarios/<usuario_id>/cambiar-rol', methods=['POST'])
@login_required
@role_required('ADMIN')
def cambiar_rol_usuario(usuario_id):
    """Cambia el rol de un usuario"""
    data = request.get_json() if request.is_json else request.form
    usuario = Usuario.query.get_or_404(usuario_id)
    
    nuevo_rol = data.get('rol_codigo')
    if not Rol.query.filter_by(codigo=nuevo_rol).first():
        return jsonify({'error': 'Rol inválido'}), 400
    
    usuario.rol_codigo = nuevo_rol
    db.session.commit()
    
    registrar_auditoria('CAMBIAR_ROL_USUARIO', detalles=f'Rol de {usuario.email} cambiado a {nuevo_rol}')
    
    return jsonify({'success': True})

@app.route('/admin/servicios')
@login_required
@role_required('ADMIN')
def admin_servicios():
    """Panel de administración de servicios"""
    servicios = CatalogoServicio.query.all()
    return render_template('admin/servicios.html', servicios=servicios)

@app.route('/admin/servicios/crear', methods=['POST'])
@login_required
@role_required('ADMIN')
def crear_servicio():
    """Crea un nuevo servicio"""
    data = request.get_json() if request.is_json else request.form
    
    servicio = CatalogoServicio(
        codigo=data.get('codigo'),
        nombre=data.get('nombre'),
        descripcion=data.get('descripcion'),
        costo=data.get('costo'),
        tiempo_estimado_dias=data.get('tiempo_estimado_dias'),
        requiere_dncd=data.get('requiere_dncd', False)
    )
    
    db.session.add(servicio)
    db.session.commit()
    
    registrar_auditoria('CREAR_SERVICIO', detalles=f'Servicio {servicio.nombre} creado')
    
    if request.is_json:
        return jsonify({'success': True, 'servicio_id': servicio.id})
    return redirect(url_for('admin_servicios'))

@app.route('/admin/servicios/<servicio_id>/editar', methods=['POST'])
@login_required
@role_required('ADMIN')
def editar_servicio(servicio_id):
    """Edita un servicio existente"""
    data = request.get_json() if request.is_json else request.form
    servicio = CatalogoServicio.query.get_or_404(servicio_id)
    
    servicio.nombre = data.get('nombre', servicio.nombre)
    servicio.descripcion = data.get('descripcion', servicio.descripcion)
    servicio.costo = data.get('costo', servicio.costo)
    servicio.tiempo_estimado_dias = data.get('tiempo_estimado_dias', servicio.tiempo_estimado_dias)
    servicio.requiere_dncd = data.get('requiere_dncd', servicio.requiere_dncd)
    servicio.activo = data.get('activo', servicio.activo)
    
    db.session.commit()
    
    registrar_auditoria('EDITAR_SERVICIO', detalles=f'Servicio {servicio.nombre} editado')
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('admin_servicios'))

@app.route('/admin/auditoria')
@login_required
@role_required('ADMIN', 'DIRECCION')
def admin_auditoria():
    """Panel de auditoría del sistema"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    pagination = Auditoria.query.order_by(Auditoria.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/auditoria.html', pagination=pagination)

# ============================================================================
# FUNCIONES DE INICIALIZACIÓN
# ============================================================================

def inicializar_datos_base():
    """Inicializa roles y estados básicos del sistema"""
    
    # Crear roles si no existen
    roles_data = [
        {'codigo': 'USUARIO', 'nombre': 'Usuario/Solicitante'},
        {'codigo': 'VUS', 'nombre': 'Ventanilla Única de Servicios'},
        {'codigo': 'TECNICO_UPC', 'nombre': 'Técnico de Productos Controlados'},
        {'codigo': 'ENCARGADO_UPC', 'nombre': 'Encargado de Unidad UPC'},
        {'codigo': 'DIRECCION', 'nombre': 'Dirección'},
        {'codigo': 'DNCD', 'nombre': 'DNCD'},
        {'codigo': 'ADMIN', 'nombre': 'Administrador del Sistema'}
    ]
    
    for rol_data in roles_data:
        if not Rol.query.filter_by(codigo=rol_data['codigo']).first():
            rol = Rol(**rol_data)
            db.session.add(rol)
    
    # Crear estados si no existen
    estados_data = [
        {'codigo': 'RECIBIDO', 'descripcion': 'Recibido en Ventanilla Única'},
        {'codigo': 'DEVUELTO_VUS', 'descripcion': 'Devuelto por VUS - Documentación Incompleta'},
        {'codigo': 'ASIGNADO_UPC', 'descripcion': 'Asignado a UPC para Evaluación'},
        {'codigo': 'EN_EVALUACION', 'descripcion': 'En Evaluación Técnica'},
        {'codigo': 'APROBADO_UPC', 'descripcion': 'Aprobado por UPC'},
        {'codigo': 'RECHAZADO_UPC', 'descripcion': 'Rechazado por UPC'},
        {'codigo': 'PENDIENTE_FIRMA_DIRECCION', 'descripcion': 'Pendiente de Firma de Dirección'},
        {'codigo': 'ENVIADO_DNCD', 'descripcion': 'Enviado a DNCD'},
        {'codigo': 'PENDIENTE_FIRMA_DNCD', 'descripcion': 'Pendiente de Firma DNCD'},
        {'codigo': 'APROBADO_FINAL', 'descripcion': 'Aprobado - Certificado Listo'},
        {'codigo': 'ENTREGADO', 'descripcion': 'Certificado Entregado'}
    ]
    
    for estado_data in estados_data:
        if not EstadoSolicitud.query.filter_by(codigo=estado_data['codigo']).first():
            estado = EstadoSolicitud(**estado_data)
            db.session.add(estado)
    
    # Crear servicios básicos si no existen
    servicios_data = [
        {
            'codigo': 'CERT_CLASE_A',
            'nombre': 'Certificado de Inscripción de Drogas Controladas Clase A',
            'descripcion': 'Certificado para inscripción de drogas controladas Clase A',
            'costo': 1500.00,
            'tiempo_estimado_dias': 15,
            'requiere_dncd': True
        },
        {
            'codigo': 'CERT_CLASE_B_PRIVADO',
            'nombre': 'Certificado de Inscripción de Drogas Controladas Clase B (Privado)',
            'descripcion': 'Certificado para establecimientos privados',
            'costo': 1200.00,
            'tiempo_estimado_dias': 10,
            'requiere_dncd': True
        },
        {
            'codigo': 'CERT_CLASE_B_PUBLICO',
            'nombre': 'Certificado de Inscripción de Drogas Controladas Clase B (Público)',
            'descripcion': 'Certificado para hospitales públicos e instituciones públicas',
            'costo': 0.00,
            'tiempo_estimado_dias': 10,
            'requiere_dncd': True
        },
        {
            'codigo': 'PERMISO_IMP_MATERIA_PRIMA',
            'nombre': 'Permiso de Importación de Materia Prima de Sustancias Controladas',
            'descripcion': 'Permiso para importación de materia prima',
            'costo': 2000.00,
            'tiempo_estimado_dias': 20,
            'requiere_dncd': True
        },
        {
            'codigo': 'PERMISO_IMP_MEDICAMENTOS',
            'nombre': 'Permiso de Importación de Medicamentos con Sustancia Controlada',
            'descripcion': 'Permiso para importación de medicamentos controlados',
            'costo': 1800.00,
            'tiempo_estimado_dias': 15,
            'requiere_dncd': True
        }
    ]
    
    for servicio_data in servicios_data:
        if not CatalogoServicio.query.filter_by(codigo=servicio_data['codigo']).first():
            servicio = CatalogoServicio(**servicio_data)
            db.session.add(servicio)
    
    # Crear usuarios por defecto para cada rol
    usuarios_default = [
        {
            'name': 'Administrador del Sistema',
            'email': 'admin@msp.gob.do',
            'password': 'admin123',
            'rol_codigo': 'ADMIN',
            'tipo_usuario': 'STAFF'
        },
        {
            'name': 'Ventanilla Única',
            'email': 'ventanilla@msp.gob.do',
            'password': 'vus123',
            'rol_codigo': 'VUS',
            'tipo_usuario': 'STAFF'
        },
        {
            'name': 'Técnico UPC',
            'email': 'tecnico@msp.gob.do',
            'password': 'tecnico123',
            'rol_codigo': 'TECNICO_UPC',
            'tipo_usuario': 'STAFF'
        },
        {
            'name': 'Dirección MSP',
            'email': 'direccion@msp.gob.do',
            'password': 'direccion123',
            'rol_codigo': 'DIRECCION',
            'tipo_usuario': 'STAFF'
        },
        {
            'name': 'DNCD',
            'email': 'dncd@msp.gob.do',
            'password': 'dncd123',
            'rol_codigo': 'DNCD',
            'tipo_usuario': 'STAFF'
        }
    ]
    
    for user_data in usuarios_default:
        if not Usuario.query.filter_by(email=user_data['email']).first():
            usuario = Usuario(
                name=user_data['name'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                rol_codigo=user_data['rol_codigo'],
                tipo_usuario=user_data['tipo_usuario']
            )
            db.session.add(usuario)
    
    db.session.commit()
    print("✅ Datos base inicializados correctamente")
    print("\n📧 Usuarios de prueba creados:")
    print("   Admin:      admin@msp.gob.do      / admin123")
    print("   Ventanilla: ventanilla@msp.gob.do / vus123")
    print("   Técnico:    tecnico@msp.gob.do    / tecnico123")
    print("   Dirección:  direccion@msp.gob.do  / direccion123")
    print("   DNCD:       dncd@msp.gob.do       / dncd123")

# ============================================================================
# RUTAS DE FIRMA DIRECCION
# ============================================================================

@app.route('/solicitudes/<solicitud_id>/firmar-direccion', methods=['POST'])
@login_required
@role_required('DIRECCION')
def firmar_direccion(solicitud_id):
    """Firma de Dirección usando workflow de firma digital tipo Adobe Sign"""
    data = request.get_json() if request.is_json else request.form
    
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    servicio = solicitud.servicio
    
    try:
        # 1. Crear certificado (siempre se crea primero)
        if not solicitud.certificado_id:
            numero_certificado = f"CERT-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"
            certificado = Certificado(
                solicitud_id=solicitud_id,
                numero_certificado=numero_certificado,
                tipo_servicio_codigo=servicio.codigo,
                nombre_archivo=f"{numero_certificado}.pdf",
                ruta=f"/certificados/{numero_certificado}.pdf",
                fecha_vencimiento=datetime.utcnow() + timedelta(days=365),
                firmante_direccion_id=session['user_id'],
                firma_digital_direccion='PENDING_WORKFLOW',  # Se actualizará con el workflow
                estado='EN_PROCESO'  # Siempre empieza en EN_PROCESO
            )
            db.session.add(certificado)
            db.session.flush()
            solicitud.certificado_id = certificado.id
            db.session.commit()
        else:
            certificado = Certificado.query.get(solicitud.certificado_id)
        
        # 2. Crear workflow de firma digital
        workflow = crear_workflow_firma_certificado(
            solicitud_id=solicitud_id,
            certificado_id=certificado.id,
            requiere_dncd=servicio.requiere_dncd
        )
        
        # 3. Ejecutar firma de Dirección inmediatamente
        resultado_firma = firmar_documento_workflow(
            workflow_id=workflow.id,
            user_id=session['user_id'],
            signature_type='ELECTRONIC'
        )
        
        # 4. Actualizar firma en certificado con datos del workflow
        certificado.firma_digital_direccion = str(resultado_firma['signature_data'])
        
        # 5. Cambiar estado según resultado del workflow
        if servicio.requiere_dncd:
            cambiar_estado_solicitud(solicitud_id, 'ENVIADO_DNCD', 'Firmado por Dirección - Enviado a DNCD')
            solicitud.fecha_recepcion_dncd = datetime.utcnow()
            # Las notificaciones a DNCD ya se enviaron en firmar_documento_workflow()
        else:
            # Si no requiere DNCD, el workflow ya marcó el certificado como ACTIVO
            cambiar_estado_solicitud(solicitud_id, 'APROBADO_FINAL', 'Certificado aprobado y firmado')
            solicitud.fecha_aprobacion = datetime.utcnow()
            crear_notificacion(
                solicitud.usuario_id,
                'CERTIFICADO_LISTO',
                f'Su certificado está listo para retiro',
                solicitud_id
            )
        
        db.session.commit()
        registrar_auditoria('FIRMAR_DIRECCION', solicitud_id, f'Solicitud firmada por Dirección - Workflow {workflow.public_access_id}')
        
        if request.is_json:
            return jsonify({
                'success': True,
                'certificado_id': certificado.id,
                'workflow_id': workflow.id,
                'workflow_public_id': workflow.public_access_id,
                'workflow_status': workflow.status,
                'signature_data': resultado_firma['signature_data']
            })
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return redirect(url_for('dashboard'))

# ============================================================================
# RUTAS DE CERTIFICADOS
# ============================================================================

@app.route('/certificados')
@login_required
def listar_certificados():
    """Listar certificados según rol"""
    rol = session.get('rol_codigo')
    
    if rol == 'USUARIO':
        # Solo ver sus propios certificados
        solicitudes = Solicitud.query.filter_by(
            usuario_id=session['user_id']
        ).filter(Solicitud.certificado_id.isnot(None)).all()
        certificados = [s.certificado_id for s in solicitudes]
        certificados = Certificado.query.filter(Certificado.id.in_(certificados)).all()
    else:
        # Staff ve todos los certificados
        certificados = Certificado.query.order_by(Certificado.fecha_emision.desc()).all()
    
    return render_template('certificados.html', certificados=certificados)

@app.route('/certificados/<certificado_id>/descargar')
@login_required
def descargar_certificado(certificado_id):
    """Descargar certificado en PDF"""
    certificado = Certificado.query.get_or_404(certificado_id)
    
    # Verificar permisos
    if session['rol_codigo'] == 'USUARIO':
        solicitud = Solicitud.query.filter_by(certificado_id=certificado_id).first()
        if solicitud and solicitud.usuario_id != session['user_id']:
            return jsonify({'error': 'No tiene permisos'}), 403
    
    # Registrar descarga en auditoría
    registrar_auditoria('DESCARGAR_CERTIFICADO', detalles=f'Certificado {certificado.numero_certificado}')
    
    # TODO: Implementar generación real de PDF
    # Por ahora devolver mensaje
    return jsonify({
        'success': True,
        'numero_certificado': certificado.numero_certificado,
        'mensaje': 'Funcionalidad de descarga de PDF pendiente de implementación'
    })

@app.route('/certificados/<numero_certificado>/verificar')
def verificar_certificado_publico(numero_certificado):
    """Verificación pública de autenticidad de certificados"""
    certificado = Certificado.query.filter_by(numero_certificado=numero_certificado).first()
    
    if not certificado:
        return render_template('verificar_certificado.html', 
                             valido=False, 
                             mensaje='Certificado no encontrado')
    
    # Verificar vigencia
    vigente = certificado.estado == 'ACTIVO' and certificado.fecha_vencimiento > datetime.utcnow()
    
    return render_template('verificar_certificado.html',
                         valido=vigente,
                         certificado=certificado)

@app.route('/api/certificados/proximos-vencer')
@login_required
@role_required('ADMIN', 'VUS')
def certificados_proximos_vencer():
    """API para obtener certificados próximos a vencer"""
    dias = request.args.get('dias', 30, type=int)
    fecha_limite = datetime.utcnow() + timedelta(days=dias)
    
    certificados = Certificado.query.filter(
        Certificado.estado == 'ACTIVO',
        Certificado.fecha_vencimiento <= fecha_limite,
        Certificado.fecha_vencimiento > datetime.utcnow()
    ).all()
    
    return jsonify([{
        'id': c.id,
        'numero_certificado': c.numero_certificado,
        'fecha_vencimiento': c.fecha_vencimiento.isoformat(),
        'dias_restantes': (c.fecha_vencimiento - datetime.utcnow()).days
    } for c in certificados])

# ============================================================================
# API DE WORKFLOWS DE FIRMA DIGITAL
# ============================================================================

@app.route('/api/workflows/<workflow_id>/status')
@login_required
def api_workflow_status(workflow_id):
    """Obtener estado completo de un workflow de firma"""
    workflow = SignatureWorkflow.query.get_or_404(workflow_id)
    
    # Verificar permisos
    if session['rol_codigo'] not in ['ADMIN', 'DIRECCION', 'DNCD']:
        if workflow.solicitud:
            solicitud = workflow.solicitud
            if solicitud.usuario_id != session['user_id']:
                return jsonify({'error': 'No tiene permisos'}), 403
    
    lines_data = []
    for line in workflow.addressee_lines:
        groups_data = []
        for group in line.groups:
            actions_data = []
            for action in group.actions:
                actions_data.append({
                    'id': action.id,
                    'user_name': action.user.name,
                    'user_email': action.user.email,
                    'user_rol': action.user.rol_codigo,
                    'action_type': action.action_type,
                    'status': action.status,
                    'action_date': action.action_date.isoformat() if action.action_date else None,
                    'signature_data': action.signature_data,
                    'reject_type': action.reject_type,
                    'reject_reason': action.reject_reason
                })
            
            groups_data.append({
                'id': group.id,
                'group_number': group.group_number,
                'is_or_group': group.is_or_group,
                'status': group.status,
                'actions': actions_data
            })
        
        lines_data.append({
            'id': line.id,
            'line_number': line.line_number,
            'status': line.status,
            'started_date': line.started_date.isoformat() if line.started_date else None,
            'completed_date': line.completed_date.isoformat() if line.completed_date else None,
            'groups': groups_data
        })
    
    return jsonify({
        'workflow_id': workflow.id,
        'public_access_id': workflow.public_access_id,
        'reference': workflow.reference,
        'subject': workflow.subject,
        'status': workflow.status,
        'creation_date': workflow.creation_date.isoformat(),
        'completion_date': workflow.completion_date.isoformat() if workflow.completion_date else None,
        'expiration_date': workflow.expiration_date.isoformat() if workflow.expiration_date else None,
        'solicitud_id': workflow.solicitud_id,
        'certificado_id': workflow.certificado_id,
        'sender': {
            'id': workflow.sender.id,
            'name': workflow.sender.name,
            'email': workflow.sender.email,
            'rol': workflow.sender.rol_codigo
        },
        'lines': lines_data
    })

@app.route('/api/workflows/<workflow_id>/signatures')
@login_required
def api_workflow_signatures(workflow_id):
    """Obtener todas las firmas ejecutadas en un workflow"""
    workflow = SignatureWorkflow.query.get_or_404(workflow_id)
    
    # Verificar permisos
    if session['rol_codigo'] not in ['ADMIN', 'DIRECCION', 'DNCD']:
        if workflow.solicitud:
            solicitud = workflow.solicitud
            if solicitud.usuario_id != session['user_id']:
                return jsonify({'error': 'No tiene permisos'}), 403
    
    signatures = []
    for line in workflow.addressee_lines:
        for group in line.groups:
            for action in group.actions:
                if action.status == 'SIGNED' and action.signature_data:
                    signatures.append({
                        'action_id': action.id,
                        'line_number': line.line_number,
                        'signer': {
                            'name': action.user.name,
                            'email': action.user.email,
                            'rol': action.user.rol_codigo
                        },
                        'signature_date': action.action_date.isoformat() if action.action_date else None,
                        'signature_type': action.signature_data.get('signature_type'),
                        'certificate_hash': action.signature_data.get('certificate_hash'),
                        'document_hash': action.signature_data.get('document_hash'),
                        'ip_address': action.signature_data.get('ip_address'),
                        'timestamp': action.signature_data.get('timestamp')
                    })
    
    return jsonify({
        'workflow_id': workflow.id,
        'public_access_id': workflow.public_access_id,
        'total_signatures': len(signatures),
        'signatures': signatures
    })

@app.route('/api/workflows/<workflow_id>/audit-log')
@login_required
@role_required('ADMIN', 'DIRECCION')
def api_workflow_audit_log(workflow_id):
    """Obtener log de auditoría completo de un workflow"""
    workflow = SignatureWorkflow.query.get_or_404(workflow_id)
    
    audit_logs = SignatureAuditLog.query.filter_by(
        workflow_id=workflow_id
    ).order_by(SignatureAuditLog.timestamp.desc()).all()
    
    return jsonify([{
        'id': log.id,
        'event_type': log.event_type,
        'user': {
            'id': log.user_id,
            'name': Usuario.query.get(log.user_id).name if log.user_id else None
        } if log.user_id else None,
        'event_data': log.event_data,
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'timestamp': log.timestamp.isoformat()
    } for log in audit_logs])

@app.route('/api/usuarios/<user_id>/pending-signatures')
@login_required
def api_user_pending_signatures(user_id):
    """Obtener firmas pendientes de un usuario"""
    # Verificar permisos
    if session['user_id'] != user_id and session['rol_codigo'] not in ['ADMIN', 'DIRECCION']:
        return jsonify({'error': 'No tiene permisos'}), 403
    
    pending_actions = SignatureAction.query.filter_by(
        user_id=user_id,
        status='NEW'
    ).all()
    
    pending_signatures = []
    for action in pending_actions:
        group = action.addressee_group
        line = group.addressee_line
        workflow = line.workflow
        
        # Solo incluir si la línea está activa
        if line.status in ['NEW', 'IN_PROGRESS'] and workflow.status in ['NOT_STARTED', 'IN_PROGRESS']:
            pending_signatures.append({
                'action_id': action.id,
                'workflow_id': workflow.id,
                'public_access_id': workflow.public_access_id,
                'subject': workflow.subject,
                'solicitud_numero': workflow.reference,
                'line_number': line.line_number,
                'action_type': action.action_type,
                'creation_date': workflow.creation_date.isoformat(),
                'expiration_date': workflow.expiration_date.isoformat() if workflow.expiration_date else None,
                'is_expired': workflow.expiration_date < datetime.utcnow() if workflow.expiration_date else False
            })
    
    return jsonify({
        'user_id': user_id,
        'total_pending': len(pending_signatures),
        'pending_signatures': pending_signatures
    })

# ============================================================================
# RUTAS DE DOCUMENTOS
# ============================================================================

@app.route('/solicitudes/<solicitud_id>/documentos/subir', methods=['POST'])
@login_required
def subir_documento(solicitud_id):
    """Subir documento a una solicitud usando Supabase Storage"""
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    
    # Verificar permisos
    if session['rol_codigo'] == 'USUARIO' and solicitud.usuario_id != session['user_id']:
        return jsonify({'error': 'No tiene permisos'}), 403
    
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    archivo = request.files['archivo']
    if archivo.filename == '':
        return jsonify({'error': 'Archivo sin nombre'}), 400
    
    # Validar extensión
    extensiones_permitidas = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
    extension = archivo.filename.rsplit('.', 1)[1].lower() if '.' in archivo.filename else ''
    
    if extension not in extensiones_permitidas:
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400
    
    # Generar nombre único con estructura de carpetas por solicitud
    nombre_storage = f"solicitud_{solicitud_id}/{str(uuid.uuid4())}.{extension}"
    
    try:
        # Leer el contenido del archivo
        file_content = archivo.read()
        
        # Subir a Supabase Storage
        response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=nombre_storage,
            file=file_content,
            file_options={"content-type": archivo.content_type or "application/octet-stream"}
        )
        
        # Obtener URL pública del archivo
        file_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(nombre_storage)
        
        # Registrar en base de datos
        documento = Documento(
            solicitud_id=solicitud_id,
            origen='USUARIO',
            tipo=request.form.get('tipo_documento', 'GENERAL'),
            nombre_original=archivo.filename,
            nombre_storage=nombre_storage,
            ruta=file_url  # Guardar la URL pública
        )
        db.session.add(documento)
        db.session.commit()
        
        registrar_auditoria('SUBIR_DOCUMENTO', solicitud_id, f'Documento {archivo.filename} subido a Supabase Storage')
        
        return jsonify({'success': True, 'documento_id': documento.id, 'url': file_url})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al subir documento a Supabase Storage: {str(e)}")
        return jsonify({'error': f'Error al subir el archivo: {str(e)}'}), 500

@app.route('/documentos/<documento_id>/descargar')
@login_required
def descargar_documento(documento_id):
    """Descargar documento desde Supabase Storage"""
    import io

    from flask import send_file
    
    documento = Documento.query.get_or_404(documento_id)
    
    # Verificar permisos
    if documento.solicitud_id:
        solicitud = Solicitud.query.get(documento.solicitud_id)
        if session['rol_codigo'] == 'USUARIO' and solicitud.usuario_id != session['user_id']:
            return jsonify({'error': 'No tiene permisos'}), 403
    
    # Registrar descarga
    registrar_auditoria('DESCARGAR_DOCUMENTO', documento.solicitud_id, f'Documento {documento.nombre_original}')
    
    try:
        # Descargar desde Supabase Storage
        response = supabase.storage.from_(STORAGE_BUCKET).download(documento.nombre_storage)
        
        # Crear un archivo en memoria
        file_stream = io.BytesIO(response)
        file_stream.seek(0)
        
        # Determinar el mimetype basado en la extensión
        extension = documento.nombre_original.rsplit('.', 1)[1].lower() if '.' in documento.nombre_original else ''
        mimetypes_map = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        mimetype = mimetypes_map.get(extension, 'application/octet-stream')
        
        return send_file(
            file_stream,
            mimetype=mimetype,
            as_attachment=True,
            download_name=documento.nombre_original
        )
        
    except Exception as e:
        print(f"Error al descargar documento desde Supabase Storage: {str(e)}")
        return jsonify({'error': f'Error al descargar el archivo: {str(e)}'}), 500

# ============================================================================
# RUTAS DE REQUISITOS
# ============================================================================

class RequisitoServicio(db.Model):
    __tablename__ = 'requisitos_por_servicio'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    servicio_id = db.Column(db.String, db.ForeignKey('catalogo_servicios.id'), nullable=False)
    nombre = db.Column(db.String, nullable=False)
    descripcion = db.Column(db.Text)
    obligatorio = db.Column(db.Boolean, default=True)
    tipo_documento = db.Column(db.String)
    orden = db.Column(db.Integer, default=0)
    
    servicio = db.relationship('CatalogoServicio', backref='requisitos')

@app.route('/admin/servicios/<servicio_id>/requisitos')
@login_required
@role_required('ADMIN')
def admin_requisitos(servicio_id):
    """Panel de administración de requisitos por servicio"""
    servicio = CatalogoServicio.query.get_or_404(servicio_id)
    requisitos = RequisitoServicio.query.filter_by(servicio_id=servicio_id).order_by(RequisitoServicio.orden).all()
    
    return render_template('admin/requisitos.html', servicio=servicio, requisitos=requisitos)

@app.route('/admin/servicios/<servicio_id>/requisitos/crear', methods=['POST'])
@login_required
@role_required('ADMIN')
def crear_requisito(servicio_id):
    """Crear nuevo requisito para un servicio"""
    data = request.get_json() if request.is_json else request.form
    
    requisito = RequisitoServicio(
        servicio_id=servicio_id,
        nombre=data.get('nombre'),
        descripcion=data.get('descripcion'),
        obligatorio=data.get('obligatorio', True),
        tipo_documento=data.get('tipo_documento'),
        orden=data.get('orden', 0)
    )
    
    db.session.add(requisito)
    db.session.commit()
    
    registrar_auditoria('CREAR_REQUISITO', detalles=f'Requisito {requisito.nombre} creado para servicio {servicio_id}')
    
    if request.is_json:
        return jsonify({'success': True, 'requisito_id': requisito.id})
    return redirect(url_for('admin_requisitos', servicio_id=servicio_id))

@app.route('/admin/requisitos/<requisito_id>/editar', methods=['POST'])
@login_required
@role_required('ADMIN')
def editar_requisito(requisito_id):
    """Editar un requisito existente"""
    data = request.get_json() if request.is_json else request.form
    requisito = RequisitoServicio.query.get_or_404(requisito_id)
    
    requisito.nombre = data.get('nombre', requisito.nombre)
    requisito.descripcion = data.get('descripcion', requisito.descripcion)
    requisito.obligatorio = data.get('obligatorio', requisito.obligatorio)
    requisito.tipo_documento = data.get('tipo_documento', requisito.tipo_documento)
    requisito.orden = data.get('orden', requisito.orden)
    
    db.session.commit()
    
    registrar_auditoria('EDITAR_REQUISITO', detalles=f'Requisito {requisito.nombre} editado')
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('admin_requisitos', servicio_id=requisito.servicio_id))

@app.route('/admin/requisitos/<requisito_id>/eliminar', methods=['POST'])
@login_required
@role_required('ADMIN')
def eliminar_requisito(requisito_id):
    """Eliminar un requisito"""
    requisito = RequisitoServicio.query.get_or_404(requisito_id)
    servicio_id = requisito.servicio_id
    
    db.session.delete(requisito)
    db.session.commit()
    
    registrar_auditoria('ELIMINAR_REQUISITO', detalles=f'Requisito {requisito.nombre} eliminado')
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('admin_requisitos', servicio_id=servicio_id))

@app.route('/api/servicios/<servicio_id>/requisitos')
def api_requisitos_servicio(servicio_id):
    """API para obtener requisitos de un servicio"""
    requisitos = RequisitoServicio.query.filter_by(servicio_id=servicio_id).order_by(RequisitoServicio.orden).all()
    
    return jsonify([{
        'id': r.id,
        'nombre': r.nombre,
        'descripcion': r.descripcion,
        'obligatorio': r.obligatorio,
        'tipo_documento': r.tipo_documento,
        'orden': r.orden
    } for r in requisitos])

# ============================================================================
# TAREAS PROGRAMADAS (CRON JOBS)
# ============================================================================

@app.route('/cron/verificar-vencimientos', methods=['POST'])
def cron_verificar_vencimientos():
    """Tarea programada para verificar certificados próximos a vencer"""
    # TODO: Implementar autenticación con token para cron jobs
    
    dias_aviso = [30, 15, 7, 1]
    
    for dias in dias_aviso:
        fecha_limite = datetime.utcnow() + timedelta(days=dias)
        fecha_inicio = datetime.utcnow() + timedelta(days=dias - 1)
        
        certificados = Certificado.query.filter(
            Certificado.estado == 'ACTIVO',
            Certificado.fecha_vencimiento >= fecha_inicio,
            Certificado.fecha_vencimiento <= fecha_limite
        ).all()
        
        for certificado in certificados:
            solicitud = Solicitud.query.filter_by(certificado_id=certificado.id).first()
            if solicitud:
                crear_notificacion(
                    solicitud.usuario_id,
                    'VENCIMIENTO_CERTIFICADO',
                    f'Su certificado {certificado.numero_certificado} vencerá en {dias} días',
                    solicitud.id
                )
    
    registrar_auditoria('VERIFICAR_VENCIMIENTOS', detalles=f'Verificación automática de vencimientos ejecutada')
    
    return jsonify({'success': True, 'mensaje': 'Verificación de vencimientos completada'})

# ============================================================================
# REPORTES Y EXPORTACIÓN
# ============================================================================

@app.route('/reportes')
@login_required
@role_required('ADMIN', 'DIRECCION', 'ENCARGADO_UPC')
def reportes():
    """Panel de reportes y estadísticas"""
    return render_template('reportes.html')

@app.route('/api/reportes/solicitudes-por-periodo')
@login_required
@role_required('ADMIN', 'DIRECCION', 'ENCARGADO_UPC')
def reporte_solicitudes_periodo():
    """Reporte de solicitudes por período"""
    from sqlalchemy import extract, func
    
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    query = Solicitud.query
    
    if fecha_inicio:
        query = query.filter(Solicitud.fecha_creacion >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Solicitud.fecha_creacion <= fecha_fin)
    
    # Estadísticas por estado
    por_estado = db.session.query(
        EstadoSolicitud.descripcion,
        func.count(Solicitud.id)
    ).join(Solicitud).filter(
        Solicitud.fecha_creacion >= (fecha_inicio or '1900-01-01'),
        Solicitud.fecha_creacion <= (fecha_fin or '2100-12-31')
    ).group_by(EstadoSolicitud.descripcion).all()
    
    # Estadísticas por servicio
    por_servicio = db.session.query(
        CatalogoServicio.nombre,
        func.count(Solicitud.id)
    ).join(Solicitud).filter(
        Solicitud.fecha_creacion >= (fecha_inicio or '1900-01-01'),
        Solicitud.fecha_creacion <= (fecha_fin or '2100-12-31')
    ).group_by(CatalogoServicio.nombre).all()
    
    # Tiempo promedio de procesamiento
    solicitudes_completadas = query.filter_by(estado_codigo='ENTREGADO').all()
    if solicitudes_completadas:
        tiempos = [
            (s.fecha_entrega - s.fecha_creacion).days 
            for s in solicitudes_completadas 
            if s.fecha_entrega
        ]
        tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
    else:
        tiempo_promedio = 0
    
    return jsonify({
        'total': query.count(),
        'por_estado': dict(por_estado),
        'por_servicio': dict(por_servicio),
        'tiempo_promedio_dias': round(tiempo_promedio, 2)
    })

@app.route('/api/reportes/exportar-excel')
@login_required
@role_required('ADMIN', 'DIRECCION')
def exportar_excel():
    """Exportar reporte a Excel"""
    # TODO: Implementar exportación a Excel con openpyxl o xlsxwriter
    
    return jsonify({
        'success': True,
        'mensaje': 'Funcionalidad de exportación a Excel pendiente de implementación'
    })

# ============================================================================
# MANEJO DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    if request.is_json:
        return jsonify({'error': 'Recurso no encontrado'}), 404
    return redirect(url_for('dashboard'))

@app.errorhandler(403)
def forbidden(error):
    if request.is_json:
        return jsonify({'error': 'Acceso denegado'}), 403
    return redirect(url_for('login'))

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.is_json:
        return jsonify({'error': 'Error interno del servidor'}), 500
    return redirect(url_for('dashboard'))

# ============================================================================
# HEALTH CHECK Y MONITOREO
# ============================================================================

@app.route('/health')
def health_check():
    """Endpoint para verificar estado del servicio"""
    try:
        # Verificar conexión a base de datos
        db.session.execute(db.text('SELECT 1'))
        db_status = 'ok'
    except Exception as e:
        db_status = 'error'
    
    return jsonify({
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/info')
def api_info():
    """Información de la API"""
    return jsonify({
        'nombre': 'Sistema de Gestión de Sustancias Controladas',
        'version': '1.0.0',
        'descripcion': 'Backend para gestión de certificados y permisos - MSP y DNCD'
    })

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Sistema de Gestión de Sustancias Controladas")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Intentar conectar a la base de datos
            print("🔌 Conectando a Supabase...")
            db.engine.connect()
            print("✅ Conexión a base de datos exitosa")
            
            # Crear tablas si no existen
            print("📦 Verificando tablas...")
            db.create_all()
            print("✅ Tablas verificadas")
            
            # Inicializar bucket de Supabase Storage
            print("☁️  Inicializando Supabase Storage...")
            inicializar_bucket_storage()
            
            # Inicializar datos base
            print("📝 Inicializando datos base...")
            inicializar_datos_base()
            
        except Exception as e:
            print("⚠️  ERROR DE CONEXIÓN A BASE DE DATOS:")
            print(f"   {str(e)}")
            print("\n💡 SOLUCIONES:")
            print("   1. Verifica tu conexión a Internet")
            print("   2. Verifica que la URI de Supabase sea correcta")
            print("   3. Verifica que la contraseña sea correcta")
            print("   4. Intenta ejecutar 'seed_data.sql' manualmente en Supabase")
            print("\n⚠️  El servidor se iniciará SIN base de datos")
            print("   (Las rutas darán error hasta que se corrija la conexión)\n")
    
    print("=" * 60)
    print("✅ Servidor iniciado en http://localhost:5000")
    print("📧 Admin: admin@msp.gob.do | Contraseña: admin123")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

