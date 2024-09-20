import pandas as pd
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
import unidecode
from datetime import datetime


# Funció per generar l'adreça de correu electrònic correctament
def generar_email(nom_complet, chars):
    nom_complet = nom_complet.split(", ")
    llinatges = nom_complet[0].split()  # Separar els llinatges
    noms = nom_complet[1].split()       # Separar els noms (pot ser compost)

    # Tractar el cas especial on el nom comença amb "LL"
    inicials_nom = ''
    for nom in noms[:2]:
        if nom.startswith("LL"):
            inicials_nom += 'll'
        else:
            inicials_nom += nom[0].lower()

    # Agafar el primer llinatge complet i el nombre de caràcters especificats del segon llinatge (si n'hi ha)
    primer_llinatge = llinatges[0].lower()  # Primer llinatge complet
    segon_llinatge = llinatges[1][:chars].lower() if len(llinatges) > 1 else ''  # Caràcters del segon llinatge segons el valor de `chars`

    # Netejar caràcters especials com accents, ñ, ç
    inicials_nom = unidecode.unidecode(inicials_nom)
    primer_llinatge = unidecode.unidecode(primer_llinatge)
    segon_llinatge = unidecode.unidecode(segon_llinatge)

    # Generar el correu electrònic
    email = f"{inicials_nom}{primer_llinatge}{segon_llinatge}@esliceu.net"
    return email

# Funció per llegir un fitxer (CSV o Excel)
def llegir_fitxer(input_file):
    # Comprovar si és CSV o Excel
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    elif input_file.endswith('.xls') or input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file, skiprows=4)  # Saltar les primeres 4 files
    else:
        raise ValueError("El fitxer ha de ser .csv, .xls o .xlsx")
    
    return df

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

# Funció per comprovar si un usuari existeix i obtenir la seva informació
def usuari_existeix(service, email):
    try:
        # Fer una petició per obtenir informació sobre l'usuari
        usuari = service.users().get(userKey=email).execute()
        org_unit_path = usuari.get('orgUnitPath', 'Sense assignar')  # Obtenir l'orgUnitPath de l'usuari
        nom = usuari['name']['givenName']  # Obtenir el nom
        cognoms = usuari['name']['familyName']  # Obtenir els cognoms
        creation_time = usuari.get('creationTime', None)  # Data de creació del compte
        last_login_time = usuari.get('lastLoginTime', 'Mai')  # Darrera connexió

        # Comprovar si la darrera connexió és 1970, és a dir, que mai no s'ha connectat
        if last_login_time == '1970-01-01T00:00:00.000Z':
            last_login_time = 'Mai'

        return True, org_unit_path, nom, cognoms, creation_time, last_login_time
    except Exception as e:
        print(f"L'usuari {email} no existeix o no es pot recuperar la informació")
        return False, None, None, None, None, None

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

# Funció per registrar els canvis en un fitxer .log
def registrar_canvi(log_file, missatge):
    with open(log_file, 'a') as log:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.write(f"{timestamp} - {missatge}\n")

# Funció per obtenir tots els usuaris d'una unitat organitzativa
def obtenir_usuaris_unitat(service, org_unit_path):
    try:
        results = service.users().list(customer='my_customer', query=f'orgUnitPath={org_unit_path}', maxResults=500).execute()
        usuaris = results.get('users', [])
        return usuaris
    except Exception as e:
        print(f"No s'han pogut obtenir els usuaris de la unitat organitzativa {org_unit_path}: {e}")
        return []


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
    

def moure_usuari_a_una_altra_unitat(service, email, nova_unitat):
    try:
        service.users().update(userKey=email, body={'orgUnitPath': nova_unitat}).execute()
        print(f"Usuari {email} mogut correctament a {nova_unitat}.")
        return True
    except Exception as e:
        print(f"No s'ha pogut moure l'usuari {email} a {nova_unitat}: {e}")
        return False

