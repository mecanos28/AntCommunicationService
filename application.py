import logging
from random import random

import boto3
import requests
import uuid

from os import getenv
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from botocore.exceptions import ClientError

## Swagger ##
from mocking import _mocked_response, \
    MOCK_HORMIGA_RESPONSE, _get_random_mock_entorno, get_hormiga_response_with_generated_id

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = 'static/swagger.json'  # Our API url (can of course be a local resource)

### Constantes ###
POLL_TO_ENTORNO_SECONDS = 60  # Actualmente configurado a 10 segundos para pruebas. Debe ser 60 segundos en producción.
POLL_TO_RETURN= 60 #Configurado en 10 segundos para pruebas 
ENTORNO_NEXT_ELEMENT_URL = "http://ec2-52-200-81-149.compute-1.amazonaws.com/api/environment/next-task"
ENTORNO_POLLING_ACTIVE = True
#ENTORNO_TIMER_RETURN = True

IS_MOCKING_ALL_APIS = False
IS_MOCKING_ENTORNO = False
IS_MOCKING_HORMIGA_REQUEST = False
IS_MOCKING_HORMIGA_RETURN = False
IS_MOCKING_INFORMAR_ATAQUE = False
IS_MOCKING_INFORMAR_COMIDA = False

# Pendientes de onbordear
HORMIGA_REQUEST_URL = "http://ec2-3-132-148-116.us-east-2.compute.amazonaws.com:38000/v1/getHormiga?cantidad=1&type=comunicacion'" # Cambiar a la URL correcta cuando sepamos
HORMIGA_RETURN_URL = "http://ec2-3-19-106-46.us-east-2.compute.amazonaws.com:38000/v1/killHormiga" # Cambiar a la URL correcta cuando sepamos
INFORMAR_ATAQUE_URL = "http://colony-defense-service-env.eba-pmxaehhm.us-east-1.elasticbeanstalk.com:8080/api/attack-handler/create" # Cambiar a la URL correcta cuando sepamos
INFORMAR_COMIDA_URL = "http://100.26.157.202/swagger/index.html/harvest" # Cambiar a la URL correcta cuando sepamos


### Configuración de Registro (Logging) ###
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

### Configuración del Programador (Scheduler) ###
def tarea_programada():
    """Función para acceder al endpoint poll_entorno periódicamente."""
    respuesta = requests.get('http://127.0.0.1:5000/poll-entorno')  # Asumiendo que Flask corre en el puerto 5000 por defecto
    print(f"Respuesta de la tarea programada: {respuesta.status_code}")

if ENTORNO_POLLING_ACTIVE:
    print("Iniciando scheduler... para poll_entorno")
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(tarea_programada, 'interval', seconds=POLL_TO_ENTORNO_SECONDS)
    sched.start()

### Configuración de Flask ###
application = Flask(__name__)
api = Api(application)

ns = api.namespace('Mensajes', description='Operaciones con Mensajes')
integration_ns = api.namespace('Integracion' , description='Integracion con otros APIs')

dynamodb_record_model = api.model('Mensaje', {
    'Id':fields.String(readonly=True, description='DynamoDB record Id'),
    'Estado':fields.String(required=True, description='Estado del mensaje'),
    'Data':fields.String(required=True, description='El mensaje'),
    'Hormiga':fields.String(required=False, description='Id de la hormiga asignada')
})

message_input_model = api.model('Data',{
    'Estado':fields.String(required=True, description='Estado del mensaje'),
    'Data': fields.String(required=True, description='El objeto mensaje convertido en string')
})

message_update_input_model = api.model('Update',{
    'Estado':fields.String(required=True, description='Estado del mensaje'),
    'Hormiga': fields.String(required=True, description='El id de la hormiga string')
})


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

    if respuesta and respuesta.status_code == 200:
        data = respuesta.json()
        application.logger.info(f"Dato obtenido de {ENTORNO_NEXT_ELEMENT_URL}: {data}")

        # *guardar en dynamo* *estado: pendiente*
        id_mensaje_recibido = guardar_datos(data, "Recibido")
        #application.logger.info(f"Dato guardado en DynamoDB: {str(dato_guardado)}")
        # pedir hormiga para los datos recibidos
        respuesta_pedir_hormiga = _llamar_api_pedir_hormiga()
        application.logger.info(f"Respuesta de pedir hormiga: {str(respuesta_pedir_hormiga)}")

        # si recibimos hormiga, asignar hormiga a los datos recibidos *guardar en dynamo* *estado: trabajando*
        #id_mensaje_recibido = dato_guardado.id
        id_hormiga= respuesta_pedir_hormiga["id"]
        
        if id_hormiga is None:
            respuesta_pedir_hormiga = _llamar_api_pedir_hormiga()
            application.logger.info(f"Respuesta de pedir hormiga: {str(respuesta_pedir_hormiga)}")
            id_hormiga=respuesta_pedir_hormiga.id 

        actualizar_mensaje(id_mensaje_recibido, "Procesando", id_hormiga)

        # añadir timer de 1 minuto, se pasa como parametro en segundos
        #if ENTORNO_TIMER_RETURN:
                #print("Iniciando scheduler... para timer de hormiga")
                #scheduler = BackgroundScheduler(daemon=True)
                #scheduler.add_job(enviar_mensaje(dato_guardado), 'interval', seconds=POLL_TO_RETURN)
                #scheduler.start()
        # cuando el timer llegue a 0. llamar a subsistema correspondiente. devolver hormiga. *guardar en dynamo* *estado: terminado*\

        enviar_mensaje(data)
        actualizar_estado(id_mensaje_recibido, "Procesado")

        application.logger.info("Se envia mensaje con datos")
        
        _llamar_api_devolver_hormiga(id_hormiga)

    else:
        application.logger.warning(f"No se pudo obtener datos de {ENTORNO_NEXT_ELEMENT_URL}.")


