from . import celery_tasks  # noqa
from . import models
from .models.job import PreExecFailed
from ptero_common import nicer_logging, statuses
from ptero_common.server_info import get_server_info
from ptero_shell_command.exceptions import JobNotFoundError, RetryJobError
import os
import subprocess
import time


LOG = nicer_logging.getLogger(__name__)

CHILD_POLLING_INTERVAL = float(os.environ[
        'PTERO_SHELL_COMMAND_CHILD_POLLING_INTERVAL'])
DB_POLLING_INTERVAL = float(os.environ[
        'PTERO_SHELL_COMMAND_DB_POLLING_INTERVAL'])
KILL_INTERVAL = float(os.environ['PTERO_SHELL_COMMAND_KILL_INTERVAL'])

NUM_POLLS_DB = int(DB_POLLING_INTERVAL / CHILD_POLLING_INTERVAL)
NUM_POLLS_KILL = int(KILL_INTERVAL / CHILD_POLLING_INTERVAL)


class Backend(object):
    def __init__(self, session, celery_app, db_revision):
        self.session = session
        self.celery_app = celery_app
        self.db_revision = db_revision

    def cleanup(self):
        self.session.rollback()

    @property
    def shell_command(self):
        return self.celery_app.tasks[
            'ptero_shell_command.implementation.celery_tasks.shell_command.'
            'ShellCommandTask'
        ]

    def create_job(self, job_id, command_line, user, working_directory,
            **kwargs):

        if 'umask' in kwargs:
            kwargs['umask'] = int(kwargs['umask'], 8)

        job = models.Job(id=job_id, command_line=command_line, user=user,
                working_directory=working_directory, **kwargs)
        self.session.add(job)

        LOG.debug("Commiting job (%s) to DB", job.id,
                extra={'jobId': job.id})
        self.session.commit()
        LOG.debug("Job (%s) committed to DB", job.id,
                extra={'jobId': job.id})

        LOG.info("Submitting Celery ShellCommandTask for job (%s)",
                job.id, extra={'jobId': job.id})
        self.shell_command.delay(job.id)

        return job.as_dict

    def run_job(self, job_id, attempt_number):
        job = self._get_job(job_id)

        if job.user == 'root':
            self._set_job_status(job, statuses.errored,
                    message="Refusing to execute job as root user")
            self.session.commit()
            return

        LOG.debug('command_line: %s', job.command_line,
                extra={'jobId': job.id})
        try:

            job.stdout, job.stderr, job.exit_code = self._launch_process(job)

            LOG.debug('exit_code: %s', job.exit_code, extra={'jobId': job.id})
            if job.should_retry(job.exit_code, attempt_number):
                exit_code = job.exit_code
                self.session.rollback()
                raise RetryJobError("Job (%s) should be retried after "
                    "exiting (%s) on attempt number (%s)" % (job.id, exit_code,
                        attempt_number))

            if job.exit_code == 0:
                self._set_job_status(job, statuses.succeeded)
            else:
                self._set_job_status(job, statuses.failed)
                LOG.debug('stdout: %s', job.stdout,
                    extra={'jobId': job.id})
                LOG.debug('stderr: %s', job.stderr,
                    extra={'jobId': job.id})

        except PreExecFailed as e:
            LOG.exception('Exception during pre-exec',
                    extra={'jobId': job.id})
            self._set_job_status(job, statuses.errored, message=str(e))

        except OSError as e:
            if e.errno == 2:
                LOG.exception('Exception: Command not found: %s',
                        job.command_line[0], extra={'jobId': job.id})
                self._set_job_status(job, statuses.errored,
                        message='Command not found: %s' % job.command_line[0])
            else:
                LOG.exception('Exception: OSError',
                    extra={'jobId': job.id})
                self._set_job_status(job, statuses.errored, message=str(e))

        self.session.commit()

    def _launch_process(self, job):
        if job.stdin is not None:
            pipe_read, pipe_write = os.pipe()
            os.write(pipe_write, job.stdin)
            os.close(pipe_write)
            stdin = pipe_read
        else:
            stdin = None

        p = subprocess.Popen([str(x) for x in job.command_line],
            env=job.environment, close_fds=True,
            preexec_fn=job._setup_execution_environment,
            stdin=stdin,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self._set_job_status(job, statuses.running)
        self.session.commit()

        job_exit_code = self._wait_for_process(p, job.id)
        job_stdout, job_stderr = p.communicate()
        if stdin is not None:
            os.close(stdin)

        return job_stdout, job_stderr, job_exit_code

    def _wait_for_process(self, process, job_id):
        while process.poll() is None:
            LOG.debug('Polling to find out if job (%s) is canceled',
                    job_id, extra={'jobId': job_id})
            if self.job_is_canceled_and_rollback(job_id):
                LOG.info("Found job (%s) was canceled while running: "
                        "terminating child process",
                        job_id, extra={'jobId': job_id})
                self._kill_process(process, job_id)
            else:
                self._busy_wait(process, num_polls=NUM_POLLS_DB)

        return process.poll()

    def _busy_wait(self, process, num_polls):
        for i in xrange(num_polls):
            if process.poll() is not None:
                return
            else:
                time.sleep(CHILD_POLLING_INTERVAL)
        return

    def _kill_process(self, process, job_id):
        process.terminate()
        self._busy_wait(process, num_polls=NUM_POLLS_KILL)
        if process.poll() is None:
            LOG.info("Stubborn job (%s) wouldn't go down... KILLing", job_id,
                    extra={'jobId': job_id})
            process.kill()
            process.wait()

    def _set_job_status(self, job, status, message=None):
        job.set_status(status, message=message)
        self.session.commit()
        job.trigger_webhooks()

    def _get_job(self, job_id):
        job = self.session.query(models.Job).get(job_id)
        if job is not None:
            return job
        else:
            raise JobNotFoundError("No job with id (%s) was found" % job_id)

    def get_job(self, job_id):
        job = self._get_job(job_id)
        return job.as_dict

    def server_info(self):
        result = get_server_info(
                'ptero_shell_command.implementation.celery_app')
        result['databaseRevision'] = self.db_revision
        return result

    def update_job(self, job_id, status=None):
        job = self._get_job(job_id)
        if status is not None:
            self._set_job_status(job, status,
                    message="Status set by PATCH request")
            return job.as_dict

    def job_is_canceled_and_rollback(self, job_id):
        result = self.job_is_canceled(job_id)
        self.session.rollback()
        return result

    def job_is_canceled(self, job_id):
        return self.session.query(models.JobStatusHistory).filter(
                models.JobStatusHistory.job_id == job_id).filter(
                models.JobStatusHistory.status == statuses.canceled).count() > 0

    def get_retry_delay(self, job_id, attempt_number):
        job = self._get_job(job_id)
        return job.retry_delay(attempt_number)
