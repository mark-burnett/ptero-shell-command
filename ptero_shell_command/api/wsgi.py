from ptero_shell_command.api import application
from ptero_common.logging_configuration import configure_logging
import argparse

app = application.create_app()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--debug', action='store_true', default=False)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    configure_logging(level_env_var='PTERO_SHELL_COMMAND_LOG_LEVEL',
            time_env_var='PTERO_SHELL_COMMAND_LOG_TIME')
    app.run(host=args.host, port=args.port, debug=args.debug)
