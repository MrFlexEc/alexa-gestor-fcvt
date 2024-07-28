from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
import fitz  # PyMuPDF
import time, re
from auth import login  # Tu función de autenticación con Google Drive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from conexion import *  # Tu función de conexión a MongoDB si es necesario
import uuid
import pytesseract
from PIL import Image
horarios_ruta = Blueprint('horarios', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
horarios_ruta.config = {'UPLOAD_FOLDER': UPLOAD_FOLDER}

# Asegúrate de que el directorio de subidas exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Función para verificar si la extensión del archivo está permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Función para subir archivo a Google Drive y devolver el ID
def subir_archivo_a_drive(ruta_archivo, id_folder):
    credenciales = login()  # Función para obtener credenciales de Google Drive

    archivo = credenciales.CreateFile({
        'title': os.path.basename(ruta_archivo),
        'parents': [{"kind": "drive#fileLink", "id": id_folder}]
    })
    archivo.SetContentFile(ruta_archivo)
    archivo.Upload()
    return archivo['id'], archivo['title']  # Devuelve el ID del archivo subido en Google Drive



def subir_imagen_a_drive(credenciales, image_path, folder_id, image_title):
    try:
        imagen_drive = credenciales.CreateFile({
            'title': image_title,
            'parents': [{"kind": "drive#fileLink", "id": folder_id}]
        })
        imagen_drive.SetContentFile(image_path)
        imagen_drive.Upload()
        file_id = imagen_drive['id']  # Obtén el ID del archivo subido
        return file_id
    except Exception as e:
        print(f"Error al subir la imagen a Google Drive: {str(e)}")
        return None  # Retorna None en caso de error

def extraer_lineas_con_profesor(texto):
    # Patrón para buscar líneas que contienen "Profesor" y capturar títulos y nombres
    patron = r"Profesor\s+((?:\w+\.\s*)?[A-ZÁÉÍÓÚÜÑñ][a-záéíóúüññ\s\.]+(?:,\s*\w+\s*)?)"
    coincidencias = re.findall(patron, texto, re.IGNORECASE)
    return coincidencias


def extraer_nombres_validos(texto):
    # Patrón para buscar palabras que comienzan con mayúscula y tienen más de 3 letras, todas en mayúscula
    patron = r"\b[A-ZÁÉÍÓÚÜÑ]{4,}\b"  # Busca palabras de 4 letras en adelante, todas en mayúscula
    coincidencias = re.findall(patron, texto)
    return coincidencias

def extraer_nombres_final(nombres_extraccion):
    # Tomar solo los dos primeros nombres de la lista
    if len(nombres_extraccion) > 1:
        return nombres_extraccion[:2]
    else:
        return nombres_extraccion
    
@horarios_ruta.route('/horarios/')
def home():
    return render_template('Horarios.html')

@horarios_ruta.route('/upload_and_add_horario', methods=['POST'])
def upload_and_process():
    if 'file' not in request.files:
        return jsonify(success=False, message='No se subio ningun archivo')

    file = request.files['file']
    periodo_horario = request.form.get("periodo_horario")
    observacion = request.form.get("observacion")
    if not periodo_horario:
        return jsonify(success=False, message='Faltan campos por completar')

    id_folder = '1COEo694kE7LcvZmBaPtviknw7ocky6PU'  # ID de la carpeta en Google Drive

    if file.filename == '':
        return jsonify(success=False, message='No seleccionaste ningun archivo . ')

    if file and allowed_file(file.filename):
        secure_name = secure_filename(file.filename)
        file_path = os.path.join(horarios_ruta.config['UPLOAD_FOLDER'], secure_name)
        file.save(file_path)

        try:
            # Enviar mensaje de espera al usuario
            message = 'Procesando... Esto puede tardar un momento.'

            # Subir archivo a Google Drive y obtener el ID del archivo
            id_drive,title = subir_archivo_a_drive(file_path, id_folder)

            # Conectar con MongoDB y guardar información del horario
            client = connect_to_mongodb()
            if client:
                db = client.AlexaGestor
                collection_horarios = db.horarios

                horario_id = str(uuid.uuid4())

                horarios = {
                    "_id": horario_id,
                    "periodo_horario": periodo_horario,
                    "observacion": observacion,
                    "id_drive": id_drive,  # Agrega el ID de Google Drive aquí
                    "title":title
                    # Puedes agregar más campos según sea necesario
                }

                collection_horarios.insert_one(horarios)
                # Cerrar conexión con MongoDB
                client.close()

                # Subir archivo a Google Drive y obtener el ID del archivo y el nombre final
                imagen_ids, nombrefinal_str = convertir_pdf_a_imagenes_y_subir_a_drive(file_path,horario_id)
                #Proceso para enviear a la nueva base de datos el id y el nombre del horarios del docente

                # Eliminar el archivo local después de procesarlo y subirlo
                os.remove(file_path)
                if convertir_pdf_a_imagenes_y_subir_a_drive:
                    return jsonify(success=True)
        except Exception as e:
            return jsonify(success=False)

    else:
        return jsonify(success=False, message='Tipo de archivo no permitido.')

    return redirect(url_for('horarios.ingreso_comunidades'))

# Función para convertir PDF a imágenes y subirlas a Google Drive
def convertir_pdf_a_imagenes_y_subir_a_drive(input_pdf,horario_id, dpi=300):
    credenciales = login()  # Asume que esta función maneja la autenticación con Google Drive

    imagen_ids = []  # Lista para almacenar los IDs de las imágenes subidas
    nombrefinal_str = ""

    try:
        id_folder = '18KiGWZdqFzHS9eSpeBjetyH3YW4g3lce'
        documento = fitz.open(input_pdf)
        nombres_profesores = []

        for numero_pagina in range(len(documento)):
            pagina = documento.load_page(numero_pagina)
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = pagina.get_pixmap(matrix=mat)

            output_image_path = os.path.join(horarios_ruta.config['UPLOAD_FOLDER'], f"pagina_{numero_pagina + 1}.png")
            pix.save(output_image_path)
            texto = pytesseract.image_to_string(Image.open(output_image_path), lang='spa', config='--psm 6 --oem 1')
            
            lineas_con_profesor = extraer_lineas_con_profesor(texto)
            if not lineas_con_profesor:
                nombrefinal = f"NO RECONOCIDO {numero_pagina + 1}"
                
            else:
                for linea in lineas_con_profesor:
                    nombres_extraccion = extraer_nombres_validos(linea)
                    if nombres_extraccion:
                        nombres_profesores.extend(nombres_extraccion)
                        nombrefinal = extraer_nombres_final(nombres_extraccion)
                        if nombrefinal and all(nombrefinal):
                            print(f"Nombre final: {nombrefinal}")
                        else:
                            nombrefinal = f"DocenteNoReconocido_{numero_pagina + 1}"

            nombrefinal_str = " ".join(nombrefinal)  # Concatena los nombres con un espacio
            file_id = subir_imagen_a_drive(credenciales, output_image_path, id_folder, nombrefinal_str)
            upload_and_process_image(horario_id, file_id, output_image_path ,nombrefinal_str)

            if file_id:
                imagen_ids.append(file_id)
            
            del pix
            time.sleep(1)
            try:
                os.remove(output_image_path)
                #print(f"Archivo local eliminado: {output_image_path}")
            except Exception as e:
                print(f"No se pudo eliminar el archivo: {str(e)}")

    except Exception as e:
        print(f"Error al convertir PDF y subir imágenes a Google Drive: {str(e)}")

    finally:
        if documento:
            documento.close()

    return imagen_ids, nombrefinal_str


def upload_and_process_image(horario_id, imagen_ids, imagen_path, nombrefinal_str):
    client = connect_to_mongodb()
    if client:
        db = client.AlexaGestor
        collection_horarioI = db.horariosIndividual
        
        # Generar un ID único para este documento en la colección horariosIndividual
        horarioIndividual_id = str(uuid.uuid4())
        # Crear el documento a insertar en la colección horariosIndividual
        horariosIndividuales = {
            "_id": horarioIndividual_id,  # ID único del documento
            "imagen_ids": imagen_ids,     # Lista de IDs de imágenes relacionadas
            "horario_nombre_imagen": nombrefinal_str,  # Nombre de la imagen
            "horario_id": horario_id      # ID del horario relacionado
        }
        
        # Insertar el documento en la colección
        collection_horarioI.insert_one(horariosIndividuales)

        client.close()
    else:
        print("Ha surgido un problema al conectar con MongoDB.")
@horarios_ruta.route('/api/horarios', methods=['GET'])
def obtener_horarios():
    try:
        client = connect_to_mongodb()
        db = client.AlexaGestor
        collection = db.horarios

        # Excluir el campo "_id" de los resultados
        resultados = collection.find({})

        # Convertir los resultados a una lista de diccionarios
        horarios = [horario for horario in resultados]

        # Cerrar la conexión con MongoDB
        client.close()

        # Devolver los resultados como JSON
        return jsonify({"horarios": horarios}), 200

    except Exception as e:
        print("ERROR")
@horarios_ruta.route('/eliminar/horario/<_id>', methods=['DELETE'])
def delete_horario(_id):
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection_I = db.horariosIndividual

        # Obtener todos los documentos individuales que coincidan con el _id de horario
        horariosIndividuales = list(collection_I.find({"horario_id": _id}))
        
        
        for horarioIndividual in horariosIndividuales:
            # Obtener los IDs de las imágenes de OneDrive asociadas
            imagen_ids = horarioIndividual.get("imagen_ids", [])

            # Imprimir los IDs de las imágenes para verificar su contenido
            #print(f"IDs de imágenes de OneDrive para horario individual {_id}: {imagen_ids}")
            borrar_horarioimagen(imagen_ids)            
            
            # Eliminar documentos individuales de la colección horariosIndividual
            collection_I.delete_many({"horario_id": _id})

        # Eliminar horario principal y otros procesos
        collection = db.horarios
        horario = collection.find_one({"_id": _id})
        if horario:
            id_googledrive = horario.get("id_drive")
            if id_googledrive:
                borrar_horarioOnedrive(id_googledrive)
            collection.delete_one({"_id": _id})
            
        return jsonify(success=True)
    except Exception as e:
        print("ERROR")
    finally:
        client.close()

def borrar_horarioimagen(id_archivo):
    credenciales = login()
    try:
        print(f"Intentando eliminar archivo de imagen de OneDrive con ID: {id_archivo}")
        archivo = credenciales.CreateFile({'id': id_archivo})
        print(f"Obteniendo metadatos del archivo de imagen con ID: {id_archivo}")
        archivo.FetchMetadata()  # Verificar si el archivo existe
        print(f"Eliminando archivo de imagen con ID: {id_archivo}")
        archivo.Delete()  # Eliminar el archivo de OneDrive
        print(f"Archivo de imagen con ID: {id_archivo} eliminado correctamente")
        return True
    except FileNotFoundError:
        print(f"Error: Archivo de imagen con ID {id_archivo} no encontrado en OneDrive")
        return False
    except Exception as e:
        print(f"Error al borrar archivo de imagen de OneDrive con ID {id_archivo}: {str(e)}")
        return False

def borrar_horarioOnedrive(id_archivo):
    credenciales = login()
    try:
        print(f"Creando archivo con ID: {id_archivo}")
        archivo = credenciales.CreateFile({'id': id_archivo})
        print(f"Obteniendo metadatos del archivo con ID: {id_archivo}")
        archivo.FetchMetadata()  # Verificar si el archivo existe
        print(f"Eliminando archivo con ID: {id_archivo}")
        archivo.Delete()  # Eliminar el archivo de OneDrive
        print(f"Archivo con ID: {id_archivo} eliminado correctamente")
        return True
    except Exception as e:
        print(f"Error al borrar archivo de OneDrive con ID: {id_archivo}: {str(e)}")
        return False
@horarios_ruta.route('/api/horarios_individual', methods=['GET'])
def obtener_horariosIn():
    client = connect_to_mongodb()
    try:
        db = client.AlexaGestor
        collection = db.horarios
        collection_I = db.horariosIndividual

        horarios_individuales = list(collection_I.find({}))
        
        for horario in horarios_individuales:
            horario_id = horario.get("horario_id")
            
            horario_principal = collection.find_one({"_id": horario_id}, {"_id": 0, "title": 1})
            
            horario["title"] = horario_principal["title"] if horario_principal else "Desconocido"
        
        return jsonify({"horarios_individuales": horarios_individuales}), 200
    except Exception as e:
        print(  "eRROR")
    finally:
        client.close()