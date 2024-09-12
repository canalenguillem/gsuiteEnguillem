import os
import shutil

# Carpeta per moure els fitxers log
log_dir = 'logs'

# Crear la carpeta logs si no existeix
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Obtenir tots els fitxers al directori actual
fitxers = [f for f in os.listdir() if os.path.isfile(f)]

# Filtrar només els fitxers .log
fitxers_log = [f for f in fitxers if f.endswith('.log')]

# Moure els fitxers .log a la carpeta logs
for fitxer_log in fitxers_log:
    desti = os.path.join(log_dir, fitxer_log)
    shutil.move(fitxer_log, desti)
    print(f"Mogut {fitxer_log} a {log_dir}")

print("Procés completat. Els fitxers .log han estat moguts a la carpeta 'logs'.")
