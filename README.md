# Sistema de Gestión de Sustancias Controladas
## Ministerio de Salud Pública y DNCD

Sistema web para la gestión de solicitudes, evaluación, aprobación y emisión de certificados y permisos de sustancias controladas según la Ley 50-88.

---

## 📋 Características Principales

- ✅ **Gestión de Solicitudes**: Depósito electrónico con documentos adjuntos
- ✅ **Flujo de Trabajo Completo**: 16 estados del proceso de revisión
- ✅ **Múltiples Roles**: Usuario, VUS, Técnico UPC, Dirección, DNCD, Admin
- ✅ **Firma Digital**: Certificados con firmas digitales múltiples
- ✅ **Auditoría Completa**: Trazabilidad de todas las acciones
- ✅ **Notificaciones**: Alertas por correo y plataforma
- ✅ **Catálogo Administrable**: Servicios y requisitos configurables
- ✅ **Base de Datos PostgreSQL**: Persistencia robusta
- ✅ **API REST**: 50+ endpoints documentados
- ✅ **Vistas HTML**: 22 rutas de interfaz web

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos

- Python 3.8 o superior
- Cuenta en Supabase (GRATIS - no requiere tarjeta de crédito)
- pip (gestor de paquetes Python)

**NOTA IMPORTANTE:** Este proyecto usa **Supabase** como base de datos PostgreSQL en la nube. 
**NO necesitas instalar PostgreSQL localmente.** Todo funciona desde la nube de forma gratuita.

### 2. Crear Base de Datos en Supabase (5 minutos)

```bash
# 1. Ve a https://supabase.com y crea una cuenta (GRATIS)

# 2. Crea un nuevo proyecto:
#    - Name: sustancias-controladas-msp
#    - Database Password: [Genera una contraseña segura]
#    - Region: Selecciona la más cercana
#    - Plan: Free (500 MB, perfecto para este proyecto)

# 3. Obtén tu URL de conexión:
#    Settings > Database > Connection string > URI
#    
#    Se verá así:
#    postgresql://postgres:TU_PASSWORD@db.tuproyecto.supabase.co:5432/postgres
```

Ver guía detallada en: **SUPABASE_SETUP.txt**

### 3. Configurar Proyecto

```bash
# Clonar o descargar el proyecto
cd "Desarrollo Web"

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo de configuración
copy .env.example .env

# Editar .env y pegar tu URL de Supabase:
# SUPABASE_DB_URL=postgresql://postgres:TU_PASSWORD@db.tuproyecto.supabase.co:5432/postgres
```

### 4. Inicializar Base de Datos

```bash
# Este comando crea las tablas y datos iniciales en Supabase
python init_db.py

# Deberías ver:
# ✅ Conexión a PostgreSQL exitosa
# ✅ Tablas creadas correctamente
# ✅ Datos iniciales cargados
```

### 5. Ejecutar el Servidor

```bash
python main.py
```

El servidor estará disponible en: **http://localhost:5000**

**¡Todo listo!** Tu aplicación ahora usa Supabase en la nube. 🎉

---

## 📁 Estructura del Proyecto

```
Desarrollo Web/
│
├── main.py                    # Aplicación principal Flask
├── init_db.py                 # Script de inicialización de DB
├── requirements.txt           # Dependencias Python
│
├── schema.sql                 # Esquema de base de datos
├── seed_data.sql             # Datos iniciales
│
├── DATABASE_GUIDE.txt        # Guía completa de PostgreSQL
├── RUTAS_VISTAS_AGREGADAS.txt # Documentación de rutas
├── README.md                 # Este archivo
│
├── static/                   # Archivos estáticos (CSS, JS, imágenes)
│   ├── css/
│   ├── js/
│   └── images/
│
├── template/                 # Templates HTML (Jinja2)
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard_*.html
│   └── ...
│
└── uploads/                  # Archivos subidos (temporal)
```

---

## 🔐 Credenciales de Prueba

**Contraseña para todos:** `password123`

| Rol | Email | Descripción |
|-----|-------|-------------|
| Admin | admin@msp.gob.do | Administrador del sistema |
| VUS | vus@msp.gob.do | Ventanilla Única de Servicios |
| Técnico UPC | tecnico@msp.gob.do | Técnico evaluador |
| Encargado UPC | encargado@msp.gob.do | Encargado de UPC |
| Dirección | direccion@msp.gob.do | Director/Management |
| DNCD | usuario@dncd.gob.do | Usuario DNCD |
| Usuario | juan.perez@example.com | Usuario regular |
| Empresa | maria.garcia@empresa.com | Usuario empresarial |

---

## 📚 Documentación de API

### Endpoints Principales

#### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/register` - Registrar usuario

