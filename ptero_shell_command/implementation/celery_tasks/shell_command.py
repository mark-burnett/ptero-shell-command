import celery
from ptero_common import nicer_logging


LOG = nicer_logging.getLogger(__name__)


__all__ = ['ShellCommandTask']


class PreExecFailed(Exception):
    pass


class ShellCommandTask(celery.Task):
    def run(self, job_id):
        try:
            backend = celery.current_app.factory.create_backend()
            if backend.job_is_canceled(job_id):
                backend.cleanup()
            else:
                backend.run_job(job_id)
        except:
            LOG.exception("Exception while trying to run job (%s)", job_id)
