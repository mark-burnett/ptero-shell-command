from .base import BaseAPITest
from ptero_common import nicer_logging
from ptero_common import statuses
import uuid


LOG = nicer_logging.getLogger(__name__)


class TestCancel(BaseAPITest):
    def test_canceling_after_ended(self):
        ended_listener = self.create_webhook_server([200])
        canceled_listener = self.create_webhook_server([200])

        job_id = str(uuid.uuid4())
        url = "%s/%s" % (self.jobs_url, job_id)
        put_response = self.put(url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': ended_listener.url,
                'canceled': canceled_listener.url,
            },
        })
        self.assertEqual(put_response.status_code, 201)

        ended_listener.stop()
        get_response = self.get(url)
        self.assertEqual(statuses.succeeded, get_response.DATA['status'])

        patch_response = self.patch(url, {"status": statuses.canceled})
        self.assertEqual(patch_response.status_code, 200)

        canceled_listener.stop()
        get_response = self.get(url)
        self.assertEqual(statuses.canceled, get_response.DATA['status'])
