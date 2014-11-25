from .base import BaseAPITest


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

    def test_command_line_too_short(self):
        self.valid_request_data['commandLine'] = []
        self._expect_400(self.valid_request_data)

    def test_command_line_contains_non_strings(self):
        self.valid_request_data['commandLine'] = ['foo', 1, 'bar']
        self._expect_400(self.valid_request_data)

    def test_user_non_string_integer(self):
        self.valid_request_data['user'] = 100
        self._expect_400(self.valid_request_data)

    def test_user_non_string_null(self):
        self.valid_request_data['user'] = None
        self._expect_400(self.valid_request_data)

    def test_user_too_short(self):
        self.valid_request_data['user'] = ''
        self._expect_400(self.valid_request_data)

    def test_working_directory_non_string(self):
        self.valid_request_data['working_directory'] = None
        self._expect_400(self.valid_request_data)

    def test_working_directory_too_short(self):
        self.valid_request_data['working_directory'] = ''
        self._expect_400(self.valid_request_data)

    def test_extra_properties(self):
        self.valid_request_data['unknownExtraProperty'] = 'foo'
        self._expect_400(self.valid_request_data)

    def test_environment_contains_strings_integer(self):
        self.valid_request_data['environment'] = {
            'foo': 7
        }
        self._expect_400(self.valid_request_data)

    def test_environment_contains_strings_null(self):
        self.valid_request_data['environment'] = {
            'foo': None
        }
        self._expect_400(self.valid_request_data)
