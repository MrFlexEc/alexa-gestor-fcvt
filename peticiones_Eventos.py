from flask import Blueprint,Flask, request, jsonify, render_template
from conexion import *
from flask_login import login_required

import uuid



eventos_ruta = Blueprint('eventos', __name__)

# Ruta principal que renderiza un archivo HTML
@eventos_ruta.route('/eventos/')
def home():
    return render_template('Eventos.html')

# Ruta para manejar solicitudes GET a /api/data
@eventos_ruta.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"mensaje": "Solicitud GET recibida"})

# Ruta para manejar solicitudes PUT a /api/data
@eventos_ruta.route('/agregar/evento', methods=['PUT'])
def add_evento():
    data = request.get_json()
    print("Datos recibidos:", data)
    
    nombre_evento = data.get("nombre_evento", "").strip()
    fecha_evento_inicio = data.get("fecha_evento_inicio")
    fecha_evento_fin = data.get("fecha_evento_fin")
    ubicacion_evento = data.get("ubicacion_evento")
    observaciones = data.get("observaciones")  # Cambiar a minúscula para que coincida

    if not nombre_evento or not fecha_evento_inicio or not fecha_evento_fin or not ubicacion_evento:
        return jsonify(success=False, message='Faltan campos por completar')


    client = connect_to_mongodb()

    try:
        if client:
            print("Conexión exitosa a MongoDB")
            db = client.AlexaGestor
            collection = db.eventos
            
            # Generar un ID único
            evento_id = str(uuid.uuid4())

            evento = {
                "_id": evento_id,
                "nombre_evento": nombre_evento,
                "ubicacion_evento": ubicacion_evento,
                "fecha_evento_inicio": fecha_evento_inicio,
                "fecha_evento_fin": fecha_evento_fin,
                "observaciones": observaciones
            }
            result = collection.insert_one(evento)
            client.close()
            if result:
                return jsonify(success=True)
            else:
                return jsonify(success=False, message=f'Ha surgido un error al agregar el evento {nombre_evento}.')
        else:
            print("Error: No se pudo conectar a MongoDB Atlas")
            return jsonify(success=False, message=f'Ha surgido un problema con la conexion.')
    except Exception as e:
        print("Error:", e)
    
@eventos_ruta.route('/eliminar/evento/<_id>', methods=['DELETE'])
def delete_carrera(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.eventos
        result = collection.delete_one({"_id": _id})
        if result.deleted_count == 1:
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Ha surgido un problema al eliminar el evento.')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

@eventos_ruta.route('/api/eventos', methods=['GET'])
def obtener_eventos():
    try:
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection = db.eventos

        # Excluir el campo "_id" de los resultados
        resultados = collection.find({})

        # Convertir los resultados a una lista de diccionarios
        eventos = [evento for evento in resultados]

        # Cerrar la conexión con MongoDB
        client.close()

        # Devolver los resultados como JSON
        return jsonify({"eventos": eventos}), 200

    except Exception as e:
        print("error")
