from conexion import *
import unicodedata
import re 
from unidecode import unidecode


def normalizar_texto(texto):
    """ Normaliza el texto eliminando tildes y convirtiendo a minúsculas. """
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()

def seleccionar_horario(dato):
    palabras = dato.split()
    
    nombre = None
    apellido = None

    if len(palabras) >= 2:
        nombre = palabras[0]
        apellido = palabras[1]
    elif len(palabras) == 1:
        nombre = palabras[0]

    nombre_normalizado = normalizar_texto(nombre) if nombre else None
    apellido_normalizado = normalizar_texto(apellido) if apellido else None

    client = connect_to_mongodb()
    if client:
        try:
            db = client.AlexaGestor
            collection = db.horariosIndividual
            
            # Construcción de la consulta para nombre y apellido en cualquier orden
            query = {"$or": []}

            if nombre_normalizado and apellido_normalizado:
                query["$or"].append({"horario_nombre_imagen": {"$regex": f"^{nombre_normalizado}.*{apellido_normalizado}$", "$options": "i"}})
                query["$or"].append({"horario_nombre_imagen": {"$regex": f"^{apellido_normalizado}.*{nombre_normalizado}$", "$options": "i"}})
            
            if nombre_normalizado:
                query["$or"].append({"horario_nombre_imagen": {"$regex": f"^{nombre_normalizado}.*$", "$options": "i"}})
            
            if apellido_normalizado:
                query["$or"].append({"horario_nombre_imagen": {"$regex": f"^{apellido_normalizado}.*$", "$options": "i"}})

            if not query["$or"]:
                client.close()
                return None, None

            horario = collection.find_one(
                query,
                {"_id": 0, "imagen_ids": 1, "horario_nombre_imagen": 1}
            )
            
            if horario:
                imagen_ids = horario.get("imagen_ids", [])
                nombre_completo = horario.get("horario_nombre_imagen", "")
                client.close()
                return imagen_ids, nombre_completo
            else:
                client.close()
                return None, None
        
        except Exception as e:
            print(f"Error al buscar el horario: {e}")
            client.close()
            return None, None
    
    else:
        print("No se pudo conectar a MongoDB Atlas")
        return None, None
    
dato="zamora"    
ids, nombre = seleccionar_horario(dato)
print(f"Entrada: {dato} => IDs: {ids}, Nombre: {nombre}")