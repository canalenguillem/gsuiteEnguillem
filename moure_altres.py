import pandas as pd
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import argparse
from datetime import datetime

# Funció per autenticar-se amb la Google API
def connectar_amb_google(credentials_file, admin_email):
    scopes = ['https://www.googleapis.com/auth/admin.directory.user']
    
    # Carregar les credencials de la Service Account
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=scopes)
    
    # Delegar l'autoritat al compte d'administrador
    delegated_credentials = credentials.with_subject(admin_email)
    
    # Construir el servei de Google Admin SDK
    service = build('admin', 'directory_v1', credentials=delegated_credentials)
    return service

# Funció per moure un usuari a una altra unitat organitzativa
def moure_usuari_a_una_altra_unitat(service, email, nova_unitat):
    try:
        service.users().update(userKey=email, body={'orgUnitPath': nova_unitat}).execute()
        print(f"Usuari {email} mogut correctament a {nova_unitat}.")
        return True
    except Exception as e:
        print(f"No s'ha pogut moure l'usuari {email} a {nova_unitat}: {e}")
        return False

# Funció per obtenir tots els usuaris d'una unitat organitzativa
def obtenir_usuaris_unitat(service, org_unit_path):
    try:
        results = service.users().list(customer='my_customer', query=f'orgUnitPath={org_unit_path}', maxResults=500).execute()
        usuaris = results.get('users', [])
        return usuaris
    except Exception as e:
        print(f"No s'han pogut obtenir els usuaris de la unitat organitzativa {org_unit_path}: {e}")
        return []

# Funció principal per comparar els usuaris del CSV amb els usuaris de la unitat organitzativa
def comparar_i_moure_usuaris(credentials_file, admin_email, csv_file, org_unit_altres):
    # Connectar-se amb l'API de Google
    service = connectar_amb_google(credentials_file, admin_email)

    # Llegir el CSV
    df = pd.read_csv(csv_file)

    # Obtenir la unitat organitzativa del CSV
    org_unit = df['Org Unit Path'].iloc[0]  # Assumim que tots els usuaris tenen la mateixa unitat organitzativa
    print(f"Unitat organitzativa extreta del CSV: {org_unit}")

    # Obtenir tots els usuaris de la unitat organitzativa especificada
    usuaris_org_unit = obtenir_usuaris_unitat(service, org_unit)

    # Llista d'emails del CSV
    emails_csv = df['Email Address'].tolist()

    # Recórrer els usuaris de la unitat organitzativa al servidor
    for usuari in usuaris_org_unit:
        email = usuari['primaryEmail']

        # Si l'usuari no està al CSV, preguntar si es vol moure
        if email not in emails_csv:
            print(f"L'usuari {email} no està al fitxer CSV.")
            resposta = input(f"Vols moure {email} a la unitat organitzativa {org_unit_altres}? (S/n): ").strip().lower()
            if resposta in ['s', '']:
                moure_usuari_a_una_altra_unitat(service, email, org_unit_altres)
            else:
                print(f"Usuari {email} no mogut.")

if __name__ == '__main__':
    # Utilitzar argparse per gestionar els paràmetres de la línia de comandes
    parser = argparse.ArgumentParser(description="Compara usuaris d'una unitat organitzativa amb un fitxer CSV i mou els que no hi són.")
    
    # Paràmetres opcionals amb format "--"
    parser.add_argument('--credentials-file', type=str, required=True, help='El fitxer de credencials JSON de la Service Account.')
    parser.add_argument('--admin-email', type=str, required=True, help='El correu electrònic de l\'administrador del domini.')
    parser.add_argument('--csv-file', type=str, required=True, help='El fitxer CSV amb els usuaris.')
    parser.add_argument('--org-unit-altres', type=str, required=True, help='La unitat organitzativa on es mouran els usuaris que no estan al CSV.')

    # Obtenir els arguments
    args = parser.parse_args()

    # Cridar la funció principal
    comparar_i_moure_usuaris(args.credentials_file, args.admin_email, args.csv_file, args.org_unit_altres)
