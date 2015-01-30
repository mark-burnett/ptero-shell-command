from .base import BaseAPITest
import os
import re
import unittest

class TestDropPermissions(BaseAPITest):
    def test_running_job_as_root_should_fail(self):
        webhook_target = self.create_webhook_server([200])

        user = 'root'
        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'error': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'error',
                'jobId': post_response.DATA['jobId'],
                'errorMessage': 'Refusing to execute job as root user'
            },
        ]
        self.assertEqual(expected_data, webhook_data)

    @unittest.skipIf(not os.environ.get('PTERO_SHELL_COMAMND_TEST_WITH_ROOT_WORKERS'),
        "not running fork worker as root")
    def test_job_user_and_group(self):
        webhook_target = self.create_webhook_server([200])

        user = 'nobody'
        primarygroup = 'nobody'
        os.chmod(self.job_working_directory, 0777)
        self.post(self.jobs_url, {
            'commandLine': ['id'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        id_result = webhook_data[0]['stdout']

        actual_user = self._find_match(r"uid=\d+\((\w+)\)", id_result)
        actual_primarygroup = self._find_match(r"gid=\d+\((\w+)\)", id_result)

        self.assertEqual(user, actual_user)
        self.assertEqual(primarygroup, actual_user)

    @unittest.skipIf(os.environ.get('PTERO_SHELL_COMAMND_TEST_WITH_ROOT_WORKERS'),
        "running fork worker as root")
    def test_user_of_job(self):
        webhook_target = self.create_webhook_server([200])

        user = 'nobody'
        post_response = self.post(self.jobs_url, {
            'commandLine': ['whoami'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'error': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'error',
                'jobId': post_response.DATA['jobId'],
                'errorMessage': 'Failed to setreuid: Operation not permitted'
            }
        ]
        self.assertEqual(expected_data, webhook_data)

    def test_exception_on_setuid_failure(self):
        webhook_target = self.create_webhook_server([200])

        user = '_no_such_user'
        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'error': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'error',
                'jobId': post_response.DATA['jobId'],
                'errorMessage': 'getpwnam(): name not found: _no_such_user'
            }
        ]
        self.assertEqual(expected_data, webhook_data)

    def _find_match(self, regexp, target):
        match = re.search(regexp, target)
        if match:
            return match.group(1)
        else:
            return ''
