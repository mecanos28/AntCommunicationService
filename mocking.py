import uuid
from random import random

MOCK_ENTORNO = [
    {
        "_id": "64dd6b46695b541fdf8bbbfc",
        "type": "enemy",
        "name": "Avispa Guerrera",
        "antsRequired": 8,
        "timeRequired": 15320
    },
    {
        "_id": "64dd6b46695b541fdf8bbbfd",
        "type": "enemy",
        "name": "Escarabajo Titán",
        "antsRequired": 9,
        "timeRequired": 13340
    },
    {
        "_id": "64dd6b46695b541fdf8bbbfe",
        "type": "enemy",
        "name": "Araña Tejedora",
        "antsRequired": 7,
        "timeRequired": 15870
    },
    {
        "_id": "64dd6b46695b541fdf8bbbff",
        "type": "enemy",
        "name": "Hormiga León",
        "antsRequired": 6,
        "timeRequired": 14000
    },
    {
        "_id": "64dd6b46695b541fdf8bbd00",
        "type": "enemy",
        "name": "Mosquito Tigre",
        "antsRequired": 5,
        "timeRequired": 15050
    },
    {
        "_id": "64dd6b46695b541fdf8bbd01",
        "type": "enemy",
        "name": "Mantis Religiosa",
        "antsRequired": 10,
        "timeRequired": 13780
    },
    {
        "_id": "64dd6b46695b541fdf8bbd02",
        "type": "enemy",
        "name": "Escarabajo Dorado",
        "antsRequired": 11,
        "timeRequired": 16090
    },
    {
        "_id": "64dd6b46695b541fdf8bbd03",
        "type": "food",
        "name": "Manzana Roja",
        "antsRequired": 4,
        "timeRequired": 17600,
        "foodValue": 5
    },
    {
        "_id": "64dd6b46695b541fdf8bbd04",
        "type": "food",
        "name": "Grano de Azúcar",
        "antsRequired": 3,
        "timeRequired": 19000,
        "foodValue": 2
    },
    {
        "_id": "64dd6b46695b541fdf8bbd05",
        "type": "food",
        "name": "Miga de Pan",
        "antsRequired": 4,
        "timeRequired": 17850,
        "foodValue": 4
    },
    {
        "_id": "64dd6b46695b541fdf8bbd06",
        "type": "food",
        "name": "Trozo de Queso",
        "antsRequired": 6,
        "timeRequired": 16500,
        "foodValue": 6
    },
    {
        "_id": "64dd6b46695b541fdf8bbd07",
        "type": "food",
        "name": "Gota de Miel",
        "antsRequired": 7,
        "timeRequired": 17320,
        "foodValue": 7
    },
    {
        "_id": "64dd6b46695b541fdf8bbd08",
        "type": "food",
        "name": "Pedazo de Chocolate",
        "antsRequired": 5,
        "timeRequired": 18010,
        "foodValue": 6
    },
    {
        "_id": "64dd6b46695b541fdf8bbd09",
        "type": "food",
        "name": "Fragmento de Pastel",
        "antsRequired": 8,
        "timeRequired": 16340,
        "foodValue": 9
    },
    {
        "_id": "64dd6b46695b541fdf8bbd0a",
        "type": "food",
        "name": "Bocado de Fruta",
        "antsRequired": 4,
        "timeRequired": 17580,
        "foodValue": 4
    }
]

MOCK_HORMIGA_RESPONSE = {
    "id": 0,
    "type": "worker",
    "name": "Hormiga Obrera",
    "birthday": "2021-06-01T00:00:00.000Z"
}


def get_hormiga_response_with_generated_id():
    return {**MOCK_HORMIGA_RESPONSE, "id": str(uuid.uuid4())}


def _mocked_response(response_data):
    class MockResponse:
        def __init__(self, data):
            self.data = data
            self.status_code = 200

        def json(self):
            return self.data

    return MockResponse(response_data)


## get random MOCK_ENTORNO array element
def _get_random_mock_entorno():
    return _mocked_response(MOCK_ENTORNO[int(random() * len(MOCK_ENTORNO))])
