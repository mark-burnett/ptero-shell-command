from ptero_common.logging_configuration import configure_web_logging
from ptero_shell_command.api import application
import os

app = application.create_app()
configure_web_logging('SHELL_COMMAND')

if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=os.environ['PTERO_SHELL_COMMAND_PORT'],
            debug=False, use_reloader=False)
