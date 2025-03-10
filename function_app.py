import os
import sys
import subprocess
import azure.functions as func
import logging

# Obtén la ruta absoluta a la carpeta de dependencias
package_path = os.path.join(os.getcwd(), '.python_packages', 'lib', 'site-packages')

# Crea un entorno (copiando el actual) y añade PYTHONPATH
env = os.environ.copy()
env["PYTHONPATH"] = package_path + os.pathsep + env.get("PYTHONPATH", "")

app = func.FunctionApp()

@app.function_name(name="RunBotFunction")
@app.timer_trigger(schedule="0 10 13 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def RunBotFunction(myTimer: func.TimerRequest) -> None:
    logging.info("Timer trigger ejecutado.")
    result = subprocess.run([sys.executable, "lanzador.py"], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        logging.error("Error: %s", result.stderr)
    else:
        logging.info("Éxito: %s", result.stdout)

@app.function_name(name="ManualRunBotFunction")
@app.route(route="manual-run", methods=["GET"])
def ManualRunBotFunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Ejecución manual del bot.")
    result = subprocess.run([sys.executable, "lanzador.py"], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        logging.error("Error: %s", result.stderr)
        return func.HttpResponse(f"Error: {result.stderr}", status_code=500)
    else:
        logging.info("Éxito: %s", result.stdout)
        return func.HttpResponse(f"Éxito: {result.stdout}", status_code=200)

@app.function_name(name="ListPackagesFunction")
@app.route(route="list-packages", methods=["GET"])
def ListPackagesFunction(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Ejecutando pip freeze para listar paquetes instalados...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, env=env)
        if result.returncode != 0:
            logging.error("Error al ejecutar pip freeze: %s", result.stderr)
            return func.HttpResponse(f"Error al ejecutar pip freeze:\n{result.stderr}", status_code=500)
        return func.HttpResponse(result.stdout, status_code=200, mimetype="text/plain")
    except Exception as e:
        logging.error("Excepción: %s", e)
        return func.HttpResponse(f"Excepción: {e}", status_code=500)

@app.function_name(name="CheckChromiumFunction")
@app.route(route="check-chromium", methods=["GET"])
def CheckChromiumFunction(req: func.HttpRequest) -> func.HttpResponse:
    """
    Ejecuta el comando 'which chromium-browser' para verificar si Chromium está instalado.
    """
    logging.info("Verificando la existencia de Chromium...")
    try:
        result = subprocess.run(["which", "chromium-browser"], capture_output=True, text=True, env=env)
        path = result.stdout.strip()
        if path:
            message = f"Chromium está instalado en: {path}"
        else:
            message = "Chromium no está instalado o no se encontró 'chromium-browser'."
        return func.HttpResponse(message, status_code=200, mimetype="text/plain")
    except Exception as e:
        logging.error("Error al verificar Chromium: %s", e)
        return func.HttpResponse(f"Error: {e}", status_code=500)
