from flask.ext.restful import Api
from flask.ext.restful.representations import json as flask_json
from . import views

__all__ = ['api']

api = Api(default_mediatype='application/json')
flask_json.settings['indent'] = 4
flask_json.settings['sort_keys'] = True

api.add_resource(views.JobListView, '/jobs', endpoint='job-list')
api.add_resource(views.JobView, '/jobs/<string:pk>', endpoint='job')
