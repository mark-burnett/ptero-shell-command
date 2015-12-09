from . import validators
from flask import g, request, url_for
from flask.ext.restful import Resource
from jsonschema import ValidationError
from ptero_common import nicer_logging
from ptero_common.nicer_logging import logged_response
from ptero_shell_command.exceptions import JobNotFoundError
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
        try:
            body = g.backend.get_job(pk)
            return body, 200
        except JobNotFoundError as e:
            return {"error": e.message}, 404

    @logged_response(logger=LOG)
    def put(self, pk):
        return _submit_job(pk)

    @logged_response(logger=LOG)
    def patch(self, pk):
        LOG.info("Handling PATCH request to %s from %s for job (%s)",
                request.url, request.access_route[0], pk,
                extra={'jobId': pk})

        data = request.json
        patch_keys = set(data.keys())
        allowed_keys = set(['status'])

        disallowed_keys = patch_keys - allowed_keys
        if disallowed_keys:
            return {"error": "Not allowing PATCH of %s" %
                    str(list(disallowed_keys))}, 400

        try:
            job_data = g.backend.update_job(pk, **data)
            return job_data, 200
        except JobNotFoundError as e:
            return {"error": e.message}, 404
        except:
            LOG.exception("Exception while updating job (%s)", pk,
                    extra={'jobId': pk})
            return {"error": "Could not update job"}, 400


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


class ServerInfo(Resource):
    @logged_response(logger=LOG)
    def get(self):
        return g.backend.server_info(), 200
