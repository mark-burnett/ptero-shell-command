web: gunicorn ptero_shell_command.api.wsgi:app --access-logfile - --error-logfile -
worker: celery worker -A ptero_shell_command.implementation.celery_app -Q fork
http_worker: celery worker -A ptero_shell_command.implementation.celery_app -Q http
