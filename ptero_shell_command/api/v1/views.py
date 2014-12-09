from . import validators
from flask import g, request, url_for
from flask.ext.restful import Resource, marshal
from jsonschema import ValidationError
from ptero_shell_command import exceptions


class JobListView(Resource):
    def post(self):
        try:
            data = validators.get_job_post_data()
            job_id = g.backend.create_job(**data)
            return {'jobId': job_id}, 201, {'Location': url_for('job',
                pk=job_id)}
        except ValidationError as e:
            return {'error': e.message}, 400


class JobView(Resource):
    def get(self, pk):
        status = g.backend.get_job_status(pk)
        if status is not None:
            return {'status': status}
        else:
            return {'message': 'Job not found.'}, 404
