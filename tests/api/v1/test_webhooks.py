from .base import BaseAPITest
from ptero_common import statuses


class TestWebhooks(BaseAPITest):
    def test_begun_webhook(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.running: webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.running)

    def test_ended_webhook_success(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.succeeded)

    def test_ended_webhook_failure(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['false'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['exitCode'], '1')
        self.assertEqual(webhook_data[0]['status'], statuses.failed)

    def test_success_and_failure_webhooks_on_success(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.succeeded: webhook_target.url,
                statuses.failed: webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.succeeded)

    def test_success_and_failure_webhooks_on_failure(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['false'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.succeeded: webhook_target.url,
                statuses.failed: webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['exitCode'], '1')
        self.assertEqual(webhook_data[0]['status'], statuses.failed)

    def test_multiple_webhooks(self):
        webhook_target = self.create_webhook_server([200, 200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.running: webhook_target.url,
                'ended': webhook_target.url,
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.running)
        self.assertEqual(webhook_data[1]['status'], statuses.succeeded)

    def test_list_of_webhooks(self):
        webhook_target = self.create_webhook_server([200, 200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                statuses.running: [webhook_target.url, webhook_target.url]
            },
        })
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(webhook_data[0]['status'], statuses.running)
        self.assertEqual(webhook_data[1]['status'], statuses.running)

    def test_environment_set_for_job(self):
        webhook_target = self.create_webhook_server([200])
        environment = {
            'FOO': 'bar',
        }

        post_data = {
            'commandLine': ['/usr/bin/env'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'environment': environment,
            'webhooks': {
                'ended': webhook_target.url,
            },
        }

        post_response = self.post(self.jobs_url, post_data)
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()

        stdout = webhook_data[0]['stdout']
        actual_environment = _extract_environment_dict(stdout)

        self.assertEqual(environment, actual_environment)

    def test_stdin_stdout_pass_through(self):
        webhook_target = self.create_webhook_server([200])
        stdin = 'this is just some text'

        post_data = {
            'commandLine': ['cat'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'stdin': stdin,
            'webhooks': {
                'ended': webhook_target.url,
            },
        }

        post_response = self.post(self.jobs_url, post_data)
        print "job_id: %s" % post_response.DATA['jobId']

        webhook_data = webhook_target.stop()
        self.assertEqual(stdin, webhook_data[0]['stdout'])

    def test_command_not_found(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['bad-command'],
            'user': self.job_user,
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
            'message'].startswith('Command not found'))


def _extract_environment_dict(stdin):
    result = {}
    for line in stdin.split('\n'):
        if line:
            key, value = line.split('=')
            result[key] = value.strip('\n')
    return result
