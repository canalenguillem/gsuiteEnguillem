import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from textwrap import wrap

# Funció per separar el nom en llinatges i nom propi i limitar els llinatges a 12 caràcters
def formatejar_nom_com_llinatges_i_nom(first_name, last_name):
    # Tractar els llinatges (limitar-los a 12 caràcters) i el nom
    llinatges = last_name[:12]  # Agafem només els primers 12 caràcters dels llinatges
    nom = first_name
    return llinatges, nom

# Funció per generar les etiquetes en PDF
def generar_pdf_amb_etiquetes(csv_file, output_pdf):
    # Llegir el CSV
    df = pd.read_csv(csv_file)

    # Crear el PDF
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4

    # Definir el nombre de columnes i files
    columnes = 4  # Canviat a 4 columnes
    files = 6

    # Definir l'espai entre etiquetes i les mides
    ample_etiqueta = (width - 2 * 10 * mm) / columnes  # Deixar un marge de 10 mm a la dreta i esquerra
    alt_etiqueta = (height - 20 * mm) / files  # Aumentar marge inferior i superior a 20 mm

    marge = 10 * mm  # Aumentar el marge superior a 10 mm per evitar retalls

    # Definir la font i el tamany de lletra
    font_size = 8  # Reduir el tamany de la lletra
    c.setFont("Helvetica", font_size)  # Utilitzar la font sans-serif Helvetica

    # Posició inicial (dalt a l'esquerra)
    x_inicial = marge
    y_inicial = height - marge

    # Iterar per cada usuari
    for index, row in df.iterrows():
        # Calcula la posició de la fila i la columna dins la pàgina
        columna_actual = index % columnes
        fila_actual = (index // columnes) % files

        # Calcula la posició en el PDF
        x = x_inicial + columna_actual * ample_etiqueta
        y = y_inicial - (fila_actual + 1) * alt_etiqueta

        # Formatejar nom i llinatges
        llinatges, nom = formatejar_nom_com_llinatges_i_nom(row['First Name'], row['Last Name'])

        # Obtener la password, si no existe, usa '*****'
        password = row.get('Password', '*****')

        # Definir text de l'etiqueta amb llinatges a dalt i nom a baix
        text = f"Llinatges: {llinatges}\nNom: {nom}\nEmail: {row['Email Address']}\nPassword: {password}"

        # Utilitzar el text object per a millorar el format
        text_obj = c.beginText(x + 5 * mm, y + alt_etiqueta - 10 * mm)
        text_obj.textLines(text)  # Afegeix línies de text amb salts de línia automàtics

        # Dibuixar el text al PDF
        c.drawText(text_obj)

        # Dibuixar un rectangle al voltant de cada etiqueta per fer fàcil el retall
        c.setStrokeColor("black")
        c.rect(x, y, ample_etiqueta, alt_etiqueta, stroke=1, fill=0)

        # Si hem omplert una pàgina, passa a la següent
        if (index + 1) % (columnes * files) == 0:
            c.showPage()  # Nova pàgina
            c.setFont("Helvetica", font_size)  # Restaurar la font per a la següent pàgina

    # Tancar el PDF
    c.save()
    print(f"PDF amb etiquetes generat correctament com {output_pdf}")

if __name__ == '__main__':
    import argparse

    # Utilitzar argparse per gestionar els paràmetres de la línia de comandes
    parser = argparse.ArgumentParser(description='Generar etiquetes en PDF a partir d\'un CSV.')
    parser.add_argument('--csv-file', type=str, required=True, help='El fitxer CSV amb els usuaris.')
    parser.add_argument('--output-pdf', type=str, default='etiquetes.pdf', help='El nom del fitxer PDF de sortida.')

    # Obtenir els arguments
    args = parser.parse_args()

    # Generar el PDF amb les etiquetes
    generar_pdf_amb_etiquetes(args.csv_file, args.output_pdf)
