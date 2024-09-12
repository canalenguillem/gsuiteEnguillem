import pandas as pd
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import argparse
import os
from datetime import datetime
from functions import connectar_amb_google, usuari_existeix, actualitzar_unitat_organitzativa, actualitzar_nom_i_cognoms, registrar_canvi, crear_usuari

# Funció principal per llegir el CSV, comprovar si els correus existeixen, gestionar la unitat organitzativa, crear usuaris i generar els CSV amb els usuaris nous i els existents
def comprovar_usuaris_csv(credentials_file, admin_email, csv_file, create_users='N'):
    # Connectar-se amb l'API de Google
    service = connectar_amb_google(credentials_file, admin_email)

    # Llegir el CSV
    df = pd.read_csv(csv_file)

    # Generar el nom base del fitxer CSV per usar-lo més tard en crear els fitxers news i olds
    base_name = os.path.splitext(csv_file)[0]  # Afegeix aquesta línia

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

    # Guarda els fitxers news i olds segons les funcions ja definides

    # Si hi ha usuaris que no existeixen, generar un nou CSV i un fitxer Excel
    # Generar el timestamp per al nom del fitxer news
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    if usuaris_no_existents:
        # Crear un nou DataFrame amb els usuaris que no existeixen
        df_no_existents = pd.DataFrame(usuaris_no_existents)


        # Generar el nom dels fitxers amb el sufix news-any-mes-dia-hora
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
    parser.add_argument('--create-users', type=str, default='N', help='(Opcional) Si s\'han de crear els usuaris que no existeixen (S per crear-los, N per defecte).')

    # Obtenir els arguments
    args = parser.parse_args()

    # Cridar la funció per comprovar els usuaris i crear-los si no existeixen i si --create-users és S
    comprovar_usuaris_csv(args.credentials_file, args.admin_email, args.csv_file, args.create_users)
