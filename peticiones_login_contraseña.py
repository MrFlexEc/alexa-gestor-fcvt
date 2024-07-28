from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from conexion import connect_to_mongodb
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

logincontraseña_ruta = Blueprint('login_contraseña', __name__)

# Ruta principal que renderiza un archivo HTML de login
@logincontraseña_ruta.route('/recuperar_contraseña')
def home():
    return render_template('Login_contraseña.html')

# Ruta para verificar las credenciales y autenticar al usuario
@logincontraseña_ruta.route('/recuperacion', methods=['POST'])
def recuperar_contraseña():
    data = request.get_json()
    correo = data.get("correo", '').strip()
    
    if not correo:
        return jsonify(success=False, message="Falta correo"), 400

    client = connect_to_mongodb()

    try:
        db = client.AlexaGestor
        collection = db.usuarios
        usuario = collection.find_one({"correo": correo})
        
        if usuario:
            nombres = usuario.get("nombres")
            apellidos = usuario.get("apellidos")
            contraseña = usuario.get("contrasenia")  # Asegúrate de tener este campo en tu colección
            
            destinatario = correo
            asunto = 'Recuperación de contraseña AlexaGestor'
            cuerpo = f"Hola, {apellidos} {nombres}, espero que te encuentres bien.\n\n"
            cuerpo += f"Hemos recibido tu solicitud para recuperar la contraseña de tu cuenta.\n"
            cuerpo += f"A continuación, te proporcionamos la información solicitada:\n\n"
            cuerpo += f"Tu contraseña es: {contraseña}\n"
            cuerpo += f"Correo asociado: {correo}\n\n"
            cuerpo += f"¡Recuerda guardar tus credenciales de manera segura!\n"
            cuerpo += f"Si no lo solicitaste, por favor contacta con nuestro soporte.\n\n"
            cuerpo += f"Saludos cordiales,\n"
            cuerpo += f"Equipo de Soporte AlexaGestor"
            
            correo_enviado = enviar_correo(destinatario, asunto, cuerpo)
            if correo_enviado:
                return jsonify(success=True, message="Se ha enviado la información al correo proporcionado."), 400
            else: 
                return jsonify(success=False, message="No se pudo enviar el correo."), 400
        else:
                return jsonify(success=False, message="El correo proporcionado no existe en el registro."), 400
        
    except Exception as e:
        return jsonify(success=False)
    finally:
        client.close()
# Ruta para cerrar sesión
@logincontraseña_ruta.route('/retroceder', methods=['GET'])
def logout():
    # Redirigir al usuario al login con un mensaje
    return redirect(url_for('login.home'))



def enviar_correo(destinatario, asunto, cuerpo):
    # Cargar variables de entorno desde archivo .env
    load_dotenv()

    # Obtener credenciales de las variables de entorno
    remitente = os.getenv('OUTLOOK_EMAIL')
    contrasena = os.getenv('OUTLOOK_PASSWORD')

    if not remitente or not contrasena:
        print("Error: No se encontraron las credenciales en las variables de entorno.")
        return False

    # Crear el objeto de mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    # Adjuntar el cuerpo del mensaje
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Conectar al servidor de Gmail
    try:
        servidor_smtp = smtplib.SMTP('smtp.gmail.com', 587)
        servidor_smtp.starttls()  # Iniciar la conexión segura
        servidor_smtp.login(remitente, contrasena)
        texto = mensaje.as_string()
        servidor_smtp.sendmail(remitente, destinatario, texto)
        servidor_smtp.quit()
        print("Correo enviado exitosamente")
        return True
    except smtplib.SMTPException as e:
        print(f"Error SMTP: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False