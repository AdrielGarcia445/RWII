"""
Script de prueba para verificar el envío de emails
Ejecutar: python test_email.py
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "gob.dncd@gmail.com"
SMTP_PASSWORD = "qgsp ahdq xqms isvs"

def test_email(destinatario):
    """Prueba de envío de email"""
    try:
        print(f"📧 Enviando email de prueba a: {destinatario}")
        
        mensaje = MIMEMultipart('alternative')
        mensaje['Subject'] = 'Prueba - Sistema de Sustancias Controladas'
        mensaje['From'] = f'Sistema DNCD <{SMTP_EMAIL}>'
        mensaje['To'] = destinatario
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="margin: 0; padding: 40px; font-family: Arial, sans-serif; background: #f1f5f9;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #22c55e 100%); padding: 40px; text-align: center;">
                    <div style="width: 70px; height: 70px; margin: 0 auto 15px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 32px; color: #22c55e;">✓</span>
                    </div>
                    <h1 style="margin: 0; color: white; font-size: 28px;">¡Email de Prueba!</h1>
                    <p style="margin: 10px 0 0; color: rgba(255,255,255,0.9); font-size: 15px;">Sistema de Sustancias Controladas</p>
                </div>
                
                <div style="padding: 40px;">
                    <h2 style="margin: 0 0 20px; color: #1e293b; font-size: 22px;">Configuración SMTP Exitosa</h2>
                    
                    <p style="margin: 0 0 20px; color: #475569; font-size: 15px; line-height: 1.6;">
                        Si estás viendo este correo, significa que la configuración de SMTP está funcionando correctamente.
                    </p>
                    
                    <div style="background: #dcfce7; border-left: 4px solid #22c55e; padding: 15px; border-radius: 8px;">
                        <strong style="color: #166534;">✅ Configuración verificada:</strong>
                        <ul style="margin: 10px 0 0; padding-left: 20px; color: #166534;">
                            <li>Servidor SMTP conectado</li>
                            <li>Autenticación exitosa</li>
                            <li>Email enviado correctamente</li>
                        </ul>
                    </div>
                </div>
                
                <div style="background: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; color: #64748b; font-size: 13px;">
                        <strong>Ministerio de Salud Pública</strong> • <strong>DNCD</strong> • <strong>VUS</strong>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        parte_html = MIMEText(html, 'html')
        mensaje.attach(parte_html)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
            print("🔄 Conectando al servidor SMTP...")
            servidor.starttls()
            print("🔐 Autenticando...")
            servidor.login(SMTP_EMAIL, SMTP_PASSWORD)
            print("📤 Enviando mensaje...")
            servidor.send_message(mensaje)
        
        print("✅ ¡Email enviado exitosamente!")
        print(f"📬 Revisa la bandeja de entrada de: {destinatario}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("   PRUEBA DE CONFIGURACIÓN SMTP")
    print("   Sistema de Sustancias Controladas")
    print("="*60)
    print()
    
    email_prueba = input("Ingresa tu email para la prueba: ").strip()
    
    if email_prueba:
        print()
        test_email(email_prueba)
    else:
        print("❌ Email no válido")
    
    print()
    print("="*60)
