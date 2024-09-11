import pandas as pd
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import argparse
import os
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

# Funció per comprovar si un usuari existeix i obtenir la seva unitat organitzativa i nom complet
def usuari_existeix(service, email):
    try:
        # Fer una petició per obtenir informació sobre l'usuari
        usuari = service.users().get(userKey=email).execute()
        org_unit_path = usuari.get('orgUnitPath', 'Sense assignar')  # Obtenir l'orgUnitPath de l'usuari
        nom = usuari['name']['givenName']
        cognoms = usuari['name']['familyName']
        return True, org_unit_path, nom, cognoms
    except Exception as e:
        print(f"L'usuari {email} no existeix.")
        return False, None, None, None

# Funció per actualitzar la unitat organitzativa d'un usuari
def actualitzar_unitat_organitzativa(service, email, nova_unitat):
    try:
        # Actualitzar la unitat organitzativa
        service.users().update(userKey=email, body={'orgUnitPath': nova_unitat}).execute()
        print(f"Unitat organitzativa actualitzada per a {email}. Nova unitat: {nova_unitat}")
        return True
    except Exception as e:
        print(f"No s'ha pogut actualitzar la unitat organitzativa per a {email}: {e}")
        return False

# Funció per actualitzar el nom i cognoms d'un usuari
def actualitzar_nom_i_cognoms(service, email, first_name, last_name):
    try:
        # Actualitzar nom i cognoms
        body = {
            'name': {
                'givenName': first_name,
                'familyName': last_name
            }
        }
        service.users().update(userKey=email, body=body).execute()
        print(f"Nom i cognoms actualitzats per a {email}: {first_name} {last_name}")
        return True
    except Exception as e:
        print(f"No s'ha pogut actualitzar el nom i cognoms per a {email}: {e}")
        return False

# Funció per crear un nou usuari a Google Workspace
def crear_usuari(service, first_name, last_name, email, password, org_unit_path, log_file):
    try:
        body = {
            'name': {
                'givenName': first_name,
                'familyName': last_name,
            },
            'password': password,
            'primaryEmail': email,
            'orgUnitPath': org_unit_path
        }
        service.users().insert(body=body).execute()
        print(f"Usuari {email} creat correctament.")
        registrar_canvi(log_file, f"Usuari creat: {email}")
        return True
    except Exception as e:
        print(f"No s'ha pogut crear l'usuari {email}: {e}")
        registrar_canvi(log_file, f"Error en crear l'usuari: {email}. Error: {e}")
        return False

# Funció per registrar els canvis en un fitxer .log
def registrar_canvi(log_file, missatge):
    with open(log_file, 'a') as log:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.write(f"{timestamp} - {missatge}\n")

