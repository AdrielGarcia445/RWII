# 📧 Sistema de Verificación de Email - Guía de Implementación

## 🎯 Resumen de Cambios

Se ha implementado un sistema completo de verificación de correo electrónico para nuevos usuarios que se registran en el sistema. Cuando un usuario se registra, recibe un email bonito con diseño profesional y puede activar su cuenta con un solo clic.

---

## ✨ Funcionalidades Implementadas

### 1. **Verificación por Email al Registrarse**
- Al completar el registro, el usuario queda **inactivo** hasta verificar su email
- Se genera un **token único** de verificación
- Se envía un **email automático** con diseño profesional

### 2. **Email de Verificación**
- **Diseño profesional** con tonos azul oscuro y verde
- Botón destacado "Verificar mi cuenta"
- Link alternativo por si el botón no funciona
- Información clara de MSP, DNCD y VUS
- Responsive y compatible con todos los clientes de email

### 3. **Activación Automática**
- Al hacer clic en el botón del email, el usuario:
  - ✅ Se verifica automáticamente
  - ✅ Se activa su cuenta
  - ✅ Inicia sesión automáticamente
  - ✅ Es redirigido al dashboard

### 4. **Validaciones de Seguridad**
- Token único e irrepetible
- Expiración de 24 horas
- Usuarios no verificados no pueden iniciar sesión
- Los admins y usuarios creados por admin están pre-verificados

---

## 🔧 Configuración SMTP

### Credenciales de Gmail
```python
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "gob.dncd@gmail.com"
SMTP_PASSWORD = "qgsp ahdq xqms isvs"  # Contraseña de aplicación
```

**Nota:** La contraseña es una contraseña de aplicación de Gmail, no la contraseña regular.

---

## 📋 Migración de Base de Datos

### Nuevas Columnas en `usuarios`

```sql
email_verificado        BOOLEAN     DEFAULT FALSE
token_verificacion      VARCHAR     UNIQUE
fecha_token_verificacion TIMESTAMP
```

### Ejecutar Migración

1. Ve a Supabase SQL Editor
2. Ejecuta el archivo `migracion_verificacion_email.sql`
3. Verifica que se ejecutó correctamente

```sql
-- Verificar columnas agregadas
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'usuarios' 
AND column_name IN ('email_verificado', 'token_verificacion', 'fecha_token_verificacion');
```

---

## 🚀 Flujo de Registro y Verificación

### Paso 1: Usuario se Registra
```
Usuario completa formulario → Datos guardados → Token generado → Email enviado
```

### Paso 2: Usuario Verifica Email
```
Usuario abre email → Click en botón → Token validado → Cuenta activada → Login automático
```

### Paso 3: Usuario Accede al Sistema
```
Redirigido al dashboard → Puede usar todas las funcionalidades
```

---

## 🎨 Diseño del Email

