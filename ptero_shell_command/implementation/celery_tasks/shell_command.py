import celery
from ptero_common import nicer_logging
import os
import pwd
import subprocess
from ptero_common import statuses

LOG = nicer_logging.getLogger(__name__)
__all__ = ['ShellCommandTask']


class PreExecFailed(Exception):
    pass


class ShellCommandTask(celery.Task):
    def run(self, command_line, umask, user, working_directory,
            environment=None, stdin=None, webhooks=None):

        if user == 'root':
            self.webhook(statuses.errored, webhooks, status=statuses.errored,
                    jobId=self.request.id,
                    errorMessage='Refusing to execute job as root user')
            return False

        try:
            LOG.debug('command_line: %s', command_line,
                    extra={'jobId': self.request.id})
            p = subprocess.Popen([str(x) for x in command_line],
                env=environment, close_fds=True,
                preexec_fn=lambda: self._setup_execution_environment(
                    umask, user, working_directory),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.webhook(statuses.running, webhooks, status=statuses.running,
                         jobId=self.request.id)

            # XXX We cannot use communicate for real, because communicate
            # buffers the data in memory until the process ends.
            stdout_data, stderr_data = p.communicate(stdin)

            exit_code = p.wait()
            LOG.debug('exit_code: %s', exit_code,
                    extra={'jobId': self.request.id})
            if exit_code == 0:
                status = statuses.succeeded
            else:
                status = statuses.failed
                LOG.debug('stdout: %s', stdout_data,
                    extra={'jobId': self.request.id})
                LOG.debug('stderr: %s', stderr_data,
                    extra={'jobId': self.request.id})

            webhook_data = {
                'status': status,
                'jobId': self.request.id,
                'exitCode': exit_code,
                'stdout': stdout_data,
                'stderr': stderr_data}

            if exit_code == 0:
                self.webhook(statuses.succeeded, webhooks, **webhook_data)
            else:
                self.webhook(statuses.failed, webhooks, **webhook_data)

            self.webhook('ended', webhooks, **webhook_data)
            return exit_code == 0

        except PreExecFailed as e:
            LOG.exception('Exception during pre-exec',
                    extra={'jobId': self.request.id})
            self.webhook(statuses.errored, webhooks, status=statuses.errored,
                         jobId=self.request.id, errorMessage=e.message)
            return False

        except OSError as e:
            if e.errno == 2:
                LOG.exception('Exception: Command not found: %s',
                        command_line[0], extra={'jobId': self.request.id})
                self.webhook(statuses.errored, webhooks,
                        status=statuses.errored, jobId=self.request.id,
                        errorMessage='Command not found: %s' % command_line[0])
            else:
                LOG.exception('Exception: OSError',
                    extra={'jobId': self.request.id})
                self.webhook(statuses.errored, webhooks,
                        status=statuses.errored, jobID=self.request.id,
                        errorMessage=e.message)
            return False

    def webhook(self, webhook_name, webhooks, **kwargs):
        if webhooks is None:
            return

        if webhook_name in webhooks:
            task = self._get_http_task()
            urls = webhooks[webhook_name]
            if not isinstance(urls, list):
                urls = [urls]

            for url in urls:
                LOG.info('Webhook: "%s" for job %s -- %s',
                        webhook_name, self.request.id, url,
                        extra={'jobId': self.request.id})
                task.delay('POST', url, **kwargs)

    def _get_http_task(self):
        return celery.current_app.tasks[
            'ptero_common.celery.http.HTTP'
        ]

    @property
    def user(self):
        return pwd.getpwuid(os.getuid())[0]

    def _setup_execution_environment(self, umask, user, working_directory):
        pw_ent = self._get_pw_ent(user)

        if self.user == 'root':
            self._set_groups(user, pw_ent.pw_gid)
            self._set_gid(pw_ent.pw_gid)
            self._set_uid(pw_ent.pw_uid)
        elif self.user != user:
            raise PreExecFailed("Attempted submit job as invalid user (%s),"
                    " only valid value is (%s)" % (user, self.user))

        self._set_umask(umask)
        self._set_working_directory(working_directory)

    def _set_umask(self, umask):
        if umask is not None:
            try:
                os.umask(umask)
            except TypeError as e:
                raise PreExecFailed('Failed to set umask: ' + e.message)

    def _get_pw_ent(self, user):
        try:
            pw_ent = pwd.getpwnam(user)
        except KeyError as e:
            raise PreExecFailed(e.message)
        return pw_ent

    def _set_groups(self, user, gid):
        try:
            os.initgroups(user, gid)
        except OSError as e:
            raise PreExecFailed('Failed to initgroups: ' + e.strerror)

    def _set_gid(self, gid):
        try:
            os.setregid(gid, gid)
        except OSError as e:
            raise PreExecFailed('Failed to setregid: ' + e.strerror)

    def _set_uid(self, uid):
        try:
            os.setreuid(uid, uid)
        except OSError as e:
            raise PreExecFailed('Failed to setreuid: ' + e.strerror)

    def _set_working_directory(self, working_directory):
        try:
            os.chdir(working_directory)
        except OSError as e:
            raise PreExecFailed(
                'chdir(%s): %s' % (working_directory, e.strerror))
