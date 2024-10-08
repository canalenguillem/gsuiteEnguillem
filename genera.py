import pandas as pd
import argparse
import unidecode
import os

# Funció per generar l'adreça de correu electrònic correctament
def generar_email(nom_complet, chars_llinatges, chars_nom):
    nom_complet = nom_complet.split(", ")
    llinatges = nom_complet[0].split()  # Separar els llinatges
    noms = nom_complet[1].split()       # Separar els noms (pot ser compost)

    # Agafar els primers chars_nom caràcters del primer nom (pot ser compost)
    inicials_nom = ''
    for nom in noms[:2]:
        if nom.startswith("LL"):
            inicials_nom += 'll'
        else:
            inicials_nom += nom[:chars_nom].lower()

    # Agafar el primer llinatge complet i el nombre de caràcters especificats del segon llinatge (si n'hi ha)
    primer_llinatge = llinatges[0].lower()  # Primer llinatge complet
    segon_llinatge = llinatges[1][:chars_llinatges].lower() if len(llinatges) > 1 else ''  # Caràcters del segon llinatge segons el valor de `chars_llinatges`

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
def generar_csv_i_excel_amb_emails(input_file, password, org_unit_path, output_base, chars_llinatges, chars_nom):
    # Crear la carpeta "data" si no existeix
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Llegir el fitxer (sigui CSV o Excel)
    df = llegir_fitxer(input_file)
    print(f"chars_llinatges = {chars_llinatges}, chars_nom = {chars_nom}")

    # Crear noves columnes per a Email Address, Password i Org Unit Path
    df['Email Address'] = df['Llinatges i nom'].apply(lambda x: generar_email(x, chars_llinatges, chars_nom))
    df['Password'] = password
    df['Org Unit Path'] = org_unit_path
    
    # Seleccionar les columnes necessàries per a l'arxiu de sortida
    df_output = df[['Llinatges i nom', 'Llinatges i nom', 'Email Address', 'Password', 'Org Unit Path']]
    
    # Separar les columnes de "Llinatges i nom" en "First Name" i "Last Name"
    df_output[['First Name', 'Last Name']] = df['Llinatges i nom'].str.split(", ", expand=True)

    # Reordenar les columnes
    df_output = df_output[['First Name', 'Last Name', 'Email Address', 'Password', 'Org Unit Path']]

    # Generar els noms de fitxers per a CSV i Excel utilitzant el mateix nom base dins de la carpeta "data"
    output_csv = os.path.join("data", f"{output_base}.csv")
    output_xls = os.path.join("data", f"{output_base}.xlsx")

    # Guardar el DataFrame resultant en un nou CSV
    df_output.to_csv(output_csv, index=False)
    print(f"Fitxer CSV guardat correctament a {output_csv}")

    # Guardar el DataFrame resultant en un nou Excel
    df_output.to_excel(output_xls, index=False, engine='openpyxl')
    print(f"Fitxer Excel guardat correctament a {output_xls}")

# Parser d'arguments per acceptar paràmetres des de la línia de comandes
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generar correus electrònics i arxius CSV/Excel.')
    parser.add_argument('password', type=str, help='El password per als comptes.')
    parser.add_argument('org_unit_path', type=str, help="El camí d'Org Unit Path.")
    parser.add_argument('input_file', type=str, help='El fitxer CSV o Excel d\'entrada.')
    parser.add_argument('--output', type=str, required=True, help='El nom base per als fitxers de sortida (sense extensió).')
    parser.add_argument('--chars', type=int, default=1, help='Nombre de caràcters a agafar del segon llinatge (per defecte: 2).')
    parser.add_argument('--chars-nom', type=int, default=1, help='Nombre de caràcters a agafar del nom (per defecte: 1).')

    args = parser.parse_args()
    
    generar_csv_i_excel_amb_emails(args.input_file, args.password, args.org_unit_path, args.output, args.chars, args.chars_nom)
