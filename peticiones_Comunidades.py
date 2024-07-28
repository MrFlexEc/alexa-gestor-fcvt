from flask import Blueprint,Flask, request, jsonify, render_template
from conexion import *
from flask_login import login_required

import uuid

comunidades_ruta = Blueprint('comunidades', __name__)

# Ruta principal que renderiza un archivo HTML
@comunidades_ruta.route('/comunidades/')
def ingreso_comunidades():
    return render_template('Comunidades.html')
# Ruta para manejar solicitudes GET a /api/data
@comunidades_ruta.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"mensaje": "Solicitud GET recibida"})

# Ruta para manejar solicitudes PUT a /api/data
@comunidades_ruta.route('/agregar/comunidad', methods=['PUT'])
def add_comunidad():
    data = request.get_json()
    print("Datos recibidos:", data)
    
    # Extraer los campos del JSON recibido
    nombre_comunidad = data.get("nombre_comunidad","").strip()
    periodo_comunidad = data.get("periodo_comunidad")
    ubicacion_comunidad = data.get("ubicacion_comunidad")
    observaciones = data.get("observaciones")
    carrera_id = data.get("carrera_id")
    docente_id = data.get("docente_id")
    
    # Validar que todos los campos requeridos estén presentes
    if not nombre_comunidad or not periodo_comunidad or not ubicacion_comunidad or not carrera_id or not docente_id:
        return jsonify(success=False, message='Faltan campos por completar')

    # Conectar a MongoDB
    client = connect_to_mongodb()

    try:
        if client:
            print("Conexión exitosa a MongoDB")
            db = client.AlexaGestor
            collection_comunidades = db.comunidades
            collection_docentes = db.docentes
            collection_carreras = db.carreras
            
            # Verificar existencia de id_docente en la colección docentes
            docente = collection_docentes.find_one({"_id": docente_id})
            
            
            # Verificar existencia de id_carrera en la colección carreras
            carrera = collection_carreras.find_one({"_id": carrera_id})
            if carrera:
                print(carrera)
            
            # Generar un ID único para la comunidad
            comunidad_id = str(uuid.uuid4())

            # Crear el documento para insertar
            comunidad = {
                "_id": comunidad_id,
                "nombre_comunidad": nombre_comunidad,
                "periodo_comunidad": periodo_comunidad,
                "ubicacion_comunidad": ubicacion_comunidad,
                "observaciones": observaciones,
                "carrera_id": carrera_id,
                "docente_id": docente_id
             }
            
            # Insertar el documento en la colección
            result = collection_comunidades.insert_one(comunidad)
            print("Comunidad agregada con ID:", comunidad_id)
            if result:
                return jsonify(success=True)
            else:
                return jsonify(success=False, message=f'Ha surgido un error al agregar la comunidad {nombre_comunidad}.')

    except Exception as e:
        return jsonify(success=False)
    finally:
        client.close()
    
@comunidades_ruta.route('/eliminar/comunidad/<_id>', methods=['DELETE'])
def delete_comunidad(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.comunidades
        result = collection.delete_one({"_id": _id})
        if result.deleted_count == 1:
            print("eliminado con exito")
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Ha surgido un problema al eliminar la comunidad.')
    except Exception as e:
            return jsonify(success=False)
    finally:
        client.close()
@comunidades_ruta.route('/api/comunidades', methods=['GET'])
def obtener_comunidades():
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection_comunidades = db.comunidades
        collection_docentes = db.docentes
        collection_carreras = db.carreras

        comunidades = list(collection_comunidades.find({}))
        
        for comunidad in comunidades:
            docente_id = comunidad.get("docente_id")
            carrera_id = comunidad.get("carrera_id")
            
            # Imprime los IDs para depuración
            print(f"Buscando docente_id: {docente_id}")
            print(f"Buscando carrera_id: {carrera_id}")
            
            # Consulta para docente
            docente = collection_docentes.find_one({"_id": docente_id}, {"_id": 0, "nombre_docente": 1, "apellido_docente": 1})
            print(f"Docente encontrado: {docente}")
            
            # Consulta para carrera usando cadena
            carrera = collection_carreras.find_one({"_id": carrera_id}, {"_id": 0, "nombre_carrera": 1})
            print(f"Carrera encontrada: {carrera}")
            
            # Asigna nombres a la comunidad
            comunidad["nombre_docente"] = f"{docente['nombre_docente']} {docente['apellido_docente']}" if docente else "Desconocido"
            comunidad["nombre_carrera"] = f"{carrera['nombre_carrera']}" if carrera else "Desconocido"
        
        return jsonify({"comunidades": comunidades}), 200
    except Exception as e:
        # Imprime el error para depuración
        print(f"Error: {e}")
        return jsonify(success=False)
    finally:
        client.close()

# Manejo de errores 404 (No encontrado)
@comunidades_ruta.errorhandler(404)
def not_found(error):
    return jsonify({"error": "No encontrado"}), 404

# Manejo de errores 500 (Error interno del servidor)
@comunidades_ruta.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

# Si el script se ejecuta directamente, inicia el servidor de desarrollo de Flask
