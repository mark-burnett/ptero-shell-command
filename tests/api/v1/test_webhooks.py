from .base import BaseAPITest


class TestWebhooks(BaseAPITest):
    def test_begun_callback(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'callbacks': {
                'begun': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'begun',
                'jobId': post_response.DATA['jobId'],
            },
        ]
        self.assertEqual(expected_data, webhook_data)

    def test_begun_webhook(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'begun': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'begun',
                'jobId': post_response.DATA['jobId'],
            },
        ]
        self.assertEqual(expected_data, webhook_data)

    def test_succeeded_webhook(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'ended',
                'exitCode': 0,
                'stdout': '',
                'stderr': '',
                'jobId': post_response.DATA['jobId'],
            },
        ]
        self.assertEqual(expected_data, webhook_data)

    def test_failed_webhook(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['false'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'ended',
                'exitCode': 1,
                'stdout': '',
                'stderr': '',
                'jobId': post_response.DATA['jobId'],
            },
        ]
        self.assertEqual(expected_data, webhook_data)

    def test_multiple_webhooks(self):
        webhook_target = self.create_webhook_server([200, 200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'begun': webhook_target.url,
                'ended': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'begun',
                'jobId': post_response.DATA['jobId'],
            },
            {
                'status': 'ended',
                'exitCode': 0,
                'stdout': '',
                'stderr': '',
                'jobId': post_response.DATA['jobId'],
            },
        ]
        self.assertEqual(expected_data, webhook_data)

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

        self.post(self.jobs_url, post_data)

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

        self.post(self.jobs_url, post_data)

        webhook_data = webhook_target.stop()
        self.assertEqual(stdin, webhook_data[0]['stdout'])

    def test_command_not_found(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['bad-command'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'error': webhook_target.url,
            },
        })

        webhook_data = webhook_target.stop()
        expected_data = [
            {
                'status': 'error',
                'errorMessage': 'Command not found: bad-command',
                'jobId': post_response.DATA['jobId'],
            },
        ]
        self.assertEqual(expected_data, webhook_data)


def _extract_environment_dict(stdin):
    result = {}
    for line in stdin.split('\n'):
        if line:
            key, value = line.split('=')
            result[key] = value.strip('\n')
    return result
