from ptero_shell_command.api import application
import logging
import os

app = application.create_app()

if __name__ == '__main__':
    logging.basicConfig(
            level=os.environ['PTERO_SHELL_COMMAND_LOG_LEVEL'].upper())
    app.run(host=os.environ['PTERO_SHELL_COMMAND_HOST'],
            port=os.environ['PTERO_SHELL_COMMAND_PORT'],
            debug=False, use_reloader=False)
