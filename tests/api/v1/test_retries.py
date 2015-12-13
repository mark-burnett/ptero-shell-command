from .base import BaseAPITest
from ptero_common import statuses
import tempfile
import os


class TestRetries(BaseAPITest):
    def test_retry_succeed(self):
        running_listener = self.create_webhook_server([200, 200, 200])
        succeeded_listener = self.create_webhook_server([200])
        handle, filepath = tempfile.mkstemp()

        post_response = self.post(self.jobs_url, {
            'commandLine': ['bash', '-c',
                'if test -f %s; then exit 4; else exit 0; fi' % filepath],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.running: running_listener.url,
                statuses.succeeded: succeeded_listener.url,
            },
            'retrySettings': {
                'exitCode': 4,
                'initialInterval': 1,
                'maxInterval': 3,
                'attempts': 20,
            }
        })
        print "job_id: %s" % post_response.DATA['jobId']

        running_listener.stop()
        os.close(handle)
        os.remove(filepath)

        # retrySettings set so that it will retry long enough to ensure
        # listener will time out if it doesn't get succeeded webhook
        succeeded_listener.stop()
        self.assertTrue(True, "Retried at least 3 times and "
            "stopped after success")

    def test_retry_failed(self):
        running_listener = self.create_webhook_server([200, 200, 200])
        failed_listener = self.create_webhook_server([200])
        handle, filepath = tempfile.mkstemp()

        post_response = self.post(self.jobs_url, {
            'commandLine': ['bash', '-c',
                'if test -f %s; then exit 5; else exit 1; fi' % filepath],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.running: running_listener.url,
                statuses.failed: failed_listener.url,
            },
            'retrySettings': {
                'exitCode': 5,
                'initialInterval': 1,
                'maxInterval': 3,
                'attempts': 20,
            }
        })
        print "job_id: %s" % post_response.DATA['jobId']

        running_listener.stop()
        os.close(handle)
        os.remove(filepath)

        # retrySettings set so that it will retry long enough to ensure
        # listener will time out if it doesn't get failed webhook
        failed_listener.stop()
        self.assertTrue(True, "Retried at least 3 times and stopped "
                "after failure")
