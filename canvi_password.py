import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import argparse

# Funció per connectar-se a Google Workspace
def connectar_amb_google(credentials_file, admin_email):
    scopes = ['https://www.googleapis.com/auth/admin.directory.user']
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=scopes)
    delegated_credentials = credentials.with_subject(admin_email)
    service = build('admin', 'directory_v1', credentials=delegated_credentials)
    return service

# Funció per canviar la contrasenya i forçar el canvi en el proper login
def canviar_password(service, email, new_password):
    try:
        body = {
            'password': new_password,
            'changePasswordAtNextLogin': True
        }
        service.users().update(userKey=email, body=body).execute()
        print(f"Contrasenya actualitzada per a {email}. Se li forçarà a canviar-la al proper login.")
        return True
    except Exception as e:
        print(f"No s'ha pogut actualitzar la contrasenya per a {email}: {e}")
        return False

if __name__ == '__main__':
    # Parser per recollir els paràmetres
    parser = argparse.ArgumentParser(description='Canviar la contrasenya d\'un usuari i forçar un canvi en el proper login.')
    parser.add_argument('--credentials-file', type=str, required=True, help='El fitxer de credencials JSON de la Service Account.')
    parser.add_argument('--admin-email', type=str, required=True, help='El correu electrònic de l\'administrador del domini.')
    parser.add_argument('--email', type=str, required=True, help='El compte de correu electrònic per al qual es vol canviar la contrasenya.')
    parser.add_argument('--password', type=str, required=True, help='La nova contrasenya per al compte de correu electrònic.')

    # Obtenir els arguments
    args = parser.parse_args()

    # Connectar-se a Google Workspace
    service = connectar_amb_google(args.credentials_file, args.admin_email)

    # Canviar la contrasenya
    canviar_password(service, args.email, args.password)
