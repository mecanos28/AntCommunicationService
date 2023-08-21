import logging
import boto3
import requests
import uuid

from os import getenv
from datetime import datetime
from flask import Flask, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
#from apscheduler.schedulers.background import BackgroundScheduler

## Swagger ##
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = 'static/swagger.json'  # Our API url (can of course be a local resource)

### Constantes ###
POLL_TO_ENTORNO_SECONDS = 300  # Actualmente configurado a 300 segundos para pruebas. Debe ser 60 segundos en producción.
ENTORNO_NEXT_ELEMENT_URL = "http://ec2-52-200-81-149.compute-1.amazonaws.com/api/environment/next-task"

# Pendientes de onbordear
HORMIGA_REQUEST_URL = "http://ec2-3-19-106-46.us-east-2.compute.amazonaws.com:38000/getHormiga" # Cambiar a la URL correcta cuando sepamos
HORMIGA_RETURN_URL = "http://ec2-3-19-106-46.us-east-2.compute.amazonaws.com:38000/returnHormiga" # Cambiar a la URL correcta cuando sepamos
INFORMAR_ATAQUE_URL = "http://colony-defense-service-env.eba-pmxaehhm.us-east-1.elasticbeanstalk.com:8080/swagger-ui/index.html" # Cambiar a la URL correcta cuando sepamos
INFORMAR_COMIDA_URL = "http://colony-food-service-env.eba-2q2j2x2m.us-east-1.elasticbeanstalk.com:8080/swagger-ui/index.html" # Cambiar a la URL correcta cuando sepamos

MOCK_ENTORNO_RESPUESTA_ENEMIGO = {
    "_id": "64dd6b46695b541fdf8bbbfb",
    "type": "enemy",
    "name": "Mariposa Monarca",
    "antsRequired": 7,
    "timeRequired": 14330
}

MOCK_ENTORNO_RESPUESTA_COMIDA = {
    "_id": "64dd6b46695b541fdf8bbbf0",
    "type": "food",
    "name": "Caramelo Duro",
    "antsRequired": 6,
    "timeRequired": 18173,
    "foodValue": 3
}

### Configuración de Registro (Logging) ###
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

### Configuración del Programador (Scheduler) ###
# def tarea_programada():
#     """Función para acceder al endpoint poll_entorno periódicamente."""
#     respuesta = requests.get('http://127.0.0.1:5000/poll-entorno')  # Asumiendo que Flask corre en el puerto 5000 por defecto
#     print(f"Respuesta de la tarea programada: {respuesta.status_code}")

# sched = BackgroundScheduler(daemon=True)
# sched.add_job(tarea_programada, 'interval', seconds=POLL_TO_ENTORNO_SECONDS)
# sched.start()

### Configuración de Flask ###
application = Flask(__name__)


### Configuración de AWS DynamoDB ###
dynamodb = boto3.resource('dynamodb', 
    region_name = getenv("REGION_NAME"), 
    aws_access_key_id = getenv('AWS_ACCESS_KEY_ID'), 
    aws_secret_access_key = getenv('AWS_SECRET_ACCESS_KEY')
    )

table = dynamodb.Table('Mensajes')

### Endpoints de API ###
# Este endpoint lo llama el programador (scheduler)
# para activar el poll hacia el servicio externo "entorno".
@application.route('/poll-entorno', methods=['GET'])
def endpoint_poll_entorno():
    """Endpoint para activar manualmente el poll."""
    _consultar_entorno()
    return {'status': 'consulta exitosa'}, 200

def _consultar_entorno():
    """Función para obtener datos del servicio externo entorno."""
    respuesta = _llamar_api_entorno()

    if respuesta.status_code == 200:
        data = respuesta.json()
        application.logger.info(f"Dato obtenido de {ENTORNO_NEXT_ELEMENT_URL}: {data}")

        # *guardar en dynamo* *estado: pendiente*
        # guardar_datos(data)

        # pedir hormiga para los datos recibidos
        respuesta_pedir_hormiga = _llamar_api_pedir_hormiga()

        # si recibimos hormiga, asignar hormiga a los datos recibidos *guardar en dynamo* *estado: trabajando*
        # retrieve_data(id)
        # asignar_hormiga(data, respuesta_pedir_hormiga)
        # guardar_datos(data)

        # añadir timer de 1 minuto

        # cuando el timer llegue a 0. llamar a subsistema correspondiente. devolver hormiga. *guardar en dynamo* *estado: terminado*\

        enviar_mensaje(data, respuesta_pedir_hormiga)
        #_llamar_api_devolver_hormiga(respuesta_pedir_hormiga.json().get('id'))

    else:
        application.logger.warning(f"No se pudo obtener datos de {ENTORNO_NEXT_ELEMENT_URL}. Estado: {respuesta.status_code}")


