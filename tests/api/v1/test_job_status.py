from .base import BaseAPITest


class TestJobStatus(BaseAPITest):
    def test_successful_job_has_succeeded_status(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })

        webhook_target.stop()

        get_response = self.get(post_response.headers['Location'])
        self.assertEqual('succeeded', get_response.DATA['status'])

    def test_failed_job_has_failed_status(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['false'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'ended': webhook_target.url,
            },
        })

        webhook_target.stop()

        get_response = self.get(post_response.headers['Location'])
        self.assertEqual('failed', get_response.DATA['status'])

    def test_running_job_has_running_status(self):
        webhook_target = self.create_webhook_server([200])

        post_response = self.post(self.jobs_url, {
            'commandLine': ['sleep', '10'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
            'webhooks': {
                'begun': webhook_target.url,
            },
        })

        webhook_target.stop()

        get_response = self.get(post_response.headers['Location'])
        self.assertEqual('running', get_response.DATA['status'])
