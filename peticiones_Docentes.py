from flask import Blueprint,Flask, request, jsonify, render_template
from conexion import *
from flask_login import login_required

import uuid



docentes_ruta = Blueprint('docentes', __name__)

# Ruta principal que renderiza un archivo HTML
@docentes_ruta.route('/docentes/')
def home():
    return render_template('docentes.html')

# Ruta para manejar solicitudes GET a /api/data
@docentes_ruta.route('/obtener_docentes', methods=['GET'])
def get_docentes():
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.docentes
        docentes = list(collection.find({}, {"_id": 1, "nombre_docente": 1, "apellido_docente": 1}))
        return jsonify(docentes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

# Ruta para manejar solicitudes PUT a /api/data
@docentes_ruta.route('/agregar/docente', methods=['PUT'])
def add_docente():
    data = request.get_json()
    print("Datos recibidos:", data)
    nombre_docente = data.get("nombre_docente", "").strip()
    apellido_docente = data.get("apellido_docente", "").strip()
    
    if not nombre_docente or not apellido_docente:
        return jsonify(success=False, message='Faltan campos por completar')

    client = connect_to_mongodb()

    try:
        if client:
            print("Conexión exitosa a MongoDB")
            db = client.AlexaGestor
            collection = db.docentes
            
            # Generar un ID único
            docente_id = str(uuid.uuid4())

            docentes = {
                "_id": docente_id,
                "nombre_docente": nombre_docente,
                "apellido_docente": apellido_docente
            }
            result = collection.insert_one(docentes)
            client.close()

            if result:
                return jsonify(success=True)
            else: 
                return jsonify(success=False, message=f'Ha surgido un error al agregar al docente {nombre_docente}.')
        else:
            return jsonify(success=False, message=f'Ha surgido un problema con la conexión.')
    except Exception as e:
        print("Error:", e)
        return jsonify(success=False)
    
@docentes_ruta.route('/eliminar/docente/<_id>', methods=['DELETE'])
def delete_docente(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.docentes
        result = collection.delete_one({"_id": _id})
        if result.deleted_count == 1:
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Ha surgido un problema al eliminar al docente.')
    except Exception as e:
        return jsonify(success=False)
    finally:
        client.close()

@docentes_ruta.route('/api/docentes', methods=['GET'])
def obtener_docentes():
    try:
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection = db.docentes

        # Excluir el campo "_id" de los resultados
        resultados = collection.find({})

        # Convertir los resultados a una lista de diccionarios
        docentes = [docente for docente in resultados]

        # Cerrar la conexión con MongoDB
        client.close()

        # Devolver los resultados como JSON
        return jsonify({"docentes": docentes}), 200

    except Exception as e:
        print("error")
