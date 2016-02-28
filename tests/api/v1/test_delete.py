from .base import BaseAPITest
from ptero_common import nicer_logging
import os
import signal
import uuid
import time


LOG = nicer_logging.getLogger(__name__)


class TestDelete(BaseAPITest):
    def setUp(self):
        super(TestDelete, self).setUp()
        self.pidfile = os.path.join(self.job_working_directory,
                str(uuid.uuid4()))

    def tearDown(self):
        self.cleanup()
        super(BaseAPITest, self).tearDown()

    def script_path(self, script_name):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.dirname(os.path.dirname(this_dir))
        return os.path.join(tests_dir, 'scripts', script_name)

    def cleanup(self):
        TIMEOUT = 2 * int(os.environ['PTERO_SHELL_COMMAND_DB_POLLING_INTERVAL'])
        start_time = time.time()
        while self.process_is_alive():
            if (time.time() - start_time) >= TIMEOUT:
                LOG.error("Found pidfile (%s)", self.pidfile)
                self.terminate_process(self.pidfile)
                self.assertTrue(False, msg="ERROR: Process was still running")
                break
            else:
                time.sleep(1)

    def process_is_alive(self):
        return os.path.exists(self.pidfile)

    @staticmethod
    def terminate_process(pidfile):
        with open(pidfile, 'r') as infile:
            pid = int(infile.readline())
        LOG.error("Terminating process with pid %s", pid)
        os.kill(pid, signal.SIGTERM)

    def test_delete_while_running(self):
        running_listener = self.create_webhook_server([200])

        job_id = str(uuid.uuid4())
        url = "%s/%s" % (self.jobs_url, job_id)
        put_response = self.put(url, {
            'commandLine': [self.script_path('make_file_while_running'),
                self.pidfile, 123],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'running': running_listener.url,
            },
        })
        self.assertEqual(put_response.status_code, 201)

        running_listener.stop()

        delete_response = self.delete(url)
        self.assertEqual(delete_response.status_code, 200)

        get_response = self.get(url)
        self.assertEqual(get_response.status_code,
                int(os.environ['PTERO_NO_SUCH_ENTITY_STATUS_CODE']))
