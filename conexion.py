
# Configura la conexión a MongoDB Atlas
from pymongo import MongoClient

def connect_to_mongodb():
    try:
        client = MongoClient("mongodb+srv://alexatesis2024LA:alexatesis2024LA@cluster0.kpmldgn.mongodb.net/")

        return client # Devuelve el cliente MongoDB, la base de datos y el sistema de archivos de la base de datos
    except Exception as e:
        print("Error al conectar a MongoDB Atlas:", e)
        return None


