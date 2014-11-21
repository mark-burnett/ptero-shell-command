from .base import BaseAPITest
import simplejson


class TestBadRequests(BaseAPITest):
    def setUp(self):
        super(TestBadRequests, self).setUp()

        self.valid_request_data = {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
        }

    def _expect_400(self, data):
        post_response = self.post(self.jobs_url, data)
        self.assertEqual(400, post_response.status_code)

    def test_empty_body(self):
        self._expect_400({})

    def test_missing_required_parameters(self):
        for param in ['commandLine', 'user', 'workingDirectory']:
            self.valid_request_data.pop(param)
            self._expect_400(self.valid_request_data)
