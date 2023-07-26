from flask import Flask, request, app
# import boto3
# import requests
# import json
# import time

app = Flask(__name__)
# dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('your-table-name')
# queue = boto3.client('sqs').get_queue_url(QueueName='your-queue-name')['QueueUrl']


@app.route('/recibir-mensaje', methods=['POST'])
def handle_request():
    data = request.get_json()
    print('Mensaje recibido: ', data)

    # Store data in DynamoDB
    ## Console log it would save here. Implement later.



    # item_id = data.get('id')
    # response = table.put_item(
    #     Item={
    #         'id': item_id,
    #         'data': json.dumps(data)
    #     }
    # )

    # Send message to SQS with delay
    ## Console log it would send SQS message here. Implement later.
    # response = boto3.client('sqs').send_message(
    #     QueueUrl=queue,
    #     MessageBody=json.dumps(data),
    #     DelaySeconds=60
    # )

    return {'status': 'success'}, 200


if __name__ == '__main__':
    app.run(debug=True)
