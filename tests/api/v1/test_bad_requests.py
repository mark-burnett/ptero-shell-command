from .base import BaseAPITest
from ptero_common import statuses
from ptero_common.view_wrapper import NO_SUCH_ENTITY_STATUS_CODE
import uuid


class TestBadRequests(BaseAPITest):
    def setUp(self):
        super(TestBadRequests, self).setUp()

        self.valid_request_data = {
            'commandLine': ['true'],
            'user': self.job_user,
            'workingDirectory': self.job_working_directory,
        }

    def _expect(self, data, status_code):
        post_response = self.post(self.jobs_url, data)
        self.assertEqual(status_code, post_response.status_code)

    def _expect_400(self, data):
        self._expect(data, 400)

    def _fake_job_url(self):
        fake_job_id = str(uuid.uuid4())
        url = '%s/%s' % (self.jobs_url, fake_job_id)
        return url

    def test_empty_body(self):
        self._expect_400({})

    def test_missing_required_parameters(self):
        for param in ['commandLine', 'user', 'workingDirectory']:
            self.valid_request_data.pop(param)
            self._expect_400(self.valid_request_data)

    def test_command_line_too_short(self):
        self.valid_request_data['commandLine'] = []
        self._expect_400(self.valid_request_data)

    def test_command_line_contains_numbers(self):
        self.valid_request_data['commandLine'] = ['foo', 1, 'bar']
        self._expect(self.valid_request_data, 201)

    def test_command_line_contains_non_strings(self):
        self.valid_request_data['commandLine'] = ['foo', True, 'bar']
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

    def test_get_non_existent_job(self):
        response = self.get(self._fake_job_url())
        self.assertEqual(response.status_code, NO_SUCH_ENTITY_STATUS_CODE)

    def test_patch_non_existent_job(self):
        response = self.patch(self._fake_job_url(),
                {"status": statuses.canceled})
        self.assertEqual(response.status_code, NO_SUCH_ENTITY_STATUS_CODE)
