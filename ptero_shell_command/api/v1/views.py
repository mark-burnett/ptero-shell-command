from . import validators
from flask import g, request, url_for
from flask.ext.restful import Resource
from jsonschema import ValidationError
from ptero_common import nicer_logging
from ptero_common.nicer_logging import logged_response


LOG = nicer_logging.getLogger(__name__)


class JobListView(Resource):
    @logged_response(logger=LOG)
    def post(self):
        try:
            data = validators.get_job_post_data()
            job_id = g.backend.create_job(**data)
            LOG.info("Responding 201 to POST from %s and created job %s",
                    request.access_route[0], job_id,
                    extra={'jobId': job_id})
            return ({'jobId': job_id}, 201,
                    {'Location': url_for('job', pk=job_id, _external=True)})
        except ValidationError as e:
            LOG.exception("JSON body does not pass validation")
            LOG.info("Responding 400 to POST from %s", request.access_route[0])
            return {'error': e.message}, 400


class JobView(Resource):
    @logged_response(logger=LOG)
    def get(self, pk):
        status = g.backend.get_job_status(pk)
        if status is not None:
            return {'status': status}
        else:
            return {'message': 'Job not found.'}, 404
