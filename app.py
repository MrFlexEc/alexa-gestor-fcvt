from flask import Flask, session, redirect, url_for
from peticiones_login import login_ruta
from peticiones_login_contraseña import logincontraseña_ruta
from peticiones_Comunidades import comunidades_ruta
from peticiones_home import home_ruta
from peticiones_Horarios_Distribucion import horarios_ruta
from peticiones_Eventos import eventos_ruta
from peticiones_Carreras import carreras_ruta
from peticiones_Docentes import docentes_ruta
from peticiones_Formatos_Documentos import formatos_ruta
from peticiones_Proceso_Academicos import procesos_ruta
from peticiones_PerfilDocente_Gemeni import perfil_ruta
from peticiones_usuarios import user_ruta
from auth import login

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necesario para manejar sesiones en Flask

# Función para verificar si el usuario está autenticado
def verificar_autenticacion():
    # Verificar si 'usuario_id' está en la sesión
    if 'usuario_id' not in session:
        # Redireccionar a la página de login si no está autenticado
        return redirect(url_for('login.home'))

@app.before_request
def before_request():
    verificar_autenticacion()


# Registrar los Blueprints en la aplicación principal
app.register_blueprint(login_ruta)
app.register_blueprint(logincontraseña_ruta)
app.register_blueprint(home_ruta)
app.register_blueprint(comunidades_ruta)
app.register_blueprint(horarios_ruta)
app.register_blueprint(eventos_ruta)
app.register_blueprint(carreras_ruta)
app.register_blueprint(docentes_ruta)
app.register_blueprint(formatos_ruta)
app.register_blueprint(procesos_ruta)
app.register_blueprint(perfil_ruta)
app.register_blueprint(user_ruta)

if __name__ == '__main__':
    app.run(debug=True, port=8080)