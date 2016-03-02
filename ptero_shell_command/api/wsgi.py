from ptero_common.logging_configuration import configure_web_logging
from ptero_shell_command.api import application
import os

app = application.create_app()
configure_web_logging('SHELL_COMMAND')


def handle_sigterm(signum, frame):
    import sys
    sys.stderr.write('Handling SIGTERM... shutting down the Flask Server')
    shutdown_server()


def shutdown_server():
    raise RuntimeError('Forcefully shutting down the Flask Server')


if __name__ == '__main__':
    import signal
    signal.signal(signal.SIGTERM, handle_sigterm)

    app.run(host='0.0.0.0',
            port=os.environ['PTERO_SHELL_COMMAND_PORT'],
            debug=False, use_reloader=False)
