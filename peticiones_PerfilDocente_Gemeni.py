from flask import Blueprint, Flask, request, jsonify, render_template
from conexion import *
from scholarly import scholarly
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
import os
import base64
from threading import Thread
import time
from datetime import datetime

perfil_ruta = Blueprint('Perfil', __name__)

@perfil_ruta.route('/perfil_scholar/')
def ingreso_procesos():
    return render_template('Perfil_Scholar.html')


# Función para la actualización periódica de perfilesGoogle
# Función para procesar y almacenar datos en perfilesGoogle
def process_and_store_data(perfilgoogle_id, docente_id, perfil_id):
    try:
        # Recopilar detalles del autor y sus publicaciones
        author_filled, publications_details = fetch_author_details(perfilgoogle_id)

        # Crear el documento para la colección de perfilesGoogle
        perfil_Google = {
            'name': author_filled['name'],
            'affiliation': author_filled.get('affiliation', 'No contiene'),
            'email': author_filled.get('email', 'No contiene'),
            'interests': author_filled['interests'],
            'publications': publications_details,
            'last_updated': datetime.utcnow(),
            'perfil_id': perfil_id
        }

        # Insertar o actualizar el documento en la colección de perfilesGoogle
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection_perfilesGoogle = db.perfilesGoogle
        result = collection_perfilesGoogle.update_one(
            {"perfil_id": perfil_id},
            {"$set": perfil_Google},
            upsert=True  # Insertar si no existe, actualizar si existe
        )

        if result.modified_count > 0:
            print(f"Perfil actualizado: {perfil_id}")
        elif result.upserted_id is not None:
            print(f"Nuevo perfil insertado: {perfil_id}")

    except Exception as e:
        print(f"Error al procesar datos: {e}")

# Función para obtener detalles del autor y sus publicaciones
def fetch_author_details(author_id):
    author = scholarly.search_author_id(author_id)
    author_filled = scholarly.fill(author)

    # Crear una lista de tareas para las publicaciones del autor
    tasks = []
    with ThreadPoolExecutor() as executor:
        for pub in author_filled['publications']:
            tasks.append(executor.submit(fetch_publication_details, pub))

        # Recoger los resultados de las tareas conforme se vayan completando
        publications_details = [future.result() for future in tasks]

    return author_filled, publications_details

# Función para obtener detalles de publicaciones
def fetch_publication_details(pub):
    pub_filled = scholarly.fill(pub)
    return {
        "title": pub_filled['bib'].get('title', 'No contiene'),
        "year": pub_filled['bib'].get('pub_year', 'No contiene'),
        "citations": pub_filled.get('num_citations', 'No contiene'),
        "authors": pub_filled['bib'].get('author', 'No contiene'),
        "abstract": pub_filled['bib'].get('abstract', 'No contiene')
    }

# Ruta para agregar un perfil
@perfil_ruta.route('/agregar/perfil', methods=['POST'])
def add_perfil():
    try:
        perfilgoogle_id = request.form.get("perfilgoogle_id")
        docente_id = request.form.get("docente_id")
        author_name = request.form.get("author_name")
        if not author_name or author_name == "ID de autor no válido":
            return jsonify(success=False, message='El autor no puede estar vacio ni ser invalido')


        if not docente_id or not perfilgoogle_id:
            return jsonify(success=False, message='Faltan campos por completar')
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection_perfiles = db.perfiles
        collection_docentes = db.docentes

        # Verificar si el docente existe
        docente = collection_docentes.find_one({"_id": docente_id})
        if not docente:
            return jsonify({"error": "El id_docente no existe"}), 400

        perfil_id = str(uuid.uuid4())

        # Crear el documento para insertar en MongoDB
        perfil = {
            "_id": perfil_id,
            "perfilgoogle_id": perfilgoogle_id,
            "docente_id": docente_id,
        }

        # Insertar el documento en la colección de perfiles
        insercion = collection_perfiles.insert_one(perfil)

        if insercion.inserted_id:
            # Iniciar el procesamiento en un hilo separado
            Thread(target=process_and_store_data, args=(perfilgoogle_id, docente_id, perfil_id)).start()

            return jsonify(success=True)

        else:
            return jsonify(success=False, message=f'Ha surgido un error al agregar el perfil')

    except StopIteration:
        return jsonify(success=False, message=f'No se encontro el ID proporcionado en google Scholar')

    except Exception as e:
        print("Error")
# Función para la actualización periódica de perfilesGoogle
def periodic_update():
    while True:
        try:
            print("Actualización periódica en proceso...")
            client = connect_to_mongodb()
            db = client.AlexaGestor
            # Obtener todos los perfiles de la colección perfiles
            collection_perfiles = db.perfiles

            for perfil in collection_perfiles.find({}):
                perfilgoogle_id = perfil['perfilgoogle_id']
                docente_id = perfil['docente_id']
                perfil_id = perfil['_id']

                # Procesar y almacenar datos actualizados en perfilesGoogle
                Thread(target=process_and_store_data, args=(perfilgoogle_id, docente_id, perfil_id)).start()

        except Exception as e:
            print(f"Error en la actualización periódica: {e}")

        # Intervalo de actualización (24 horas en este ejemplo)
        time.sleep(86400)  # 24 horas en segundos
@perfil_ruta.route('/eliminar/perfil/<_id>', methods=['DELETE'])
def delete_perfil(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        
        # Eliminar perfil de la colección 'perfiles'
        collection_perfiles = db.perfiles
        result_perfiles = collection_perfiles.delete_one({"_id": _id})
        
        # Eliminar perfil correspondiente de la colección 'perfilesGoogle'
        collection_perfilesGoogle = db.perfilesGoogle
        result_perfilesGoogle = collection_perfilesGoogle.delete_one({"perfil_id": _id})
        
        if result_perfiles.deleted_count == 1:
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Ha surgido un error al eliminar perfil.')
        
    except Exception as e:
        print("Error")
    finally:
        client.close()


@perfil_ruta.route('/api/perfiles', methods=['GET'])
def obtener_perfiles():
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection_perfiles = db.perfiles
        collection_docentes = db.docentes
          
        perfiles = list(collection_perfiles.find({}))
        for perfil in perfiles:
            docente_id = perfil.get("docente_id")
            docente = collection_docentes.find_one({"_id": docente_id}, {"_id": 0, "nombre_docente": 1, "apellido_docente": 1})
            if docente:
                perfil["nombre_docente"] = f"{docente['nombre_docente']} {docente['apellido_docente']}"
            else:
                perfil["nombre_docente"] = "Desconocido"

        
        return jsonify({"perfiles": perfiles}), 200
    except Exception as e:
        print(f"Error en obtener_perfiles(): {str(e)}")
    finally:
        client.close()
@perfil_ruta.route('/send_author_id', methods=['POST'])
def send_author_id():
    data = request.get_json()
    author_id = data.get('author_id')
    
    # Busca y llena la información del autor
    author = scholarly.search_author_id(author_id)
    author_filled = scholarly.fill(author)

    # Extrae la información que deseas enviar al frontend
    author_name = author_filled.get('name')
    # Imprime información del autor en la salida capturada
    print(f"Nombre: {author_name}")
    
    return jsonify({'author_name': author_name})
    
# Iniciar la actualización periódica en un hilo separado al iniciar la aplicación Flask
Thread(target=periodic_update).start()
