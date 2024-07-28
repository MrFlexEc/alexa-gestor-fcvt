from conexion import *
from flask import Blueprint, request, render_template


home_ruta = Blueprint('home', __name__)

# Ruta principal que renderiza un archivo HTML
@home_ruta.route('/home')
def home():
    return render_template('home.html')