# Funció principal per llegir el CSV, comprovar si els correus existeixen, gestionar la unitat organitzativa, crear usuaris i generar els CSV amb els usuaris nous i els existents
def comprovar_usuaris_csv(credentials_file, admin_email, csv_file, org_unit_expected=None, create_users='N'):
    # Connectar-se amb l'API de Google
    service = connectar_amb_google(credentials_file, admin_email)

    # Llegir el CSV
    df = pd.read_csv(csv_file)

    # Generar el nom del fitxer log basat en la data i hora actuals
    log_file = datetime.now().strftime(f"%Y-%m-%d-%H-%M-%S-{os.path.basename(csv_file)}.log")

    # Llistes per guardar els usuaris que no existeixen i els que ja existien
    usuaris_no_existents = []
    usuaris_existents = []

    # Recórrer cada fila del CSV i comprovar si l'usuari existeix
    for index, row in df.iterrows():
        email = row['Email Address']
        first_name = row['First Name']
        last_name = row['Last Name']
        password = row['Password']
        org_unit_path = row['Org Unit Path']

        existeix, org_unit_actual, nom_servidor, cognoms_servidor = usuari_existeix(service, email)
        if existeix:
            # Comparar noms i cognoms amb el que hi ha al servidor
            if first_name.lower() == nom_servidor.lower() and last_name.lower() == cognoms_servidor.lower():
                print(f"L'usuari {email} ja existeix i els noms coincideixen.")
                # Comprovar si s'ha de canviar la unitat organitzativa
                if org_unit_expected and org_unit_actual != org_unit_expected:
                    resposta = input(f"L'usuari {email} està a {org_unit_actual}. Vols actualitzar-lo a {org_unit_expected}? (S/n): ").strip().lower()
                    if resposta in ['s', '']:
                        if actualitzar_unitat_organitzativa(service, email, org_unit_expected):
                            registrar_canvi(log_file, f"Actualitzada la unitat organitzativa de {email} a {org_unit_expected}")
            else:
                # Informar que els noms no coincideixen i mostrar els noms del servidor i del fitxer CSV
                print(f"L'usuari {email} ja existeix però els noms no coincideixen.")
                print(f"Nom al servidor: {nom_servidor} {cognoms_servidor}. Nom al fitxer CSV: {first_name} {last_name}.")
                confirmar = input("Confirmar que és la mateixa persona i actualitzar el nom al servidor amb el del CSV? (S/n/p): ").strip().lower()
                if confirmar == 's':
                    if actualitzar_nom_i_cognoms(service, email, first_name, last_name):
                        registrar_canvi(log_file, f"Actualitzat el nom de {email} amb el nom del CSV: {first_name} {last_name}")
                elif confirmar == 'n':
                    registrar_canvi(log_file, f"Nom no actualitzat per a {email}. Servidor: {nom_servidor} {cognoms_servidor}, CSV: {first_name} {last_name}")
                elif confirmar == 'p':
                    print(f"Saltant {email}.")
                    continue  # No fem res i passem a la següent fila
            
            # Afegeix l'usuari existent a la llista d'usuaris existents
            usuaris_existents.append(row.drop(labels=['Password']))
        else:
            # Si l'opció --create-users és S, crear l'usuari
            if create_users.upper() == 'S':
                crear_usuari(service, first_name, last_name, email, password, org_unit_path, log_file)
            else:
                print(f"Usuari {email} no creat perquè l'opció --create-users no està activada.")
                registrar_canvi(log_file, f"Usuari no creat: {email}")
            
            # Afegeix l'usuari a la llista d'usuaris no existents
            usuaris_no_existents.append(row)

    # Si hi ha usuaris que no existeixen, generar un nou CSV i un fitxer Excel
    if usuaris_no_existents:
        # Crear un nou DataFrame amb els usuaris que no existeixen
        df_no_existents = pd.DataFrame(usuaris_no_existents)

        # Generar el timestamp per al nom del fitxer news
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")

        # Generar el nom dels fitxers amb el sufix news-any-mes-dia-hora
        base_name = os.path.splitext(csv_file)[0]
        new_csv_file = f"{base_name}_news-{timestamp}.csv"
        new_xls_file = f"{base_name}_news-{timestamp}.xlsx"

        # Guardar el nou CSV amb els usuaris que no existeixen
        df_no_existents.to_csv(new_csv_file, index=False)
        print(f"S'ha creat el fitxer {new_csv_file} amb els usuaris que no existeixen.")
        registrar_canvi(log_file, f"Creat el fitxer {new_csv_file} amb els usuaris que no existeixen")

        # Guardar el nou Excel amb els usuaris que no existeixen
        df_no_existents.to_excel(new_xls_file, index=False, engine='openpyxl')
        print(f"S'ha creat el fitxer {new_xls_file} amb els usuaris que no existeixen.")
        registrar_canvi(log_file, f"Creat el fitxer {new_xls_file} amb els usuaris que no existeixen")

    # Si hi ha usuaris existents, generar un fitxer CSV i Excel amb aquests usuaris
    if usuaris_existents:
        # Crear un DataFrame amb els usuaris que ja existien, sense la columna Password
        df_existents = pd.DataFrame(usuaris_existents)

        # Generar el nom dels fitxers amb el sufix olds-any-mes-dia-hora
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        old_csv_file = f"{base_name}_olds-{timestamp}.csv"
        old_xls_file = f"{base_name}_olds-{timestamp}.xlsx"

        # Guardar el fitxer CSV amb els usuaris existents
        df_existents.to_csv(old_csv_file, index=False)
        print(f"S'ha creat el fitxer {old_csv_file} amb els usuaris que ja existien.")
        registrar_canvi(log_file, f"Creat el fitxer {old_csv_file} amb els usuaris que ja existien")

        # Guardar el fitxer Excel amb els usuaris existents
        df_existents.to_excel(old_xls_file, index=False, engine='openpyxl')
        print(f"S'ha creat el fitxer {old_xls_file} amb els usuaris que ja existien.")
        registrar_canvi(log_file, f"Creat el fitxer {old_xls_file} amb els usuaris que ja existien")
    else:
        print("No hi ha usuaris existents per a generar un fitxer.")
        registrar_canvi(log_file, "No hi ha usuaris existents per a generar un fitxer.")

if __name__ == '__main__':
    # Utilitzar argparse per gestionar els paràmetres de la línia de comandes
    parser = argparse.ArgumentParser(description='Comprova si els usuaris del CSV existeixen a Google Workspace i crea els que falten.')
    
    # Paràmetres opcionals amb format "--"
    parser.add_argument('--credentials-file', type=str, required=True, help='El fitxer de credencials JSON de la Service Account.')
    parser.add_argument('--admin-email', type=str, required=True, help='El correu electrònic de l\'administrador del domini.')
    parser.add_argument('--csv-file', type=str, required=True, help='El fitxer CSV amb els usuaris a comprovar.')
    parser.add_argument('--org-unit-expected', type=str, default=None, help='(Opcional) La unitat organitzativa esperada per als usuaris existents.')
    parser.add_argument('--create-users', type=str, default='N', help='(Opcional) Si s\'han de crear els usuaris que no existeixen (S per crear-los, N per defecte).')

    # Obtenir els arguments
    args = parser.parse_args()

    # Cridar la funció per comprovar els usuaris i crear-los si no existeixen i si --create-users és S
    comprovar_usuaris_csv(args.credentials_file, args.admin_email, args.csv_file, args.org_unit_expected, args.create_users)
