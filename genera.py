import os
import pandas as pd
import argparse
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

# Funció principal per llegir el CSV/Excel i generar el nou arxiu amb correus
def generar_csv_i_excel_amb_emails(input_file, password, org_unit_path, output_base, chars):
    # Llegir el fitxer (sigui CSV o Excel)
    df = llegir_fitxer(input_file)
    
    # Crear la carpeta logs si no existeix
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Crear el fitxer de log dins de la carpeta logs
    log_file = os.path.join('logs', datetime.now().strftime(f"%Y-%m-%d-%H-%M-%S-{output_base}.log"))

    with open(log_file, 'a') as log:
        log.write(f"Creació del fitxer {output_base}.csv i {output_base}.xlsx\n")
    
    # Crear noves columnes per a Email Address, Password i Org Unit Path
    df['Email Address'] = df['Llinatges i nom'].apply(lambda x: generar_email(x, chars))
    df['Password'] = password
    df['Org Unit Path'] = org_unit_path
    
    # Separar les columnes de "Llinatges i nom" en "First Name" i "Last Name"
    df_output = df['Llinatges i nom'].str.split(", ", expand=True)
    df['Last Name'] = df_output[0]
    df['First Name'] = df_output[1]

    # Seleccionar les columnes necessàries per a l'arxiu de sortida
    df_output = df[['First Name', 'Last Name', 'Email Address', 'Password', 'Org Unit Path']]

    # Generar els noms de fitxers per a CSV i Excel utilitzant el mateix nom base
    output_csv = f"{output_base}.csv"
    output_xls = f"{output_base}.xlsx"

    # Guardar el DataFrame resultant en un nou CSV
    df_output.to_csv(output_csv, index=False)
    print(f"Fitxer CSV guardat correctament com {output_csv}")

    # Guardar el DataFrame resultant en un nou Excel
    df_output.to_excel(output_xls, index=False, engine='openpyxl')
    print(f"Fitxer Excel guardat correctament com {output_xls}")

# Parser d'arguments per acceptar paràmetres des de la línia de comandes
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generar correus electrònics i arxius CSV/Excel.')
    parser.add_argument('password', type=str, help='El password per als comptes.')
    parser.add_argument('org_unit_path', type=str, help="El camí d'Org Unit Path.")
    parser.add_argument('input_file', type=str, help='El fitxer CSV o Excel d\'entrada.')
    parser.add_argument('--output', type=str, required=True, help='El nom base per als fitxers de sortida (sense extensió).')
    parser.add_argument('--chars', type=int, default=2, help='Nombre de caràcters a agafar del segon llinatge (per defecte: 2).')

    args = parser.parse_args()
    
    generar_csv_i_excel_amb_emails(args.input_file, args.password, args.org_unit_path, args.output, args.chars)
