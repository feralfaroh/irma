import azure.functions as func
import logging
import subprocess
import sys

app = func.FunctionApp()

@app.function_name(name="RunBotFunction")
@app.timer_trigger(schedule="0 0 7 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def RunBotFunction(myTimer: func.TimerRequest) -> None:
    logging.info("Timer trigger ejecutado.")
    result = subprocess.run([sys.executable, "lanzador.py"], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("Error: %s", result.stderr)
    else:
        logging.info("Éxito: %s", result.stdout)

@app.function_name(name="ManualRunBotFunction")
@app.route(route="manual-run", methods=["GET"])
def ManualRunBotFunction(req: func.HttpRequest) -> func.HttpResponse:
    # Llama a la misma lógica que en RunBotFunction
    logging.info("Ejecución manual del bot.")
    result = subprocess.run([sys.executable, "lanzador.py"], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("Error: %s", result.stderr)
        return func.HttpResponse(f"Error: {result.stderr}", status_code=500)
    else:
        logging.info("Éxito: %s", result.stdout)
        return func.HttpResponse(f"Éxito: {result.stdout}", status_code=200)
