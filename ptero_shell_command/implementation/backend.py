from . import celery_tasks
import logging

LOG = logging.getLogger(__name__)


class Backend(object):
    def __init__(self, celery_app):
        self.celery_app = celery_app

    def cleanup(self):
        pass

    @property
    def shell_command(self):
        return self.celery_app.tasks[
'ptero_shell_command.implementation.celery_tasks.shell_command.ShellCommandTask'
        ]

    def create_job(self, command_line, environment={}, stdin=None,
            callbacks=None):
        task = self.shell_command.delay(command_line, environment=environment,
                stdin=stdin, callbacks=callbacks)
        LOG.debug("Task (%s) command_line: '%s'", task.id, command_line)
        LOG.debug("Task (%s) stdin: '%s'", task.id, stdin)

        return task.id

    def get_job_status(self, job_id):
        task = self.shell_command.AsyncResult(job_id)

        return _job_status_from_task(task)

def _job_status_from_task(task):
    if task is None:
        return None

    state = task.state
    if state == 'SUCCESS':
        result = task.result
        if result.get('exit_code') == 0:
            return 'succeeded'
        else:
            return 'failed'

    elif state == 'STARTED':
        return 'running'

    elif state == 'PENDING':
        return 'pending'