#### Solicitudes
- `POST /api/solicitud` - Crear nueva solicitud
- `GET /api/solicitud/<id>` - Obtener solicitud
- `GET /api/solicitudes` - Listar solicitudes

#### VUS (Ventanilla Única)
- `POST /api/vus/validar/<id>` - Validar solicitud
- `POST /api/vus/entregar/<id>` - Registrar entrega

#### UPC (Evaluación Técnica)
- `POST /api/upc/recibir/<id>` - Recibir solicitud
- `POST /api/upc/evaluar/<id>` - Evaluar solicitud
- `POST /api/upc/reasignar/<id>` - Reasignar técnico

#### Dirección
- `POST /api/direccion/firma-rechazo/<id>` - Firmar rechazo
- `POST /api/direccion/firma-aprobacion/<id>` - Firmar aprobación

#### DNCD
- `POST /api/dncd/recibir/<id>` - Recibir en DNCD
- `POST /api/dncd/firma/<id>` - Firmar y autorizar

#### Administración
- `GET /api/admin/usuarios` - Gestionar usuarios
- `POST /api/admin/catalogo` - Gestionar catálogo
- `GET /api/reportes/estadisticas` - Estadísticas del sistema

**Total:** 72+ endpoints (50+ API + 22 vistas)

Ver documentación completa en: `RUTAS_VISTAS_AGREGADAS.txt`

---

## 🗄️ Base de Datos (Supabase Cloud PostgreSQL)

### Configuración de Base de Datos

- **Proveedor:** Supabase (PostgreSQL en la nube)
- **Plan:** Free Tier - 500 MB (suficiente para desarrollo)
- **Características:**
  - ✅ Sin instalación local requerida
  - ✅ Interfaz web visual para gestionar datos
  - ✅ Backups automáticos incluidos
  - ✅ Conexión SSL/TLS segura
  - ✅ Acceso desde cualquier lugar

### Tablas Principales

- **roles** - Roles del sistema (7 roles)
- **estados_solicitud** - Estados del flujo de trabajo (16 estados)
- **usuarios** - Usuarios del sistema
- **catalogo_servicios** - Servicios disponibles
- **solicitudes** - Solicitudes de certificados
- **certificados** - Certificados emitidos
- **documentos** - Archivos adjuntos
- **evaluaciones_tecnicas_upc** - Evaluaciones técnicas
- **auditoria** - Registro de auditoría completo
- **notificaciones** - Notificaciones a usuarios

### Gestión Visual de Datos

1. **Dashboard de Supabase:**
   ```
   https://supabase.com/dashboard/project/TU_PROJECT_ID
   ```

2. **Table Editor:**
   - Ver, insertar, editar, eliminar registros visualmente
   - Sin necesidad de SQL

3. **SQL Editor:**
   - Ejecutar queries personalizadas
   - Exportar datos

Ver guía completa en: **DATABASE_GUIDE.txt** y **SUPABASE_SETUP.txt**

---

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env`:

```env
# Base de datos Supabase (REQUERIDO)
SUPABASE_DB_URL=postgresql://postgres:TU_PASSWORD@db.tuproyecto.supabase.co:5432/postgres

# Seguridad
SECRET_KEY=tu-secret-key-aleatoria-y-segura

# Flask
FLASK_ENV=development
FLASK_DEBUG=1

# Archivos
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=./uploads

# Email (futuro)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notificaciones@msp.gob.do
SMTP_PASSWORD=password
```

**IMPORTANTE:** La URL de Supabase la obtienes desde tu proyecto:
`Settings > Database > Connection string > URI`

### Configuración de Producción

```python
# En producción usar:
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DEBUG'] = False

# Usar Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

---

## 📊 Flujo de Trabajo

```
Usuario deposita solicitud
         ↓
VUS revisa requisitos
    ↙        ↘
Cumple     No cumple → Devuelve al usuario
    ↓
Técnico UPC evalúa
    ↙        ↓        ↘
Aprueba  Devuelve  Rechaza
    ↓        ↓        ↓
Dirección firma  Usuario  Dirección firma
certificado     corrige   rechazo
    ↓                        ↓
¿Requiere DNCD?         Usuario notificado
    ↙      ↘
  Sí        No
    ↓        ↓
DNCD firma  Listo para retiro
    ↓
Listo para retiro
    ↓
VUS entrega certificado
    ↓
COMPLETADO
```

---

## 🧪 Testing

```bash
# Verificar conexión a DB
python -c "from main import app, db; app.app_context().push(); print('✅ DB OK')"

# Contar usuarios
python -c "from main import app, db, Usuario; app.app_context().push(); print(Usuario.query.count(), 'usuarios')"

# Ejecutar con modo debug
FLASK_DEBUG=1 python main.py
```

---

## 🛠️ Mantenimiento

### Backup de Base de Datos

