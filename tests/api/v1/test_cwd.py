from .base import BaseAPITest
import os
from ptero_common import statuses
import logging

LOG = logging.getLogger(__name__)


class TestCwd(BaseAPITest):
    def test_job_working_directory(self):
        webhook_target = self.create_webhook_server([200])

        post_data = {
            'commandLine': ['/bin/pwd'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        }

        self.post(self.jobs_url, post_data)

        webhook_data = webhook_target.stop()
        actual_working_directory = webhook_data[0]['stdout'].strip('\n')
        self.assertEqual(self.job_working_directory, actual_working_directory)

    def test_job_working_directory_does_not_exist(self):
        webhook_target = self.create_webhook_server([200])

        post_data = {
            'commandLine': ['/bin/pwd'],
            'user': self.job_user,
            'workingDirectory': '/does/not/exist',
            'webhooks': {
                statuses.errored: webhook_target.url,
            },
        }

        post_response = self.post(self.jobs_url, post_data)
        webhook_data = webhook_target.stop()
        self.assertEqual(post_response.status_code, 201)

        self.assertEqual(webhook_data[0]['status'], statuses.errored)
        self.assertTrue(webhook_data[0]['statusHistory'][-1][
            'message'].endswith('No such file or directory'))

    def test_job_working_directory_access_denied(self):
        webhook_target = self.create_webhook_server([200])

        os.chmod(self.job_working_directory, 0)
        post_data = {
            'commandLine': ['/bin/pwd'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.errored: webhook_target.url,
            },
        }

        post_response = self.post(self.jobs_url, post_data)
        webhook_data = webhook_target.stop()
        self.assertEqual(post_response.status_code, 201)

        self.assertEqual(webhook_data[0]['status'], statuses.errored)
        self.assertTrue(webhook_data[0]['statusHistory'][-1][
            'message'].endswith('Permission denied'))
