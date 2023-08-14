import boto3
import uuid
import json

from os import getenv
from boto3 import resource
from dotenv import load_dotenv, dotenv_values
#from boto3.dynamo.conditions import Attr, Key

load_dotenv()

dynamodb = boto3.resource('dynamodb', 
    region_name = getenv("REGION_NAME"), 
    aws_access_key_id = getenv('AWS_ACCESS_KEY_ID'), 
    aws_secret_access_key = getenv('AWS_SECRET_ACCESS_KEY')
    )

id_db = uuid.uuid4()
table = dynamodb.Table('Mensajes')


# Esto es solo para probar si boto se conecta con dynamo correctamente
def insert(mensaje):
    id = str(id_db)
    response = table.put_item(Item = mensaje)
    return response