### Características del Diseño
- **Colores principales:** Azul oscuro (#0f172a, #1e3a8a) y Verde (#22c55e)
- **Header gradient:** Azul a Verde
- **Ícono de verificación:** Checkmark blanco en círculo verde
- **Botón CTA:** Verde con sombra
- **Footer:** Información institucional
- **Responsive:** Adaptable a móviles

### Vista Previa del Email

```
┌────────────────────────────────────┐
│  [Gradient Azul → Verde]           │
│     ✓ (Círculo blanco/verde)       │
│     ¡Bienvenido(a)!                │
│  Sistema de Sustancias Controladas │
└────────────────────────────────────┘

  Hola, [Nombre del Usuario]

  Gracias por registrarte en el Sistema...
  
  ┌────────────────────────────┐
  │  Verificar mi cuenta  ➜   │
  └────────────────────────────┘
  
  💡 Nota: Si no puedes hacer clic...
  
─────────────────────────────────────
  MSP • DNCD • VUS
  República Dominicana
```

---

## 🔒 Seguridad Implementada

### 1. **Generación de Token**
```python
token_verificacion = secrets.token_urlsafe(32)
# Genera: "rF8kL2pQ9xN4vB7mC1zT5wY8jH3gS6dA"
```

### 2. **Expiración de Token**
- **Tiempo de vida:** 24 horas
- Después de 24 horas, el link no funciona
- Usuario debe contactar soporte

### 3. **Validaciones de Login**
```python
# Usuario DEBE verificar email para iniciar sesión
if not usuario.email_verificado and usuario.rol_codigo == 'USUARIO':
    return error('Debes verificar tu correo electrónico...')
```

### 4. **Usuarios Pre-verificados**
- Usuarios creados por **ADMIN** → `email_verificado = True`
- Usuarios **ADMIN, VUS, DNCD, etc.** → Pre-verificados
- Solo usuarios **USUARIO** requieren verificación

---

## 📝 Archivos Modificados/Creados

### Archivos Nuevos
```
migracion_verificacion_email.sql  - Script de migración SQL
VERIFICACION_EMAIL_GUIA.md        - Esta guía
```

### Archivos Modificados

#### `main.py`
- ✅ Importaciones: `smtplib`, `secrets`, `email`
- ✅ Configuración SMTP
- ✅ Función `enviar_email_verificacion()`
- ✅ Modelo `Usuario` con nuevos campos
- ✅ Ruta `/register` modificada
- ✅ Nueva ruta `/verificar-email/<token>`
- ✅ Ruta `/login` con validación de email
- ✅ `admin_crear_usuario()` pre-verifica usuarios

#### `templates/register.html`
- ✅ Mensaje de éxito con diseño bonito
- ✅ Icono de check animado
- ✅ Instrucciones claras
- ✅ Botón para ir a login

---

## 🧪 Pruebas

### Test 1: Registro Normal
1. Ve a `/register`
2. Completa el formulario
3. Envía el registro
4. **Esperado:** Ver mensaje "Revisa tu correo..."

### Test 2: Recepción de Email
1. Abre el correo registrado
2. **Esperado:** Recibir email con diseño bonito
3. **Verificar:** Botón "Verificar mi cuenta" visible

### Test 3: Verificación
1. Click en botón del email
2. **Esperado:** Redirigido a dashboard
3. **Verificar:** Usuario logueado automáticamente

### Test 4: Login sin Verificar
1. Registrarse pero NO verificar email
2. Intentar hacer login
3. **Esperado:** Error "Debes verificar tu correo..."

### Test 5: Token Expirado
1. Esperar 24+ horas después de registro
2. Click en link del email
3. **Esperado:** Error "Token expirado..."

---

## ⚙️ Variables de Entorno (Opcional)

Si deseas usar variables de entorno en producción:

```python
# En main.py, reemplazar:
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'gob.dncd@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'qgsp ahdq xqms isvs')
```

```bash
# En .env
SMTP_EMAIL=gob.dncd@gmail.com
SMTP_PASSWORD=qgsp ahdq xqms isvs
```

---

## 🎯 Endpoints Nuevos

### `POST /register`
**Cambios:**
- Genera token de verificación
- Usuario creado como inactivo
- Envía email automáticamente
- Retorna template con mensaje de éxito

### `GET /verificar-email/<token>`
**Nueva ruta:**
- Valida el token
- Verifica expiración (24h)
- Activa usuario
- Marca email como verificado
- Login automático
- Redirige a dashboard

---

## 📊 Estados de Usuario

| Estado | Descripción |
|--------|-------------|
| `activo=False, email_verificado=False` | Recién registrado, esperando verificación |
| `activo=True, email_verificado=True` | Usuario verificado y activo |
| `activo=True, email_verificado=True` | Creado por admin (pre-verificado) |

---

## 🐛 Troubleshooting

### Email no llega
1. Verificar configuración SMTP
2. Revisar carpeta de spam
3. Verificar que la contraseña de aplicación esté correcta
4. Ver logs del servidor: `print()` en `enviar_email_verificacion()`

### Token inválido
1. Verificar que el link completo se copió
2. Verificar expiración (24h)
3. Ver en BD: `SELECT token_verificacion, fecha_token_verificacion FROM usuarios WHERE email = '...'`

### Usuario no puede loguearse
1. Verificar `email_verificado = True` en BD
2. Verificar `activo = True` en BD
3. Ver mensajes de error en login

---

## 🚀 Despliegue

### Pre-requisitos
1. ✅ Ejecutar migración SQL
2. ✅ Verificar credenciales SMTP
3. ✅ Probar envío de email en local
4. ✅ Actualizar código en servidor

### Checklist de Producción
- [ ] Migración SQL ejecutada en Supabase
- [ ] SMTP configurado y probado
- [ ] Email de prueba enviado exitosamente
- [ ] Template de email se ve bien en Gmail, Outlook, etc.
- [ ] Links de verificación funcionan
- [ ] Login valida correctamente

---

## 💡 Mejoras Futuras

1. **Reenviar email de verificación**
   - Botón en login si no verificó
   - Generar nuevo token
   
2. **Notificaciones**
   - Email de bienvenida después de verificar
   - Resumen de funcionalidades
   
3. **Analytics**
   - Tasa de verificación
   - Tiempo promedio de verificación
   
4. **Personalización**
   - Templates de email por rol
   - Idiomas múltiples

---

## 📞 Soporte

Para dudas o problemas:
- Ver logs del servidor
- Revisar tabla `auditoria` para eventos de registro/verificación
- Contactar al equipo de desarrollo

---

**Última actualización:** 6 de enero de 2026  
**Versión:** 1.0  
**Sistema:** Gestión de Sustancias Controladas MSP/DNCD
