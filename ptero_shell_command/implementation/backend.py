from . import celery_tasks  # noqa
from . import models
from .models.job import PreExecFailed
from ptero_common import nicer_logging, statuses
from ptero_common.server_info import get_server_info
from ptero_shell_command.exceptions import JobNotFoundError
import subprocess


LOG = nicer_logging.getLogger(__name__)


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

    def run_job(self, job_id):
        job = self._get_job(job_id)

        if job.user == 'root':
            self._set_job_status(job, statuses.errored,
                    message="Refusing to execute job as root user")
            self.session.commit()
            return

        try:
            LOG.debug('command_line: %s', job.command_line,
                    extra={'jobId': job.id})
            job_stdin = job.stdin
            p = subprocess.Popen([str(x) for x in job.command_line],
                env=job.environment, close_fds=True,
                preexec_fn=job._setup_execution_environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self._set_job_status(job, statuses.running)
            self.session.commit()

            # XXX We cannot use communicate for real, because communicate
            # buffers the data in memory until the process ends.
            job_stdout, job_stderr = p.communicate(job_stdin)
            job_exit_code = p.wait()

            (job.stdout, job.stderr, job.exit_code) = (
                job_stdout, job_stderr, job_exit_code)

            LOG.debug('exit_code: %s', job.exit_code,
                    extra={'jobId': job.id})
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
            self._set_job_status(job, statuses.errored, message=e.message)

        except OSError as e:
            if e.errno == 2:
                LOG.exception('Exception: Command not found: %s',
                        job.command_line[0], extra={'jobId': job.id})
                self._set_job_status(job, statuses.errored,
                        message='Command not found: %s' % job.command_line[0])
            else:
                LOG.exception('Exception: OSError',
                    extra={'jobId': job.id})
                self._set_job_status(job, statuses.errored, message=e.message)

        self.session.commit()

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
