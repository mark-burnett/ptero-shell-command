from .base import BaseAPITest
import os
import re
import unittest
from ptero_common import statuses

procfile = os.environ.get('PTERO_SHELL_COMMAND_TEST_PROCFILE', '')
TEST_WITH_ROOT = re.search('.*sudo.*', procfile)


class TestDropPermissions(BaseAPITest):
    def test_running_job_as_root_should_fail(self):
        webhook_target = self.create_webhook_server([200])

        user = 'root'
        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.errored: webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.errored)
        self.assertTrue(webhook_data[0]['statusHistory'][-1][
            'message'].startswith('Refusing to execute job as root user'))

    @unittest.skipIf(not TEST_WITH_ROOT, "not running fork worker as root")
    def test_job_user_and_group(self):
        webhook_target = self.create_webhook_server([200])

        user = 'nobody'
        primarygroup = 'nobody'
        os.chmod(self.job_working_directory, 0777)
        post_response = self.post(self.jobs_url, {
            'commandLine': ['id'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()
        id_result = webhook_data[0]['stdout']

        actual_user = self._find_match(r"uid=\d+\((\w+)\)", id_result)

        self.assertEqual(user, actual_user)
        self.assertEqual(primarygroup, actual_user)

    @unittest.skipIf(TEST_WITH_ROOT, "running fork worker as root")
    def test_user_of_job(self):
        webhook_target = self.create_webhook_server([200])

        user = 'nobody'
        post_response = self.post(self.jobs_url, {
            'commandLine': ['whoami'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.errored: webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.errored)
        self.assertTrue(webhook_data[0]['statusHistory'][-1][
            'message'].startswith('Attempted to submit job as invalid user'))

    def test_exception_on_setuid_failure(self):
        webhook_target = self.create_webhook_server([200])

        user = '_no_such_user'
        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.errored: webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.errored)
        self.assertTrue(webhook_data[0]['statusHistory'][-1][
            'message'].endswith('getpwnam(): name not found: _no_such_user'))

    def _find_match(self, regexp, target):
        match = re.search(regexp, target)
        if match:
            return match.group(1)
        else:
            return ''
