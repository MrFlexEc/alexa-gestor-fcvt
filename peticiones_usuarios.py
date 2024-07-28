from conexion import *
from flask import Blueprint,Flask, request, jsonify, render_template
from conexion import *
from auth import login  # Importar la función de autenticación desde el módulo auth

from google.oauth2 import service_account

import uuid


user_ruta = Blueprint('usuarios', __name__)

# Ruta principal que renderiza un archivo HTML
@user_ruta.route('/usuarios/')
def home():
    return render_template('Usuarios.html')
@user_ruta.route('/obtener_usuarios', methods=['GET'])
def get_carreras():
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.usuarios
        Usuarios= list(collection.find({}))
        return jsonify(Usuarios), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

# Ruta para manejar solicitudes PUT a /api/data
@user_ruta.route('/agregar/usuario', methods=['PUT'])
def add_usuario():
    data = request.get_json()
    print("Datos recibidos:", data)
    nombres = data.get("nombres")
    apellidos = data.get("apellidos")
    correo = data.get("correo").strip()
    contrasenia = data.get("contrasenia")
    
    if not nombres or not apellidos or not correo or not contrasenia:
        return jsonify(success=False, message='Faltan campos por completar')

    client = connect_to_mongodb()

    try:
        if client:
            print("Conexión exitosa a MongoDB")
            db = client.AlexaGestor
            collection = db.usuarios
            
            # Generar un ID único
            usuario_id = str(uuid.uuid4())

            usuario = {
                "_id": usuario_id,
                "nombres": nombres,
                "apellidos": apellidos,
                "correo":correo,
                "contrasenia":contrasenia
            }
            Resultado = collection.insert_one(usuario)
             # Obtener todos los correos de los usuarios
            client.close()

            if Resultado:
                return jsonify(success=True, message=f"Se ha agregado un administrador: {apellidos} {nombres}")

            else:
                return jsonify(success=False, message=f'Ha surgido un error al agregar al usuario {nombres}.')
        else:
            return jsonify(success=False, message=f'Ha surgido un problema con la conexión.')
    except Exception as e:
        print("Error:", e)
    
@user_ruta.route('/eliminar/usuario/<_id>', methods=['DELETE'])
def delete_usuario(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.usuarios

        usuario = collection.find_one({"_id": _id})
        if usuario:
            email_usuario = usuario.get('correo')

            # Revocar permisos antes de eliminar el usuario
            carpetas = ['18KiGWZdqFzHS9eSpeBjetyH3YW4g3lce', '1COEo694kE7LcvZmBaPtviknw7ocky6PU', '1-KZqvvcRAM-n1h-OEC6ICHUgENCJdoTl']

            # Eliminar el usuario de la base de datos
            result = collection.delete_one({"_id": _id})
            if result.deleted_count == 1:
                return jsonify(success=True)
            else:
                return jsonify(success=False, message=f'Ha surgido un problema al eliminar al docente.')
    except Exception as e:
        print("Error")
        client.close()

@user_ruta.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection = db.usuarios

        # Excluir el campo "_id" de los resultados
        resultados = collection.find({})

        # Convertir los resultados a una lista de diccionarios
        usuarios = [usuario for usuario in resultados]

        # Cerrar la conexión con MongoDB
        client.close()

        # Devolver los resultados como JSON
        return jsonify({"usuarios": usuarios}), 200

    except Exception as e:
        print("error")

