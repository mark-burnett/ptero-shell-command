web: gunicorn ptero_shell_command.api.wsgi:app --access-logfile - --error-logfile -
fork_worker: celery worker --loglevel=INFO -A ptero_shell_command.implementation.celery_app -Q fork
http_worker: celery worker --loglevel=INFO -A ptero_shell_command.implementation.celery_app -Q http
