from flask import Blueprint, request, jsonify, render_template, session

from conexion import connect_to_mongodb
import uuid

carreras_ruta = Blueprint('carreras', __name__)

# Función para verificar si el usuario está autenticado
def verificar_autenticacion():
    # Verificar si 'usuario_id' está en la sesión
    if 'usuario_id' not in session:
        # Redireccionar a la página de login si no está autenticado
        return False
    return True
# Ruta principal que renderiza un archivo HTML
@carreras_ruta.route('/carreras/')
def home():
    if not verificar_autenticacion():
            return render_template('Login.html')  # Redirecciona al login si no está autenticado
    return render_template('Carreras.html')
# Ruta para manejar solicitudes GET a /api/data
@carreras_ruta.route('/obtener_carreras', methods=['GET'])
def get_carreras():
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.carreras
        carreras = list(collection.find({}, {"_id": 1, "nombre_carrera": 1}))
        return jsonify(carreras), 200
    except Exception as e:
        print("error")
    finally:
        client.close()

# Ruta para manejar solicitudes PUT a /api/data
@carreras_ruta.route('/agregar/carrera', methods=['PUT'])
def add_carrera():
    data = request.get_json()
    nombre_carrera = data.get("nombre_carrera")
    descripcion = data.get("descripcion")
    
    if not nombre_carrera or not descripcion:
        return jsonify(success=False, message='Faltan campos por completar')

    client = connect_to_mongodb()

    try:
        if client:
            print("Conexión exitosa a MongoDB")
            db = client.AlexaGestor
            collection = db.carreras
            
            # Generar un ID único
            carrera_id = str(uuid.uuid4())

            carrera = {
                "_id": carrera_id,
                "nombre_carrera": nombre_carrera,
                "descripcion": descripcion
            }
            result = collection.insert_one(carrera)
            client.close()
            if result:
                return jsonify(success=True)
            else:
                return jsonify(success=False, message=f'Ha surgido un error al agregar al docente {nombre_carrera}.')
        else:
            return jsonify(success=False, message=f'Ha surgido un problema con la conexión.')
    except Exception as e:
        print("Error:", e)

@carreras_ruta.route('/eliminar/carrera/<_id>', methods=['DELETE'])
def delete_carrera(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.carreras
        result = collection.delete_one({"_id": _id})
        if result.deleted_count == 1:
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Ha surgido un problema al eliminar la carrera.')
    except Exception as e:
        print("Error")
    finally:
        client.close()

@carreras_ruta.route('/api/carreras', methods=['GET'])
def obtener_carreras():
    try:
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection = db.carreras

        # Excluir el campo "_id" de los resultados
        resultados = collection.find({})

        # Convertir los resultados a una lista de diccionarios
        carreras = [carrera for carrera in resultados]

        # Cerrar la conexión con MongoDB
        client.close()

        # Devolver los resultados como JSON
        return jsonify({"carreras": carreras}), 200

    except Exception as e:
        print("error")
