from flask import Blueprint, Flask, request, jsonify, render_template
from conexion import *
import uuid
import os
import base64

procesos_ruta = Blueprint('procesos', __name__)

@procesos_ruta.route('/procesos/')
def ingreso_procesos():
    return render_template('Procesos.html')

@procesos_ruta.route('/agregar/proceso', methods=['POST'])
def add_proceso():
    try:
        nombre_pa = request.form.get("nombre_pa", '').strip()
        fecha_pa_inicio = request.form.get("fecha_pa_inicio")
        fecha_pa_fin = request.form.get("fecha_pa_fin")
        observaciones = request.form.get("observaciones")
        docente_id = request.form.get("docente_id")
        carrera_id = request.form.get("carrera_id")


        if not nombre_pa or not docente_id or not fecha_pa_fin or not fecha_pa_inicio or not carrera_id:
            return jsonify(success=False, message='Faltan campos por completar')

        # Conectar a MongoDB
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection_procesoA = db.procesosAcademicos
        collection_docentes = db.docentes
        collection_carreras = db.carreras


        # Verificar si el docente existe
        docente = collection_docentes.find_one({"_id": docente_id})
        if not docente:
            client.close()
            return jsonify({"error": "El id_docente no existe"}), 400
        carrera = collection_carreras.find_one({"_id": carrera_id})
        if not docente:
            client.close()
            return jsonify({"error": "El id_docente no existe"}), 400
        # Guardar la imagen en MongoDB
        pa_id = str(uuid.uuid4())

        # Crear el documento para insertar en MongoDB
        procesosAcademicos = {
            "_id": pa_id,
            "nombre_pa":nombre_pa,
            "fecha_pa_fin":fecha_pa_fin,
            "fecha_pa_inicio":fecha_pa_inicio,
            "observaciones":observaciones,
            "docente_id": docente_id,
            "carrera_id":carrera_id
        }

        # Insertar el documento en la colección de horarios
        result=collection_procesoA.insert_one(procesosAcademicos)

        client.close()
        if result:
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Ha surgido un error al agregar al docente {nombre_docente}.')
    except Exception as e:
        print("Error")
@procesos_ruta.route('/eliminar/proceso/<_id>', methods=['DELETE'])
def delete_horario(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.procesosAcademicos
        result = collection.delete_one({"_id": _id})
        if result.deleted_count == 1:
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=f'Ha surgido un problema al eliminar al docente.')
    except Exception as e:
        return jsonify(success=False)
    finally:
        client.close()


@procesos_ruta.route('/api/procesos', methods=['GET'])
def obtener_procesos():
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection_procesosA = db.procesosAcademicos
        collection_docentes = db.docentes
        collection_carreras = db.carreras


        procesos = list(collection_procesosA.find({}))
        for proceso in procesos:
            carrera_id = proceso.get("carrera_id")
            docente_id = proceso.get("docente_id")
            carrera = collection_carreras.find_one({"_id": carrera_id}, {"_id": 0, "nombre_carrera": 1})
            docente = collection_docentes.find_one({"_id": docente_id}, {"_id": 0, "nombre_docente": 1, "apellido_docente": 1})
            if docente or carrera:
                proceso["nombre_carrera"] = carrera["nombre_carrera"] if carrera else "Desconocido"
                proceso["nombre_docente"] = f"{docente['nombre_docente']} {docente['apellido_docente']}"
            else:
                proceso["nombre_docente"] = "Desconocido"

        
        return jsonify({"procesos": procesos}), 200
    except Exception as e:
        print(f"Error en obtener_procesos(): {str(e)}")
    finally:
        client.close()

