import pandas as pd
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import argparse
import os
from datetime import datetime, timedelta
from functions import connectar_amb_google, usuari_existeix, actualitzar_unitat_organitzativa, actualitzar_nom_i_cognoms, registrar_canvi, crear_usuari

quants = 0
canviar = 0

# Funció per actualitzar el password i forçar canvi de contrasenya en proper login
def actualitzar_password(service, email, new_password, force_password_change, log_file):
    try:
        body = {
            'password': new_password,
            'changePasswordAtNextLogin': force_password_change
        }
        service.users().update(userKey=email, body=body).execute()
        if force_password_change:
            print(f"L'usuari {email} haurà de canviar la contrasenya en el proper inici de sessió.")
        else:
            global canviar
            canviar += 1
            print(f"L'usuari {email} és candidat a un canvi de contrasenya.")
        registrar_canvi(log_file, f"Contrasenya actualitzada per a {email}. Canvi de contrasenya: {'Obligatori' if force_password_change else 'No obligatori'}.")
        return True
    except Exception as e:
        print(f"No s'ha pogut actualitzar la contrasenya per a {email}: {e}")
        registrar_canvi(log_file, f"Error en actualitzar la contrasenya per a {email}: {e}")
        return False

# Funció principal per llegir el CSV, comprovar si els correus existeixen, gestionar la unitat organitzativa, crear usuaris i generar els CSV amb els usuaris nous i els existents
def comprovar_usuaris_csv(credentials_file, admin_email, csv_file, create_users='N', change_password='N'):
    # Connectar-se amb l'API de Google
    service = connectar_amb_google(credentials_file, admin_email)

    # Llegir el CSV
    df = pd.read_csv(csv_file)

    # Crear la carpeta "data" si no existeix
    if not os.path.exists("data"):
        os.makedirs("data")

    # Generar el nom base del fitxer CSV per usar-lo més tard en crear els fitxers news i olds
    base_name = os.path.splitext(os.path.basename(csv_file))[0]  # Nom base sense extensió

    # Generar el nom del fitxer log basat en la data i hora actuals
    log_file = datetime.now().strftime(f"logs/%Y-%m-%d-%H-%M-%S-{base_name}.log")

    # Llistes per guardar els usuaris que no existeixen i els que ja existien
    usuaris_no_existents = []
    usuaris_existents = []

    # Data actual per comparar l'última connexió
    avui = datetime.now()

    # Recórrer cada fila del CSV i comprovar si l'usuari existeix
    for index, row in df.iterrows():
        global quants
        quants += 1
        email = row['Email Address']
        first_name = row['First Name']
        last_name = row['Last Name']
        password = row['Password']
        org_unit_path = row['Org Unit Path']

        existeix, org_unit_actual, nom_servidor, cognoms_servidor, creation_time, last_login_time = usuari_existeix(service, email)

        if existeix:
            # Comparar noms i cognoms amb el que hi ha al servidor
            if first_name.lower() == nom_servidor.lower() and last_name.lower() == cognoms_servidor.lower():
                print(f"L'usuari {email} ja existeix i els noms coincideixen.")
                
                # Condicions per canvi de contrasenya:
                # 1. Mai no s'ha connectat (lastLoginTime == 'Mai')
                # 2. Fa més de 12 mesos que no es connecta
                if last_login_time == 'Mai' or (avui - datetime.strptime(last_login_time, "%Y-%m-%dT%H:%M:%S.%fZ") > timedelta(days=365)):
                    global canviar
                    canviar += 1
                    if change_password.upper() == 'S':
                        actualitzar_password(service, email, password, True, log_file)
                    else:
                        print(f"L'usuari {email} és candidat a canvi de contrasenya (darrera connexió: {last_login_time}).")
                        registrar_canvi(log_file, f"Usuari {email} candidat a canvi de contrasenya (darrera connexió: {last_login_time}).")
                else:
                    # Si no es canvia la contrasenya, posem "*****"
                    row['Password'] = "*****"

                # Comprovar si s'ha de canviar la unitat organitzativa
                if org_unit_actual != org_unit_path:
                    resposta = input(f"L'usuari {email} està a {org_unit_actual}. Vols actualitzar-lo a {org_unit_path}? (S/n): ").strip().lower()
                    if resposta in ['s', '']:
                        if actualitzar_unitat_organitzativa(service, email, org_unit_path):
                            registrar_canvi(log_file, f"Actualitzada la unitat organitzativa de {email} a {org_unit_path}")
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
            usuaris_existents.append(row)
        else:
            # Si l'opció --create-users és S, crear l'usuari
            if create_users.upper() == 'S':
                crear_usuari(service, first_name, last_name, email, password, org_unit_path, log_file)
            else:
                print(f"Usuari {email} no creat perquè l'opció --create-users no està activada.")
                registrar_canvi(log_file, f"Usuari no creat: {email}")
            
            # Afegeix l'usuari a la llista d'usuaris no existents
            usuaris_no_existents.append(row)

    # Guarda els fitxers news i olds a la carpeta "data"
    # Si hi ha usuaris que no existeixen, generar un nou CSV i un fitxer Excel
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    if usuaris_no_existents:
        df_no_existents = pd.DataFrame(usuaris_no_existents)
        new_csv_file = os.path.join("data", f"{base_name}_news-{timestamp}.csv")
        new_xls_file = os.path.join("data", f"{base_name}_news-{timestamp}.xlsx")
        df_no_existents.to_csv(new_csv_file, index=False)
        print(f"S'ha creat el fitxer {new_csv_file} amb els usuaris que no existeixen.")
        registrar_canvi(log_file, f"Creat el fitxer {new_csv_file} amb els usuaris que no existeixen")
        df_no_existents.to_excel(new_xls_file, index=False, engine='openpyxl')
        print(f"S'ha creat el fitxer {new_xls_file} amb els usuaris que no existeixen.")
        registrar_canvi(log_file, f"Creat el fitxer {new_xls_file} amb els usuaris que no existeixen")

    # Si hi ha usuaris existents, generar un fitxer CSV i Excel amb aquests usuaris
    if usuaris_existents:
        df_existents = pd.DataFrame(usuaris_existents)
        old_csv_file = os.path.join("data", f"{base_name}_olds-{timestamp}.csv")
        old_xls_file = os.path.join("data", f"{base_name}_olds-{timestamp}.xlsx")
        df_existents.to_csv(old_csv_file, index=False)
        print(f"S'ha creat el fitxer {old_csv_file} amb els usuaris que ja existien.")
        registrar_canvi(log_file, f"Creat el fitxer {old_csv_file} amb els usuaris que ja existien")
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
    parser.add_argument('--create-users', type=str, default='N', help='(Opcional) Si s\'han de crear els usuaris que no existeixen (S per crear-los, N per defecte).')
    parser.add_argument('--change-password', type=str, default='N', help='(Opcional) Si s\'han d\'actualitzar les contrasenyes dels usuaris que no s\'han connectat en 12 mesos o més (S per actualitzar-les, N per defecte).')

    # Obtenir els arguments
    args = parser.parse_args()

    # Cridar la funció per comprovar els usuaris i crear-los si no existeixen i si --create-users és S
    comprovar_usuaris_csv(args.credentials_file, args.admin_email, args.csv_file, args.create_users, args.change_password)
    print(f"quants {quants} canvis pass {canviar}")
