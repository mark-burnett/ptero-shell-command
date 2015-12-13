import unittest
from ptero_shell_command.implementation.models import Job


class TestJobRetry(unittest.TestCase):
    def test_delay(self):
        job = Job(retry_settings={
            'exitCode': 4,
            'initialInterval': 1,
            'maxInterval': 12,
            'attempts': 10,
            }
        )

        expected_delays = [1, 2, 4, 8, 12, 12, 12, 12, 12, 12]
        delays = [job.retry_delay(i) for i in xrange(10)]

        self.assertEqual(expected_delays, delays)

    def test_should_retry(self):
        job = Job(retry_settings={
            'exitCode': 4,
            'initialInterval': 1,
            'maxInterval': 12,
            'attempts': 10,
            }
        )

        self.assertFalse(job.should_retry(exit_code=1, attempt_number=1))
        self.assertFalse(job.should_retry(exit_code=4, attempt_number=10))

        self.assertTrue(job.should_retry(exit_code=4, attempt_number=0))
        self.assertTrue(job.should_retry(exit_code=4, attempt_number=9))

    def test_should_retry_if_unspecified(self):
        job = Job()

        self.assertFalse(job.should_retry(exit_code=1, attempt_number=1))
