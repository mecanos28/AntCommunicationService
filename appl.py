import unittest
from unittest.mock import patch, MagicMock, Mock

from application import application, _consultar_entorno, guardar_datos, obtener_datos, \
    _llamar_api_entorno


class TestMainMethods(unittest.TestCase):

    @patch("application.table.put_item")
    def test_guardar_datos(self, mock_put_item):
        data = {
            "_id": "12345",
            "type": "testType",
            "name": "testName",
            "antsRequired": 10,
            "timeRequired": 5,
            "foodValue": 3
        }

        guardar_datos(data, "Test")
        mock_put_item.assert_called()

    @patch("application.table.get_item")
    def test_obtener_datos(self, mock_get_item):
        mock_get_item.return_value = {"Item": {"Id": "12345", "Data": "TestData", "Estado": "Test"}}
        result = obtener_datos("12345")
        self.assertEqual(result, {"Id": "12345", "Data": "TestData", "Estado": "Test"})

    @patch("application.requests.get")
    def test_llamar_api_entorno_with_mock(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "_id": '64dd6b46695b541fdf8bbbfd',
            'antsRequired': 9,
            'name': 'Escarabajo Titán',
            'timeRequired': 13340,
            'type': 'enemy'
        }
        mock_get.return_value = mock_response

        response = _llamar_api_entorno()

        self.assertEqual(response.status_code, 200)



# Add more test methods for other functions you want to test.

if __name__ == "__main__":
    unittest.main()