from .base import BaseAPITest


class TestUmask(BaseAPITest):
    def test_umask_0000_set_for_job(self):
        _test_umask_set_for_job(self, 0000)

    def test_umask_0777_set_for_job(self):
        _test_umask_set_for_job(self, 0777)

def _test_umask_set_for_job(self, umask):
    webhook_target = self.create_webhook_server([200])

    post_data = {
        'commandLine': ['/bin/bash', '-c', 'umask'],
        'user': self.job_user,
        'workingDirectory': self.job_working_directory,
        'umask': umask,
        'webhooks': {
            'ended': webhook_target.url,
        },
    }

    self.post(self.jobs_url, post_data)

    webhook_data = webhook_target.stop()
    actual_umask = webhook_data[0]['stdout'].strip('\n')
    self.assertEqual(oct(umask).zfill(4), actual_umask)
