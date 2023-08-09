import logging
from flask import Flask, request, jsonify
import boto3
import requests
import json
import uuid
from datetime import datetime
from flask_apscheduler import APScheduler

# Configure root logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

application = Flask(__name__)
scheduler = APScheduler()

# Use the root logger for Flask as well
application.logger.addHandler(logger.handlers[0])
application.logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('your-table-name')

#################################### Constantes ####################################
POLL_TO_ENTORNO_SECONDS = 10  # 10 minutes

# Reemplzar cuando tengamos el URL disponible
ENTORNO_NEXT_ELEMENT_URL = "http://placeholder.url/api/environment/next"

@application.route('/poll-entorno', methods=['GET'])
def poll_entorno_endpoint():
    poll_entorno()
    return {'status': 'polled successfully'}, 200

def poll_entorno():
    application.logger.info(f"Polling {ENTORNO_NEXT_ELEMENT_URL}")
    response = requests.get(ENTORNO_NEXT_ELEMENT_URL)
    if response.status_code == 200:
        data = response.json()
        application.logger.info(f"Dato obtenido de {ENTORNO_NEXT_ELEMENT_URL}: {data}")
        handle_received_data(data)
    else:
        application.logger.warning(f"No se pudo obtener datos de {ENTORNO_NEXT_ELEMENT_URL}. Status: {response.status_code}")

def handle_received_data(data):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    item = {
        'id': str(uuid.uuid4()),
        'externalId': data.get('_id'),
        'type': data.get('type'),
        'name': data.get('name'),
        'antsRequired': data.get('antsRequired'),
        'timeRequired': data.get('timeRequired'),
        'foodValue': data.get('foodValue', None),
        'datetime': current_time
    }

    response = table.put_item(Item=item)
    application.logger.info(f"Mensaje guardado en DynamoDB: {item}")

@application.route('/recibir-mensaje', methods=['POST'])
def handle_request():
    data = request.get_json()
    application.logger.info(f"Mensaje recibido a través de API: {data}")
    handle_received_data(data)
    return {'status': 'success receiving message'}, 200

def scheduler_task():
    # This function will hit the poll_entorno endpoint
    response = requests.get('http://localhost:5000/poll-entorno')  # Assuming Flask runs on default 5000 port
    print(f"Scheduled task response: {response.status_code}")

if __name__ == '__main__':
    scheduler.init_app(application)
    scheduler.add_job(id='polling_task', func=scheduler_task, trigger='interval', seconds=POLL_TO_ENTORNO_SECONDS)
    scheduler.start()
    application.run(debug=False, use_reloader=False)
