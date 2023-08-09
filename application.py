import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
import boto3
import requests
import uuid
from datetime import datetime

### Configuración de Registro (Logging) ###
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

### Configuración del Programador (Scheduler) ###
def tarea_programada():
    """Función para acceder al endpoint poll_entorno periódicamente."""
    respuesta = requests.get('http://127.0.0.1:5000/poll-entorno')  # Asumiendo que Flask corre en el puerto 5000 por defecto
    print(f"Respuesta de la tarea programada: {respuesta.status_code}")

sched = BackgroundScheduler(daemon=True)
sched.add_job(tarea_programada, 'interval', seconds=5)
sched.start()

### Configuración de Flask ###
application = Flask(__name__)

### Constantes ###
POLL_TO_ENTORNO_SECONDS = 10  # Actualmente configurado a 10 segundos para pruebas
ENTORNO_NEXT_ELEMENT_URL = "http://placeholder.url/api/environment/next"  # Reemplazar con la URL real cuando esté disponible

MOCK_ENTORNO_RESPUESTA = {
    "_id": "mock_id",
    "type": "mock_type",
    "name": "mock_name",
    "antsRequired": 5,
    "timeRequired": 10,
    "foodValue": 7
}

### Configuración de AWS DynamoDB ###
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('your-table-name')

### Endpoints de API ###
# Este endpoint lo llama el programador (scheduler)
# para activar el poll hacia el servicio externo "entorno".
@application.route('/poll-entorno', methods=['GET'])
def endpoint_poll_entorno():
    """Endpoint para activar manualmente la encuesta."""
    _consultar_entorno()
    return {'status': 'consulta exitosa'}, 200

def _consultar_entorno():
    """Función para obtener datos del servicio externo entorno."""
    application.logger.info(f"Consultando {ENTORNO_NEXT_ELEMENT_URL}")
    # Verificar si el URL es un placeholder, y en tal caso, usar datos mock
    if ENTORNO_NEXT_ELEMENT_URL == "http://placeholder.url/api/environment/next":
        application.logger.info(f"Usando datos simulados para {ENTORNO_NEXT_ELEMENT_URL}")
        application.logger.info(f"Esto escribiría en DynamoDB: {MOCK_ENTORNO_RESPUESTA}")
        return

    respuesta = requests.get(ENTORNO_NEXT_ELEMENT_URL)
    if respuesta.status_code == 200:
        data = respuesta.json()
        application.logger.info(f"Dato obtenido de {ENTORNO_NEXT_ELEMENT_URL}: {data}")
        procesar_datos_recibidos_de_entorno(data)
    else:
        application.logger.warning(f"No se pudo obtener datos de {ENTORNO_NEXT_ELEMENT_URL}. Estado: {respuesta.status_code}")

def procesar_datos_recibidos_de_entorno(data):
    """Función para procesar los datos recibidos y guardar en DynamoDB."""
    tiempo_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    item = {
        'id': str(uuid.uuid4()),
        'externalId': data.get('_id'),
        'type': data.get('type'),
        'name': data.get('name'),
        'antsRequired': data.get('antsRequired'),
        'timeRequired': data.get('timeRequired'),
        'foodValue': data.get('foodValue', None),
        'datetime': tiempo_actual
    }
    respuesta = table.put_item(Item=item)
    application.logger.info(f"Dato guardado en DynamoDB: {item}")


# No se usa, pero se deja como ejemplo de cómo recibir mensajes entrantes.
@application.route('/recibir-mensaje', methods=['POST'])
def manejar_solicitud():
    """Endpoint para recibir y procesar mensajes entrantes."""
    data = request.get_json()
    application.logger.info(f"Mensaje recibido a través de la API: {data}")
    procesar_datos_recibidos_de_entorno(data)
    return {'status': 'mensaje recibido con éxito'}, 200

### Ejecución Principal ###
if __name__ == '__main__':
    # Debido a que el programador (scheduler) se ejecuta en un hilo separado,
    # tenemos que desactivar el recargado automático de Flask para evitar que se ejecuten
    # múltiples instancias del programador.
    application.run(debug=False, use_reloader=False)
