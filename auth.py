from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Directorio de las credenciales
directorio_credenciales = "credentials_module.json"

# Función centralizada para manejar la autenticación
def login():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(directorio_credenciales)
    
    if gauth.credentials is None:
        # No se encontraron credenciales, autenticando de forma local
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        try:
            # Intentar refrescar el token de acceso
            gauth.Refresh()
        except Exception as e:
            print(f"Error al refrescar el token de acceso: {e}")
            gauth.LocalWebserverAuth()  # Reautenticar si falla el refresco
    else:
        gauth.Authorize()

    # Guardar las credenciales actualizadas
    gauth.SaveCredentialsFile(directorio_credenciales)
    return GoogleDrive(gauth)