def enviar_mensaje(data):
    print("Enviando un mensaje")
    if (data.get('type') == 'enemy'):
        _llamar_api_informar_ataque(data)
        application.logger.info(f"Enviando mensaje de ataque a {INFORMAR_ATAQUE_URL}" + str(data))
    else:
        _llamar_api_informar_comida(data)
        application.logger.info(f"Enviando mensaje de comida a {INFORMAR_COMIDA_URL}" + str(data))




def _llamar_api_entorno():
    if (IS_MOCKING_ALL_APIS or IS_MOCKING_ENTORNO):
        return _get_random_mock_entorno()

    try:
        application.logger.info(f"Consultando {ENTORNO_NEXT_ELEMENT_URL}")
        respuesta = requests.get(ENTORNO_NEXT_ELEMENT_URL)
        application.logger.info(respuesta)
        application.logger.info(respuesta.json())
        if respuesta.status_code == 200:
            application.logger.info(f"Dato obtenido de {ENTORNO_NEXT_ELEMENT_URL}")
            return respuesta
    except:
        application.logger.warning(f"No se pudo obtener datos de {ENTORNO_NEXT_ELEMENT_URL}. Estado: {respuesta.status_code}")

def _llamar_api_pedir_hormiga():
    if IS_MOCKING_ALL_APIS or IS_MOCKING_HORMIGA_REQUEST:
        return _mocked_response(get_hormiga_response_with_generated_id()).data

    try:
        # necesitamos pasar la ?cantidad=x&typo=''
        application.logger.info(f"Consultando {HORMIGA_REQUEST_URL}")
        respuesta = requests.get(HORMIGA_REQUEST_URL)
        if respuesta and respuesta.status_code == 200:
            application.logger.info(f"Hormiga obtenida de {HORMIGA_REQUEST_URL}")
            return respuesta
    except:
        application.logger.warning(f"No se pudo obtener datos de {HORMIGA_REQUEST_URL}. Estado: {respuesta.status_code}")


def _llamar_api_devolver_hormiga(id_hormiga):
    if IS_MOCKING_ALL_APIS or IS_MOCKING_HORMIGA_REQUEST:
        return _mocked_response({}).data

    try:
        application.logger.info(f"Consultando {HORMIGA_RETURN_URL}")
        respuesta = requests.post(HORMIGA_RETURN_URL, json={"hormiga": {"id": id_hormiga}})
        if respuesta and respuesta.status_code == 200:
            application.logger.info(f"Hormiga devuelta a {HORMIGA_RETURN_URL} con éxito id: {id_hormiga}")
            return respuesta
        else:
            application.logger.warning(f"No se pudo devolver hormiga a {HORMIGA_RETURN_URL}. Estado: {respuesta.status_code}")
    except:
        # manage respuesta could be null
        application.logger.warning(f"No se pudo obtener datos de {HORMIGA_RETURN_URL}. Estado: {respuesta.status_code}")


def _llamar_api_informar_ataque(data):
    if IS_MOCKING_ALL_APIS or IS_MOCKING_INFORMAR_ATAQUE:
        return _mocked_response({}).data

    try:
        application.logger.info(f"Consultando {INFORMAR_ATAQUE_URL}")
        respuesta = requests.post(INFORMAR_ATAQUE_URL, data)
        if respuesta and respuesta.status_code == 200:
            application.logger.info(f"Información de ataque enviada a {INFORMAR_ATAQUE_URL} con éxito data: {data}")
            return respuesta
        else:
            application.logger.warning(f"No se pudo enviar información de ataque a {INFORMAR_ATAQUE_URL}. Estado: {respuesta.status_code}")
    except:
        # manage respuesta could be null
        application.logger.warning(f"No se pudo obtener datos de {INFORMAR_ATAQUE_URL}. Estado: {respuesta.status_code}")

