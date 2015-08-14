from celery.signals import setup_logging
from ptero_common.logging_configuration import configure_celery_logging
from ptero_common.celery.utils import get_config_from_env
import celery


TASK_PATH = 'ptero_shell_command.implementation.celery_tasks'


app = celery.Celery('PTero-shell-command-celery', include=TASK_PATH)


app.conf['CELERY_ROUTES'] = (
    {
        TASK_PATH + '.shell_command.ShellCommandTask': {'queue': 'fork'},
        'ptero_common.celery.http.HTTP': {'queue': 'http'},
    },
)

config = get_config_from_env('SHELL_COMMAND')
app.conf.update(config)


@setup_logging.connect
def setup_celery_logging(**kwargs):
    configure_celery_logging('SHELL_COMMAND')
