from . import validators
from flask import g, request, url_for
from flask.ext.restful import Resource
from jsonschema import ValidationError
from ptero_common import nicer_logging
from ptero_common.nicer_logging import logged_response
import uuid


LOG = nicer_logging.getLogger(__name__)


class JobListView(Resource):
    @logged_response(logger=LOG)
    def post(self):
        job_id = str(uuid.uuid4())
        return _submit_job(job_id)


class JobView(Resource):
    @logged_response(logger=LOG)
    def get(self, pk):
        result = g.backend.get_job(pk)
        if result is not None:
            return result[1], 200
        else:
            return {'error': 'Job (%s) not found.' % pk}, 404

    @logged_response(logger=LOG)
    def put(self, pk):
        return _submit_job(pk)


def _submit_job(job_id):
    try:
        data = validators.get_job_post_data()
        job_dict = g.backend.create_job(job_id, **data)
        LOG.info("Responding 201 to POST from %s and created job %s",
                request.access_route[0], job_id,
                extra={'jobId': job_id})
        return (job_dict, 201,
                {'Location': url_for('.job', pk=job_id, _external=True)})
    except ValidationError as e:
        LOG.exception("JSON body does not pass validation")
        LOG.info("Responding 400 to POST from %s", request.access_route[0])
        return {'error': e.message}, 400