def _llamar_api_informar_comida(data):
    if IS_MOCKING_ALL_APIS or IS_MOCKING_INFORMAR_COMIDA:
        return _mocked_response({}).data

    try:
        application.logger.info(f"Consultando {INFORMAR_COMIDA_URL}")
        respuesta = requests.post(INFORMAR_COMIDA_URL, data)
        if respuesta and respuesta.status_code == 200:
            application.logger.info(f"Información de comida enviada a {INFORMAR_COMIDA_URL} con éxito data: {data}")
            return respuesta
        else:
            application.logger.warning(f"No se pudo enviar información de comida a {INFORMAR_COMIDA_URL}. Estado: {respuesta.status_code}")
    except:
        # manage respuesta could be null
        application.logger.warning(f"No se pudo obtener datos de {INFORMAR_COMIDA_URL}. Estado: {respuesta.status_code}")


def guardar_datos(data, estado):
    """Función para procesar los datos recibidos y guardar en DynamoDB."""
    tiempo_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    id = str(uuid.uuid4())
    data = {
        'id': id,
        'externalId': data.get('_id'),
        'type': data.get('type'),
        'name': data.get('name'),
        'antsRequired': data.get('antsRequired'),
        'timeRequired': data.get('timeRequired'),
        'foodValue': data.get('foodValue', None),
        'datetime': tiempo_actual
    }
    record = {
        'Id':id,
        'Estado': estado,
        'Data': data,
        'Hormiga': ''
    }
    respuesta = table.put_item(Item=record)
    application.logger.info(f"Dato guardado en DynamoDB: {record}")
    return id

def obtener_datos(id):
    """Función para obtener los datos de DynamoDB."""
    respuesta = table.get_item(Key={'Id': id})
    item = respuesta.get('Item', None)
    if item is None:
        api.abort(404, "Todo {} doesn't exist".format(id))
        return None
    else:        
        return item

    

## Acualiza el estado de un mensaje en Dynamo DB por Id.
def actualizar_estado(id, estado:str):
    response = table.update_item(
        Key = { 'Id': id },
        AttributeUpdates={
            'Estado': {
                'Value': estado,
                'Action': 'PUT'
            }
        },
        ReturnValues = "UPDATED_NEW" # retorna los valores actualizados
    )
    return response

## Acualiza la Hormiga de un mensaje en Dynamo DB por Id.
def actualizar_hormiga(id, hormiga:str):
    response = table.update_item(
        Key = { 'Id': id },
        AttributeUpdates={
            'Hormiga': {
                'Value': hormiga,
                'Action': 'PUT'
            }
        },
        ReturnValues = "UPDATED_NEW" # retorna los valores actualizados
    )
    return response

### Actualiza tanto el estado como la hormiga de un mensaje ###
def actualizar_mensaje(id, estado, hormiga):
    try:        
        response = table.update_item(
            Key = {'Id':id},
            UpdateExpression='SET Estado = :estado_new, Hormiga = :hormiga_new',
            ExpressionAttributeValues={
                ':estado_new': estado,
                ':hormiga_new': hormiga
            },
            ReturnValues = "UPDATED_NEW", # retorna los valores actualizados
            ConditionExpression = 'attribute_exists(Id)',
        )
        return response
    except ClientError as e:
        api.abort(404, "Todo {} doesn't exist".format(id))
        return None

# No se usa, pero se deja como ejemplo de cómo recibir mensajes entrantes.
@application.route('/recibir-mensaje', methods=['POST'])
def manejar_solicitud():
    """Endpoint para recibir y procesar mensajes entrantes."""
    data = request.get_json()
    application.logger.info(f"Mensaje recibido a través de la API: {data}")
    guardar_datos(data)
    return {'status': 'mensaje recibido con éxito'}, 200

################  Este es el API usando flask-restx ###############
@api.route('/hello')
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

@ns.route('/<string:id>')
@ns.response(404, 'Todo not found')
class MensajeAPI(Resource):
    '''Muestra mensajes'''
    @ns.doc('obtener_datos')
    @ns.marshal_list_with(dynamodb_record_model)
    def get(self, id):
        '''Obtener Mensaje por Id'''
        msj = obtener_datos(id)
        return msj
    
    @ns.expect(message_update_input_model)
    @ns.marshal_with(dynamodb_record_model)
    def put(self, id):
        '''Actualiza Estado & Hormiga del mensaje'''
        estado, hormiga = api.payload.values()
        return actualizar_mensaje(id, estado, hormiga)
    
@ns.route('/')
class MensajeCrear(Resource):
    @ns.expect(message_input_model)
    def post(self):
        '''Crear un Registro nuevo'''
        data, estado = api.payload.values()
        res = guardar_datos(data, estado)
        return res

@integration_ns.route('/entorno/next-task')
class EntornoNextTask(Resource):
    def get(self):
        '''Solicitar Tarea a Entorno'''
        response =  _llamar_api_entorno()
        data = response.json()
        return data

@integration_ns.route('/reina/getHormiga')
class HormigaReina(Resource):
    def get(self):
        '''Solicitar Hormiga a Hormiga Reina '''
        res = _llamar_api_pedir_hormiga()
        return res

### Ejecución Principal ###
if __name__ == '__main__':
    # Debido a que el programador (scheduler) se ejecuta en un hilo separado,
    # tenemos que desactivar el recargado automático de Flask para evitar que se ejecuten
    # múltiples instancias del programador.
    application.run(debug=False, use_reloader=False)
