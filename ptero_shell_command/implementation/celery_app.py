from celery.signals import worker_init, setup_logging
from .factory import Factory
from ptero_common.logging_configuration import configure_celery_logging
from ptero_common.celery.utils import get_celery_config
import celery
import os


TASK_PATH = 'ptero_shell_command.implementation.celery_tasks'


app = celery.Celery('PTero-shell-command-celery', include=TASK_PATH)


app.conf['CELERY_ROUTES'] = (
    {
        TASK_PATH + '.shell_command.ShellCommandTask': {'queue': 'fork'},
        'ptero_common.celery.http.HTTP': {'queue': 'http'},
    },
)

config = get_celery_config('SHELL_COMMAND')
app.conf.update(config)


@setup_logging.connect
def setup_celery_logging(**kwargs):
    configure_celery_logging('SHELL_COMMAND')


@worker_init.connect
def initialize_sqlalchemy_session(signal, sender):
    app.factory = Factory(
            database_url=os.environ['PTERO_SHELL_COMMAND_DB_STRING'],
            celery_app=app)
