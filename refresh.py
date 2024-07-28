from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Configuración del archivo de credenciales
directorio_credenciales = "credentials_module.json"
archivo_client_secrets = "client_secrets.json"

def obtener_refresh_token():
    gauth = GoogleAuth()

    # Cargar el archivo de secretos del cliente
    gauth.LoadClientConfigFile(archivo_client_secrets)

    # Autenticación local
    gauth.LocalWebserverAuth()  # Abre un navegador para que el usuario se autentique

    # Guardar las credenciales en un archivo
    gauth.SaveCredentialsFile(directorio_credenciales)

    # Crear una instancia de GoogleDrive
    drive = GoogleDrive(gauth)

    print("Autenticación completada.")
    print("refresh_token:", gauth.credentials.refresh_token)

if __name__ == "__main__":
    obtener_refresh_token()