def enviar_mensaje(data, respuesta_pedir_hormiga):
    data_a_enviar = {
        'id': data.get('_id'),
        'type': data.get('type'),
        'name': data.get('name'),
        'antsRequired': data.get('antsRequired'),
        'timeRequired': data.get('timeRequired'),
        'foodValue': data.get('foodValue'),
        'id_hormiga': respuesta_pedir_hormiga.json().get('id')
    }
    if (data.get('type') == 'enemy'):
        _llamar_api_informar_ataque(data)
    else:
        _llamar_api_informar_comida(data)


def _llamar_api_entorno():
    try:
        application.logger.info(f"Consultando {ENTORNO_NEXT_ELEMENT_URL}")
        respuesta = requests.get(ENTORNO_NEXT_ELEMENT_URL)
        print(jsonify(respuesta))
        if (respuesta.status_code == 200):
            application.logger.info(f"Dato obtenido de {ENTORNO_NEXT_ELEMENT_URL}")
            return respuesta
    except:
        application.logger.warning(f"No se pudo obtener datos de {ENTORNO_NEXT_ELEMENT_URL}. Estado: {respuesta.status_code}")

def _llamar_api_pedir_hormiga():
    try:
        application.logger.info(f"Consultando {HORMIGA_REQUEST_URL}")
        respuesta = requests.get(HORMIGA_REQUEST_URL)
        if (respuesta.status_code == 200):
            application.logger.info(f"Hormiga obtenida de {HORMIGA_REQUEST_URL}")
            return respuesta
    except:
        application.logger.warning(f"No se pudo obtener datos de {HORMIGA_REQUEST_URL}. Estado: {respuesta.status_code}")

def _llamar_api_devolver_hormiga(id_hormiga):
    try:
        application.logger.info(f"Consultando {HORMIGA_RETURN_URL}")
        respuesta = requests.post(HORMIGA_RETURN_URL, json={"hormiga": {"id": id_hormiga}})
        if (respuesta.status_code == 200):
            application.logger.info(f"Hormiga devuelta a {HORMIGA_RETURN_URL} con éxito id: {id_hormiga}")
            return respuesta
        else:
            application.logger.warning(f"No se pudo devolver hormiga a {HORMIGA_RETURN_URL}. Estado: {respuesta.status_code}")
    except:
        # manage respuesta could be null
        application.logger.warning(f"No se pudo obtener datos de {HORMIGA_RETURN_URL}. Estado: {respuesta.status_code}")

def _llamar_api_informar_ataque(data):
    try:
        application.logger.info(f"Consultando {INFORMAR_ATAQUE_URL}")
        respuesta = requests.post(INFORMAR_ATAQUE_URL, data)
        if (respuesta.status_code == 200):
            application.logger.info(f"Información de ataque enviada a {INFORMAR_ATAQUE_URL} con éxito data: {data}")
            return respuesta
        else:
            application.logger.warning(f"No se pudo enviar información de ataque a {INFORMAR_ATAQUE_URL}. Estado: {respuesta.status_code}")
    except:
        # manage respuesta could be null
        application.logger.warning(f"No se pudo obtener datos de {INFORMAR_ATAQUE_URL}. Estado: {respuesta.status_code}")

def _llamar_api_informar_comida(data):
    try:
        application.logger.info(f"Consultando {INFORMAR_COMIDA_URL}")
        respuesta = requests.post(INFORMAR_COMIDA_URL, data)
        if (respuesta.status_code == 200):
            application.logger.info(f"Información de comida enviada a {INFORMAR_COMIDA_URL} con éxito data: {data}")
            return respuesta
        else:
            application.logger.warning(f"No se pudo enviar información de comida a {INFORMAR_COMIDA_URL}. Estado: {respuesta.status_code}")
    except:
        # manage respuesta could be null
        application.logger.warning(f"No se pudo obtener datos de {INFORMAR_COMIDA_URL}. Estado: {respuesta.status_code}")


def guardar_datos(data):
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

def obtener_datos(id):
    """Función para obtener los datos de DynamoDB."""
    respuesta = table.get_item(Key={'id': id})
    return respuesta.get('Item', None)


# No se usa, pero se deja como ejemplo de cómo recibir mensajes entrantes.
@application.route('/recibir-mensaje', methods=['POST'])
def manejar_solicitud():
    """Endpoint para recibir y procesar mensajes entrantes."""
    data = request.get_json()
    application.logger.info(f"Mensaje recibido a través de la API: {data}")
    guardar_datos(data)
    return {'status': 'mensaje recibido con éxito'}, 200

#Echo para revisar repido si la app responde
@application.route('/echo', methods=['GET', 'POST'])
def echo():
   return jsonify(request.json)


### Ejecución Principal ###
if __name__ == '__main__':
    # Debido a que el programador (scheduler) se ejecuta en un hilo separado,
    # tenemos que desactivar el recargado automático de Flask para evitar que se ejecuten
    # múltiples instancias del programador.
    application.run(debug=False, use_reloader=False)
