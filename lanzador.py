# lanzador.py

import subprocess
import sys
import re

def main():
    # 1. Ejecutar script1.py y capturar su salida
    print("=== Ejecutando script1.py ===")
    proceso1 = subprocess.run(
        [sys.executable, "script1.py"],  # También podrías usar ["python", "script1.py"]
        capture_output=True,
        text=True
    )
    
    # Verifica si script1.py se ejecutó correctamente
    if proceso1.returncode != 0:
        print("Hubo un error al ejecutar script1.py.")
        print("STDERR:", proceso1.stderr)
        return
    
    # 2. Analizar la salida de script1.py para extraer la ruta del CSV
    salida_script1 = proceso1.stdout
    print("Salida de script1:\n", salida_script1)
    
    # Usamos una expresión regular para buscar la línea con "Archivo procesado guardado como: <ruta>"
    patron = r"Archivo procesado guardado como:\s*(.+)"
    match = re.search(patron, salida_script1)
    if not match:
        print("No se encontró la línea con la ruta de CSV en la salida de script1.py.")
        return
    
    csv_path = match.group(1).strip()
    print(f"Ruta extraída del CSV: {csv_path}")

    # 3. Ejecutar script2.py, pasándole la ruta CSV como argumento
    print("=== Ejecutando script2.py ===")
    proceso2 = subprocess.run(
        [sys.executable, "script2.py", csv_path],
        capture_output=True,
        text=True
    )
    
    # Verifica si script2.py se ejecutó correctamente
    if proceso2.returncode != 0:
        print("Hubo un error al ejecutar script2.py.")
        print("STDERR:", proceso2.stderr)
    else:
        print("Script2 finalizó sin errores.")
        print("Salida de script2:\n", proceso2.stdout)

if __name__ == "__main__":
    main()
