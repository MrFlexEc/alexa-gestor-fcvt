import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

def enviar_correo(destinatario, asunto, cuerpo):
    # Cargar variables de entorno desde archivo .env
    load_dotenv()

    # Obtener credenciales de las variables de entorno
    remitente = os.getenv('OUTLOOK_EMAIL')
    contrasena = os.getenv('OUTLOOK_PASSWORD')
    

    if not remitente or not contrasena:
        print("Error: No se encontraron las credenciales en las variables de entorno.")
        return

    # Crear el objeto de mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    # Adjuntar el cuerpo del mensaje
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Conectar al servidor de Outlook 365
    try:
        #smtplib.SMTP("smtp.gmail.com", port=587
        servidor_smtp = smtplib.SMTP('smtp.gmail.com',587)
        print("Conexión exitosa al servidor SMTP")
        servidor_smtp.starttls()  # Iniciar la conexión segura
        print("Conexión TLS establecida")
        servidor_smtp.login(remitente, contrasena)
        print("Autenticación exitosa")
        texto = mensaje.as_string()
        servidor_smtp.sendmail(remitente, destinatario, texto)
        print("Correo enviado exitosamente")
        servidor_smtp.quit()
    except smtplib.SMTPException as e:
        print(f"Error SMTP: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ejemplo de uso
    destinatario = 'e1314845791@live.uleam.edu.ec'  # Cambia por la dirección de correo de destino
    asunto = 'Asunto del correo'
    cuerpo = 'Cuerpo del correo'

    enviar_correo(destinatario, asunto, cuerpo)
    print("Intentando conectar al servidor SMTP...")
