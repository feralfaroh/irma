import csv
import json
import requests
from datetime import datetime
import sys
import snowflake.connector
from config import CONFIG

# Configuración de la API Ninox
ninox_url = CONFIG["ninox"]["url"]
ninox_headers = CONFIG["ninox"]["headers"]

# Lista de campos que deben ser numéricos (si es necesario convertirlos)
numeric_fields = [
    "DevolProvCto", "DevolProvUni", "DevolProvVta", "InvFinCto", "InvFinUni", "InvFinVta",
    "RebajaVta", "RecibosCto", "RecibosPzs", "RecibosVta", "VentaNetaaCosto",
    "VentaNetaenPesos", "VentaNetaenUnidades", "TransfEntCto", "TransfEntUni", "TransfEntVta",
    "TransfSalCto", "TransfSalUni", "TransfSalVta", "VentaNetaenPesosAnt", "VentaNetaenUnidadesAnt",
    "PVPCosto", "PVPVenta", "MargenObtenidoInv", "MargenObtenidoVenta", "dow", "DiferenciaMargen", "DifPesos"
]

def parse_numeric(value):
    """
    Convierte el valor de texto a número.
    Se eliminan separadores de miles, espacios y el signo de porcentaje.
    Si el valor está vacío se retorna None.
    """
    if value is None or value.strip() == "":
        return None
    value = value.replace(",", "").replace("%", "").strip()
    try:
        num = float(value)
        return int(num) if num.is_integer() else num
    except ValueError:
        return value

def formatear_fecha(fecha_str):
    """
    Convierte una cadena de fecha a formato ISO 8601 (YYYY-MM-DD).
    Se asume que en el CSV la fecha está en formato DD/MM/YYYY.
    """
    if not fecha_str or fecha_str.strip() == "":
        return None
    try:
        fecha = datetime.strptime(fecha_str.strip(), "%d/%m/%Y")
        return fecha.strftime("%Y-%m-%d")
    except ValueError:
        # Si falla la conversión, se retorna el valor original
        return fecha_str.strip()

def convertir_fila(row):
    """
    Convierte cada fila del CSV a un registro con la estructura que espera la API o la inserción en Snowflake:
    { "fields": { ... } }.
    Se convierte el campo "DiaFecha", los campos numéricos y se omiten aquellos con valor None.
    """
    nuevos_campos = {}
    for key, value in row.items():
        if key == "DiaFecha":
            nuevo_valor = formatear_fecha(value)
        elif key in numeric_fields:
            nuevo_valor = parse_numeric(value)
        else:
            nuevo_valor = value.strip() if value and value.strip() != "" else None
        
        if nuevo_valor is not None:
            nuevos_campos[key] = nuevo_valor

    return {"fields": nuevos_campos}

def leer_csv(ruta_archivo):
    """
    Lee el archivo CSV (con encoding 'latin1') y devuelve una lista de registros convertidos.
    Se asume que la primera columna es "DiaFecha".
    """
    registros = []
    with open(ruta_archivo, mode='r', encoding='latin1', newline='') as csvfile:
        lector = csv.DictReader(csvfile)
        for row in lector:
            registros.append(convertir_fila(row))
    return registros

def enviar_a_api(registros):
    """
    Envía los registros a la API de Ninox.
    La API espera un array de registros.
    Se imprime el código de estado y la respuesta en la terminal.
    """
    payload = json.dumps(registros, ensure_ascii=False)
    response = requests.post(ninox_url, headers=ninox_headers, data=payload)
    print("API Ninox -> Código de estado:", response.status_code)
    #print("API Ninox -> Respuesta:", response.text)
    if response.status_code in (200, 201):
        print("Datos importados exitosamente a Ninox.")
    else:
        print("Error al importar datos a Ninox.")

def insertar_en_snowflake(registros):
    """
    Inserta los registros en la tabla TESTING_2025 de Snowflake.
    Se arma una lista de tuplas con los valores en el orden definido por las columnas.
    Se usa executemany() para realizar la inserción en lote.
    """
    columnas = [
        "DiaFecha", "NP", "Sku", "Region", "Distrito", "NT", "Tienda", "Depto", "SubDepto", 
        "Clase", "SubClase", "Comprador", "Capa", "DiasdeInventario", "VentaNetaaCosto", 
        "VentaNetaenUnidades", "VentaNetaenPesos", "RecibosCto", "RecibosPzs", "RecibosVta", 
        "RebajaVta", "DevolProvCto", "DevolProvUni", "DevolProvVta", "InvFinUni", "InvFinCto", 
        "InvFinVta", "TransfEntCto", "TransfEntUni", "TransfEntVta", "TransfSalCto", 
        "TransfSalUni", "TransfSalVta", "VentaNetaenPesosAnt", "VentaNetaenUnidadesAnt", 
        "MargenObtenidoInv", "MargenObtenidoVenta", "PVPCosto", "PVPVenta", "DifPesos", 
        "DiferenciaMargen", "dow"
    ]
    
    insert_query = f"""
    INSERT INTO TESTING_2025 (
        {', '.join(columnas)}
    ) VALUES (
        {', '.join(['%s'] * len(columnas))}
    )
    """
    
    valores_a_insertar = []
    for registro in registros:
        campos = registro["fields"]
        fila = tuple(campos.get(col) for col in columnas)
        valores_a_insertar.append(fila)
    
    try:
        conn = snowflake.connector.connect(**CONFIG["snowflake"])
        cursor = conn.cursor()
        cursor.executemany(insert_query, valores_a_insertar)
        conn.commit()
        print("Datos insertados correctamente en Snowflake.")
    except snowflake.connector.errors.Error as e:
        print("Error al insertar en Snowflake:", e)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

def main():
    if len(sys.argv) > 1:
        ruta_csv = sys.argv[1]
    else:
        ruta_csv = r"descargas\e_06032025_508.csv"
    
    print("Verificando ruta CSV...")
    print("Ruta CSV:", ruta_csv)
    
    try:
        registros = leer_csv(ruta_csv)
    except Exception as e:
        print("Error leyendo el CSV:", e)
        return

    print("Enviando registros a Ninox...")
    enviar_a_api(registros)
    
    print("Insertando registros en Snowflake...")
    insertar_en_snowflake(registros)

if __name__ == "__main__":
    main()
