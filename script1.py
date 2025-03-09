import time
import os
import csv
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sk import CONFIG

def wait_for_window(driver, old_handles, timeout=2):
    """
    Espera 'timeout' segundos y verifica si se abrió una nueva ventana
    comparando con old_handles. Devuelve el handle de la nueva ventana o None.
    """
    time.sleep(timeout)
    new_handles = driver.window_handles
    if len(new_handles) > len(old_handles):
        return list(set(new_handles) - set(old_handles))[0]
    return None

def wait_for_csv_file(download_dir, timeout=60):
    """
    Espera hasta que se encuentre un archivo CSV en el directorio de descargas,
    ignorando archivos incompletos (por ejemplo, con extensión .crdownload).
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        files = [f for f in os.listdir(download_dir)
                 if f.lower().endswith(".csv") and not f.lower().endswith(".crdownload")]
        if files:
            return os.path.join(download_dir, files[0])
        time.sleep(1)
    return None

def importar_csv_excel(archivo_entrada):
    """
    Importa el archivo CSV (todo su contenido) usando el módulo csv con el dialecto 'excel'.
    Se usa la codificación 'latin1' para manejar correctamente caracteres especiales.
    """
    with open(archivo_entrada, 'r', encoding='latin1') as f:
        reader = csv.reader(f, dialect='excel')
        data = list(reader)
    return data

def obtener_header_csv(archivo_entrada, encoding='latin1'):
    """
    Abre el archivo CSV y retorna la primera línea (cabecera) utilizando el dialecto 'excel'.
    """
    with open(archivo_entrada, 'r', encoding=encoding) as f:
        reader = csv.reader(f, dialect='excel')
        header = next(reader)
    return header

def modificar_header(header):
    """
    Reemplaza los nombres de las columnas en los índices específicos (0, 1 y 5)
    sin alterar el resto.
    """
    if len(header) > 5:
        header[0] = "DiaFecha"
        header[1] = "NP"
        header[5] = "NT"
    return header

def limpiar_valores_dataframe(df):
    """
    Elimina el signo '=' y las comillas al inicio y final de cada valor string.
    """
    return df.applymap(lambda x: x.strip('"').lstrip('="') if isinstance(x, str) else x)

def limpiar_nombres_columnas(columnas):
    """
    Convierte cada nombre de columna a cadena y elimina el signo '=' y las comillas
    al inicio y final.
    """
    return [str(col).strip('"').lstrip('="') for col in columnas]

def procesar_csv(archivo_entrada):
    try:
        # Obtener la cabecera del archivo considerando la codificación Latin1
        header = obtener_header_csv(archivo_entrada, encoding='latin1')
        # Modificar nombres de columnas (índices 0, 1 y 5)
        header = modificar_header(header)
        
        # Importar todos los datos y descartar la cabecera original
        data = importar_csv_excel(archivo_entrada)
        data = data[1:]
        
        # Definir nombres de columnas para el DataFrame
        new_names_col = [
            "DiaFecha", "NP", "Sku", "Region", "Distrito", "NT", "Tienda",
            "SubDepto", "Depto", "Clase", "SubClase", "Capa", "Comprador",
            "DevolProvCto", "DevolProvUni", "DevolProvVta", "InvFinCto",
            "InvFinUni", "InvFinVta", "RebajaVta", "RecibosCto", "RecibosPzs",
            "RecibosVta", "VentaNetaaCosto", "VentaNetaenPesos", "VentaNetaenUnidades",
            "TransfEntCto", "TransfEntUni", "TransfEntVta", "TransfSalCto",
            "TransfSalUni", "TransfSalVta", "DiasdeInventario",
            "VentaNetaenPesosAnt", "VentaNetaenUnidadesAnt", "PVPCosto", "PVPVenta",
            "MargenObtenidoInv", "MargenObtenidoVenta"
        ]
        df = pd.DataFrame(data, columns=new_names_col)
        
        # Limpiar los valores del DataFrame (quitar '=' y comillas)
        df = limpiar_valores_dataframe(df)
        
        # Eliminar filas en las que NP sea igual a 3285317
        df = df[df['NP'].astype(str) != "3285317"]
        
        # Ejemplo: procesar valor en la segunda fila, primera columna
        if not df.empty:
            valor_segunda_fila = df.iloc[1, 0].strip('"').lstrip('="').replace('/','')
            print("Valor segunda fila:", valor_segunda_fila)
        else:
            print("DataFrame vacío después del filtrado.")
        
        # --- Inicio de la integración de las nuevas columnas ---
        
        # Convertir columnas que se usarán en cálculos a numérico
        df['VentaNetaenUnidades'] = pd.to_numeric(df['VentaNetaenUnidades'], errors='coerce')
        df['VentaNetaenPesos'] = pd.to_numeric(df['VentaNetaenPesos'], errors='coerce')
        
        # Limpiar y convertir MargenObtenidoVenta: quitar '%' y asignar 0 si hay NaN
        df['MargenObtenidoVenta'] = df['MargenObtenidoVenta'].str.replace('%', '', regex=False)
        df['MargenObtenidoVenta'] = pd.to_numeric(df['MargenObtenidoVenta'], errors='coerce').fillna(0)
        
        # Limpiar y convertir MargenObtenidoInv: quitar '%' y asignar 0 si hay NaN
        df['MargenObtenidoInv'] = df['MargenObtenidoInv'].str.replace('%', '', regex=False)
        df['MargenObtenidoInv'] = pd.to_numeric(df['MargenObtenidoInv'], errors='coerce').fillna(0)
        
        # Convertir la columna "DiaFecha" a formato datetime (dd/mm/yyyy)
        df['DiaFecha'] = pd.to_datetime(df['DiaFecha'], format='%d/%m/%Y', errors='coerce')
        
        # Calcular la columna "DiferenciaMargen":
        df['DiferenciaMargen'] = np.where(
            df['VentaNetaenUnidades'] >= 1,
            np.where(
                df['Depto'] == "Ropa, Zapatería y Te (4)",
                df['MargenObtenidoVenta'] - 30,
                df['MargenObtenidoVenta'] - 35
            ),
            np.nan
        )
        # Asignar 0 a los valores NaN en DiferenciaMargen
        df['DiferenciaMargen'] = df['DiferenciaMargen'].fillna(0)
        
        # Calcular la columna "DifPesos":
        df['DifPesos'] = (df['DiferenciaMargen'] * df['VentaNetaenPesos']) / 100
        
        # Calcular la columna "dow":
        df['dow'] = (df['DiaFecha'].dt.weekday + 1) % 7
        
        # Limitar a 4 decimales las columnas indicadas
        df['MargenObtenidoInv'] = df['MargenObtenidoInv'].round(4)
        df['MargenObtenidoVenta'] = df['MargenObtenidoVenta'].round(4)
        df['DiferenciaMargen'] = df['DiferenciaMargen'].round(4)
        df['DifPesos'] = df['DifPesos'].round(4)
        
        # Convertir la columna "DiaFecha" a formato ISO (YYYY-MM-DD)
        df['DiaFecha'] = df['DiaFecha'].dt.strftime('%Y-%m-%d')
        
        # --- Fin de la integración de las nuevas columnas ---
        
        # Generar nombre del archivo procesado
        numero_filas = df.shape[0]
        output_dir = os.path.dirname(archivo_entrada)
        archivo_procesado = os.path.join(output_dir, f'e_{valor_segunda_fila}_{numero_filas}.csv')
        
        # Guardar DataFrame con encoding Latin1 (para que se procese correctamente)
        df.to_csv(archivo_procesado, index=False, encoding='latin1')
        print(f"Archivo procesado guardado como: {archivo_procesado}")
        
    except Exception as e:
        print(f'Error al procesar el archivo: {e}')

# =================== CONFIGURACIÓN DE SELENIUM ===================
from selenium.webdriver.chrome.options import Options

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--incognito')              # Modo incógnito para evitar conflictos de perfil
options.add_argument('--no-sandbox')             # Recomendado en Docker/Azure Functions
options.add_argument('--disable-dev-shm-usage')  # Evita problemas de memoria compartida

# Indicar la ubicación del binario de Chromium
options.binary_location = "/usr/bin/chromium"

# Configurar el directorio de descargas (usando /tmp, adecuado para Azure Functions)
DOWNLOAD_DIR = os.path.join("/tmp", "descargas")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
prefs = {"download.default_directory": DOWNLOAD_DIR}
options.add_experimental_option("prefs", prefs)

# Usar el chromedriver copiado en el contenedor
service = Service('/usr/local/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=options)

try:
    # 1. ABRIR CHEDLINK
    url = "https://chedlink.chedraui.com.mx/Artus/g940/projects/main.php"
    print(f"Abriendo URL: {url}")
    driver.get(url)
    time.sleep(3)  # Espera a que cargue la página

    # 2. INICIAR SESIÓN
    print("Buscando campos de usuario y contraseña...")
    usuario_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")

    print("Ingresando credenciales...")
    usuario_input.send_keys(CONFIG['chedraui']['USUARIO'])
    password_input.send_keys(CONFIG['chedraui']['PASSWORD'])
    password_input.send_keys(Keys.RETURN)  # Inicia sesión

    time.sleep(5)  # Espera a que la siguiente página cargue

    # 3. VERIFICAR SI LA SESIÓN SE INICIÓ
    if "login" in driver.current_url.lower():
        print("Parece que no se inició sesión. Verifica credenciales o selectores.")
    else:
        print("¡Sesión iniciada correctamente!")
        # 4. ABRIR REPORTE
        reporte_url = ("https://chedlink.chedraui.com.mx/Artus/g940/openfav.php?"
                       "bRep=0&key=67795&bPDF=0&bPPT=0&bExcel=0&bEditMode=0&ckid=")
        print(f"Abriendo reporte: {reporte_url}")
        driver.get(reporte_url)
        time.sleep(7)  # Espera a que cargue el reporte

        # 5. Cambiar a frame(0) y hacer clic en "botExcel"
        driver.switch_to.frame(0)
        driver.find_element(By.ID, "botExcel").click()

        # 6. Regresar al contenido principal y cambiar a frame(2)
        driver.switch_to.default_content()
        driver.switch_to.frame(2)

        # 7. Esperar y hacer clic en el elemento que inicia la descarga
        wait = WebDriverWait(driver, 20)
        element = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#menu_0_row_1 > .cellStyle:nth-child(2)")
        ))
        root_window = driver.current_window_handle
        old_handles = [root_window]
        element.click()

        # 8. Esperar que se abra una nueva ventana (para la descarga)
        new_window = wait_for_window(driver, old_handles, timeout=2)
        if new_window:
            driver.switch_to.window(new_window)
            print("Nueva ventana detectada. Esperando a que se descargue el reporte...")
            time.sleep(5)
            csv_file_path = wait_for_csv_file(DOWNLOAD_DIR, timeout=60)
            if csv_file_path:
                print("Archivo CSV detectado:", csv_file_path)
            else:
                print("No se detectó el archivo CSV en el directorio de descargas.")
            if new_window in driver.window_handles:
                driver.close()
            if root_window in driver.window_handles:
                driver.switch_to.window(root_window)
                print("Regresado a la ventana principal.")
        else:
            print("No se detectó nueva ventana tras el clic.")

        # 9. Guardar el HTML de la página actual
        page_source = driver.page_source
        with open("reporte_chedlink.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("Reporte guardado como reporte_chedlink.html.")

        # 10. Procesar el archivo CSV descargado
        if csv_file_path:
            print("Procesando archivo CSV descargado...")
            procesar_csv(csv_file_path)
        else:
            print("No se pudo procesar el CSV porque no se encontró en el directorio de descargas.")

except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    driver.quit()
