import celery
from ptero_common import nicer_logging
from ptero_shell_command.exceptions import RetryJobError


LOG = nicer_logging.getLogger(__name__)


__all__ = ['ShellCommandTask']


class PreExecFailed(Exception):
    pass


class ShellCommandTask(celery.Task):
    ignore_result = True
    max_retries = None

    def run(self, job_id):
        try:
            backend = celery.current_app.factory.create_backend()
            if backend.job_is_canceled(job_id):
                backend.cleanup()
            else:
                try:
                    backend.run_job(job_id, attempt_number=self.request.retries)
                except RetryJobError:
                    delay = backend.get_retry_delay(job_id,
                            attempt_number=self.request.retries)
                    LOG.info("Scheduling retry for job (%s) in (%s) seconds",
                            job_id, delay, extra={'jobId': job_id})
                    self.retry(throw=False, countdown=delay)
        except:
            LOG.exception("Exception while trying to run job (%s)", job_id)
        finally:
            backend.cleanup()
