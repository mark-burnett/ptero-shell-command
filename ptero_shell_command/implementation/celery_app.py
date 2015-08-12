from celery.signals import setup_logging
from ptero_common.logging_configuration import configure_celery_logging
from ptero_common.celery.app import celery_app
import os


TASK_PATH = 'ptero_shell_command.implementation.celery_tasks'
routes = (
    {
        TASK_PATH + '.shell_command.ShellCommandTask': {'queue': 'fork'},
        'ptero_common.celery.http.HTTP': {'queue': 'http'},
    },
)
broker_url = os.environ.get('PTERO_SHELL_COMMAND_CELERY_BROKER_URL')
app = celery_app(main='PTero-shell-command-celery', task_path=TASK_PATH,
    routes=routes, broker_url=broker_url, track_started=True)


@setup_logging.connect
def setup_celery_logging(**kwargs):
    configure_celery_logging('SHELL_COMMAND')
