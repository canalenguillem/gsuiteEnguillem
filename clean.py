import os
import shutil
from datetime import datetime

def clean_old_files(current_folder="."):
    # Definir la carpeta "tests"
    tests_folder = os.path.join(current_folder, "tests")

    # Crear la carpeta "tests" si no existeix
    if not os.path.exists(tests_folder):
        os.makedirs(tests_folder)

    # Llistar tots els fitxers de la carpeta actual
    all_files = os.listdir(current_folder)
    print(f"Tots els fitxers trobats: {all_files}")

    # Filtrar només els fitxers CSV i XLSX
    csv_files = [f for f in all_files if f.endswith('.csv')]
    xlsx_files = [f for f in all_files if f.endswith('.xlsx')]
    print(f"Fitxers CSV: {csv_files}")
    print(f"Fitxers XLSX: {xlsx_files}")

    # Funció per obtenir la data d'un fitxer segons el nom, gestionant "news" o "olds"
    def extract_timestamp(file_name):
        try:
            parts = file_name.split('_')[-1].replace('news-', '').replace('olds-', '').split('.')[0]
            return datetime.strptime(parts, "%Y-%m-%d-%H-%M")
        except Exception as e:
            print(f"Error al processar el timestamp del fitxer {file_name}: {e}")
            return None

    # Agrupar els fitxers per prefix, per exemple "CFGM_SMX_B"
    grouped_files = {}
    for file in csv_files + xlsx_files:
        group_name = "_".join(file.split('_')[:3])
        timestamp = extract_timestamp(file)
        if group_name and timestamp:
            if group_name not in grouped_files:
                grouped_files[group_name] = []
            grouped_files[group_name].append((file, timestamp))

    print(f"Fitxers agrupats: {grouped_files}")

    # Processar cada grup, quedant-se només amb els 2 fitxers més nous i movent la resta a la carpeta "tests"
    for group, files in grouped_files.items():
        # Ordenar els fitxers per data de més recent a més antic
        files.sort(key=lambda x: x[1], reverse=True)

        # Els 2 més nous es queden, la resta es mouen
        print(f"Processant grup {group}, fitxers: {files}")
        for file, _ in files[2:]:
            original_path = os.path.join(current_folder, file)
            destination_path = os.path.join(tests_folder, file)
            print(f"Movent {file} a {destination_path}")
            shutil.move(original_path, destination_path)

    print("Procés completat. Els fitxers antics han estat moguts a la carpeta 'tests'.")

if __name__ == "__main__":
    clean_old_files()
