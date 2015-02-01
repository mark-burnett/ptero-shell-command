from .base import BaseAPITest
import json


class TestMockWebserver(BaseAPITest):
    def test_mock_webserver_works(self):
        webhook_target = self.create_webhook_server([302])
        import requests
        request_body = {"bob": "hi im your friend"}
        response = requests.put(
            webhook_target.url, json.dumps(request_body))
        self.assertEqual(302, response.status_code)

        datas = webhook_target.stop()
        self.assertEqual(request_body, datas[0])