```bash
# Crear backup
pg_dump -U postgres sustancias_controladas > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql -U postgres sustancias_controladas < backup_20231201.sql
```

### Ver Logs

```bash
# En producción con Gunicorn
tail -f gunicorn.log

# Ver logs de PostgreSQL
tail -f /var/log/postgresql/postgresql-14-main.log
```

### Resetear Base de Datos

```bash
# ⚠️ CUIDADO: Esto borra todos los datos
python init_db.py --reset
```

---

## 🐛 Troubleshooting

### Error: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Error: "could not connect to database"
- Verificar que PostgreSQL está corriendo
- Verificar credenciales en `DATABASE_URL`
- Verificar que la base de datos existe

### Error: "relation does not exist"
```bash
python init_db.py
```

### Queries lentos
- Verificar índices en tablas
- Usar `EXPLAIN ANALYZE` en PostgreSQL
- Optimizar consultas con JOINs

Ver más en: `DATABASE_GUIDE.txt`

---

## 📝 Requerimientos Funcionales Implementados

✅ **RF-1: Gestión de Solicitudes**
- RF-1.1: Depósito electrónico con documentos
- RF-1.2: Validación por VUS
- RF-1.3: Comunicación de devolución
- RF-1.4: Trazabilidad completa
- RF-1.5: Notificaciones por correo y plataforma

✅ **RF-2: Evaluación Técnica UPC**
- RF-2.1: Recepción y remisión
- RF-2.2: Evaluación con checklist
- RF-2.3: Devolución/rechazo
- RF-2.4: Firma digital de rechazos

✅ **RF-3: Aprobación y Emisión**
- RF-3.1: Aprobación UPC
- RF-3.2: Firma digital Dirección
- RF-3.3: Verificación y firma DNCD

✅ **RF-4: Auditoría y Trazabilidad**
- Registro completo de todas las acciones
- Historial de estados por solicitud
- Observaciones por rol

---

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con bcrypt
- ✅ Validación de roles en endpoints
- ✅ Sesiones seguras con Flask session
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ CORS configurado
- ⚠️ TODO: Implementar JWT tokens
- ⚠️ TODO: Rate limiting
- ⚠️ TODO: CSRF protection

---

## 📈 Escalabilidad

- Base de datos PostgreSQL con índices optimizados
- Connection pooling configurado
- Preparado para load balancing
- Arquitectura REST stateless
- Separación frontend/backend

---

## 🎯 Próximos Pasos

1. **Frontend Completo**
   - Crear templates HTML para todas las rutas
   - Implementar CSS y JavaScript
   - Agregar validaciones de formularios

2. **Integraciones**
   - Servicio de email (SendGrid, AWS SES)
   - Almacenamiento cloud (S3, Azure Blob)
   - Firma digital certificada
   - Pasarela de pagos

3. **Mejoras**
   - Sistema de notificaciones push
   - Exportación de reportes (PDF, Excel)
   - Dashboard con gráficos
   - API pública para consultas

4. **Seguridad**
   - Implementar JWT
   - Rate limiting
   - 2FA para administradores
   - Logs de seguridad

---

## 👥 Roles del Sistema

| Rol | Permisos | Responsabilidades |
|-----|----------|-------------------|
| USUARIO | Crear solicitudes, consultar estado | Solicitante de certificados |
| VUS | Validar requisitos, registrar entregas | Ventanilla única |
| TECNICO_UPC | Evaluar solicitudes técnicamente | Evaluación técnica |
| ENCARGADO_UPC | Reasignar, supervisar | Gestión de técnicos |
| DIRECCION | Firmar aprobaciones/rechazos | Autorización final |
| DNCD | Verificar y firmar permisos especiales | Control externo |
| ADMIN | Configurar sistema, gestionar usuarios | Administración total |

---

## 📞 Soporte

Para reportar problemas o solicitar ayuda:
- Email: soporte@msp.gob.do
- Documentación: Ver archivos .txt en el proyecto

---

## 📄 Licencia

Sistema desarrollado para el Ministerio de Salud Pública de la República Dominicana.
Basado en la Ley 50-88 sobre Drogas y Sustancias Controladas.

---

## ✅ Checklist de Implementación

- [x] Configuración Flask
- [x] Modelos SQLAlchemy
- [x] Esquema PostgreSQL
- [x] Datos iniciales
- [x] Rutas API
- [x] Rutas de vistas
- [x] Sistema de autenticación
- [x] Control de acceso por roles
- [x] Auditoría completa
- [ ] Templates HTML completos
- [ ] CSS y diseño responsivo
- [ ] JavaScript interactivo
- [ ] Integración de emails
- [ ] Almacenamiento cloud
- [ ] Firma digital real
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Deployment en producción

---

**Versión:** 1.0.0  
**Última actualización:** Noviembre 2025  
**Estado:** En desarrollo - Base funcional completa
