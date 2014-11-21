from .base import BaseAPITest
import simplejson


class TestBadRequests(BaseAPITest):
    def test_empty_body(self):
        post_response = self.post(self.jobs_url, {})
        self.assertEqual(400, post_response.status_code)
