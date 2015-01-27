from ptero_common.logging_configuration import logged_request
import celery
import logging
import requests
import json

LOG = logging.getLogger(__name__)
__all__ = ['WebhookTask']


class WebhookTask(celery.Task):
    ignore_result = True
    def run(self, url, **kwargs):
        response = logged_request.put(
            url, data=self.body(kwargs),
            headers={'Content-Type': 'application/json'}, logger=LOG)

    def body(self, kwargs):
        return json.dumps(kwargs)
