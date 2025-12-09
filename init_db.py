"""
Script de inicialización de base de datos
Ejecutar: python init_db.py
"""
import os
import sys

from sqlalchemy import text

# Agregar el directorio actual al path para importar desde main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db


def init_database():
    """
    Inicializa la base de datos:
    1. Crea todas las tablas
    2. Carga datos iniciales si las tablas están vacías
    """
    print("=" * 60)
    print("🔧 INICIALIZACIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Verificar conexión
            db.engine.connect()
            print("✅ Conexión a PostgreSQL exitosa")
            
            # Crear todas las tablas
            print("\n📦 Creando tablas...")
            db.create_all()
            print("✅ Tablas creadas correctamente")
            
            # Verificar si ya hay datos
            result = db.session.execute(text("SELECT COUNT(*) FROM roles")).scalar()
            
            if result == 0:
                print("\n📝 Cargando datos iniciales...")
                cargar_datos_iniciales()
                print("✅ Datos iniciales cargados")
            else:
                print("\n⚠️  Las tablas ya contienen datos. Omitiendo carga inicial.")
            
            print("\n" + "=" * 60)
            print("✅ INICIALIZACIÓN COMPLETADA")
            print("=" * 60)
            print("\n📊 Resumen:")
            mostrar_resumen()
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("\n⚠️  Verifica que PostgreSQL esté corriendo y las credenciales sean correctas.")
            print("   Configuración actual:", app.config['SQLALCHEMY_DATABASE_URI'])
            return False
    
    return True

def cargar_datos_iniciales():
    """Carga los datos iniciales en la base de datos"""
    
    # Insertar roles
    roles = [
        ('USUARIO', 'Usuario/Solicitante'),
        ('VUS', 'Ventanilla Única de Servicios'),
        ('TECNICO_UPC', 'Técnico de Productos Controlados'),
        ('ENCARGADO_UPC', 'Encargado de Unidad UPC'),
        ('DIRECCION', 'Dirección/Management'),
        ('DNCD', 'DNCD - Verificación Externa'),
        ('ADMIN', 'Administrador del Sistema')
    ]
    
    for codigo, nombre in roles:
        db.session.execute(
            text("INSERT INTO roles (codigo, nombre) VALUES (:codigo, :nombre)"),
            {"codigo": codigo, "nombre": nombre}
        )
    
    # Insertar estados de solicitud
    estados = [
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
        ('CANCELADO', 'Solicitud cancelada')
    ]
    
    for codigo, descripcion in estados:
        db.session.execute(
            text("INSERT INTO estados_solicitud (codigo, descripcion) VALUES (:codigo, :desc)"),
            {"codigo": codigo, "desc": descripcion}
        )
    
    # Insertar catálogo de servicios
    servicios = [
        ('CLASE_A', 'Certificado de Inscripción de Drogas Controladas Clase A', 1000.00, 15, True),
        ('CLASE_B_PRIVADO', 'Certificado de Inscripción Clase B - Establecimientos Privados', 800.00, 10, False),
        ('CLASE_B_PUBLICO', 'Certificado de Inscripción Clase B - Hospitales Públicos', 500.00, 10, False),
        ('IMPORTACION_MATERIA_PRIMA', 'Permiso de Importación de Materia Prima', 1500.00, 20, True),
        ('IMPORTACION_MEDICAMENTOS', 'Permiso de Importación de Medicamentos', 1200.00, 15, True)
    ]
    
    for codigo, nombre, costo, dias, requiere_dncd in servicios:
        db.session.execute(
            text("""
                INSERT INTO catalogo_servicios 
                (codigo, nombre, descripcion, costo, tiempo_estimado_dias, activo, requiere_dncd) 
                VALUES (:codigo, :nombre, :desc, :costo, :dias, true, :dncd)
            """),
            {
                "codigo": codigo,
                "nombre": nombre,
                "desc": f"Servicio de {nombre}",
                "costo": costo,
                "dias": dias,
                "dncd": requiere_dncd
            }
        )
    
    # Insertar usuarios de prueba
    # Hash bcrypt de "password123": $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC
    password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lQ7TQw5EvJHC"
    
    usuarios = [
        ('Admin Sistema', 'admin@msp.gob.do', 'ADMIN', 'STAFF'),
        ('Usuario VUS', 'vus@msp.gob.do', 'VUS', 'STAFF'),
        ('Técnico UPC', 'tecnico@msp.gob.do', 'TECNICO_UPC', 'STAFF'),
        ('Encargado UPC', 'encargado@msp.gob.do', 'ENCARGADO_UPC', 'STAFF'),
        ('Director MSP', 'direccion@msp.gob.do', 'DIRECCION', 'STAFF'),
        ('Usuario DNCD', 'usuario@dncd.gob.do', 'DNCD', 'STAFF'),
        ('Juan Pérez', 'juan.perez@example.com', 'USUARIO', 'PROFESIONAL'),
        ('María García', 'maria.garcia@empresa.com', 'USUARIO', 'EMPRESARIAL')
    ]
    
    for nombre, email, rol, tipo in usuarios:
        db.session.execute(
            text("""
                INSERT INTO usuarios (name, email, password_hash, rol_codigo, tipo_usuario, activo)
                VALUES (:name, :email, :pass, :rol, :tipo, true)
            """),
            {
                "name": nombre,
                "email": email,
                "pass": password_hash,
                "rol": rol,
                "tipo": tipo
            }
        )
    
    db.session.commit()

def mostrar_resumen():
    """Muestra un resumen de los datos en la base de datos"""
    with app.app_context():
        tablas = [
            'roles',
            'estados_solicitud',
            'catalogo_servicios',
            'usuarios',
            'solicitudes',
            'certificados'
        ]
        
        for tabla in tablas:
            try:
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()
                print(f"   - {tabla}: {count} registros")
            except:
                print(f"   - {tabla}: No existe o no accesible")
        
        print("\n📧 Credenciales de prueba (contraseña: password123):")
        print("   - Admin:      admin@msp.gob.do")
        print("   - VUS:        vus@msp.gob.do")
        print("   - Técnico:    tecnico@msp.gob.do")
        print("   - Dirección:  direccion@msp.gob.do")
        print("   - DNCD:       usuario@dncd.gob.do")
        print("   - Usuario:    juan.perez@example.com")

def reset_database():
    """CUIDADO: Elimina y recrea todas las tablas"""
    print("\n⚠️  ADVERTENCIA: Esto eliminará TODOS los datos")
    respuesta = input("¿Estás seguro? (escribe 'SI' para continuar): ")
    
    if respuesta != 'SI':
        print("Operación cancelada")
        return
    
    with app.app_context():
        print("\n🗑️  Eliminando tablas...")
        db.drop_all()
        print("✅ Tablas eliminadas")
        
        print("\n📦 Recreando tablas...")
        db.create_all()
        print("✅ Tablas recreadas")
        
        print("\n📝 Cargando datos iniciales...")
        cargar_datos_iniciales()
        print("✅ Datos cargados")
        
        print("\n✅ Base de datos reseteada completamente")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        init_database()
