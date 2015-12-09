from .base import BaseAPITest
from ptero_common import nicer_logging
from ptero_common import statuses
import os
import signal
import uuid


LOG = nicer_logging.getLogger(__name__)


class TestCancel(BaseAPITest):
    def setUp(self):
        super(TestCancel, self).setUp()
        self.pidfile = os.path.join(self.job_working_directory,
                str(uuid.uuid4()))
        self.failed_listener = self.create_webhook_server([200])

    def tearDown(self):
        self.cleanup()
        super(BaseAPITest, self).tearDown()

    def script_path(self, script_name):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(os.path.dirname(this_dir))
        return os.path.join(tests_dir, 'scripts', script_name)

    def cleanup(self):
        if os.path.exists(self.pidfile):
            # give the (hopefully canceled) job the chance to kill the process.
            try:
                self.failed_listener.stop()
            except RuntimeError:
                # Since this file only gets created if the process runs, and
                # gets deleted once the process exits, its presence is an error.
                LOG.error("Found pidfile (%s)", self.pidfile)
                self.terminate_process(self.pidfile)
                self.assertTrue(False, msg="ERROR: Process was still running")

    @staticmethod
    def terminate_process(pidfile):
        with open(pidfile, 'r') as infile:
            pid = int(infile.readline())
        LOG.error("Terminating process with pid %s", pid)
        os.kill(pid, signal.SIGTERM)

    def test_canceling_while_running(self):
        running_listener = self.create_webhook_server([200])
        canceled_listener = self.create_webhook_server([200])

        job_id = str(uuid.uuid4())
        url = "%s/%s" % (self.jobs_url, job_id)
        put_response = self.put(url, {
            'commandLine': [self.script_path('make_file_while_running'),
                self.pidfile, 123],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'running': running_listener.url,
                'canceled': canceled_listener.url,
                'failed': self.failed_listener.url,
            },
        })
        self.assertEqual(put_response.status_code, 201)

        running_listener.stop()

        patch_response = self.patch(url, {"status": statuses.canceled})
        self.assertEqual(patch_response.status_code, 200)

        canceled_listener.stop()
        self.failed_listener.stop()

    def test_canceling_immediately(self):
        canceled_listener = self.create_webhook_server([200])

        job_id = str(uuid.uuid4())
        url = "%s/%s" % (self.jobs_url, job_id)
        put_response = self.put(url, {
            'commandLine': [self.script_path('make_file_while_running'),
                self.pidfile, 123],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'canceled': canceled_listener.url,
                'failed': self.failed_listener.url,
            },
        })
        self.assertEqual(put_response.status_code, 201)

        patch_response = self.patch(url, {"status": statuses.canceled})
        self.assertEqual(patch_response.status_code, 200)

        canceled_listener.stop()

    def test_canceling_after_ended(self):
        succeeded_listener = self.create_webhook_server([200])
        ended_listener = self.create_webhook_server([200, 200])
        canceled_listener = self.create_webhook_server([200])

        job_id = str(uuid.uuid4())
        url = "%s/%s" % (self.jobs_url, job_id)
        put_response = self.put(url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'succeeded': succeeded_listener.url,
                'ended': ended_listener.url,
                'canceled': canceled_listener.url,
            },
        })
        self.assertEqual(put_response.status_code, 201)

        succeeded_listener.stop()
        get_response = self.get(url)
        self.assertEqual(statuses.succeeded, get_response.DATA['status'])

        patch_response = self.patch(url, {"status": statuses.canceled})
        self.assertEqual(patch_response.status_code, 200)

        canceled_listener.stop()
        get_response = self.get(url)
        self.assertEqual(statuses.canceled, get_response.DATA['status'])

        try:
            ended_listener.stop()
            self.assertFalse(True, "More than one ended callback was sent")
        except RuntimeError:
            self.assertTrue(True, "Only one callback was sent")
