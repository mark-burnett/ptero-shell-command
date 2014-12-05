from flask import request
import json
import jsonschema
import os
import pkg_resources


def _load_schema(schema_name):
    return json.load(pkg_resources.resource_stream('ptero_shell_command',
        _schema_path(schema_name)))


def _schema_path(schema_name):
    return os.path.join('schemas', 'v1', '%s.json' % schema_name)


_POST_JOB_SCHEMA = _load_schema('post_job')
_POST_JOB_KEYS_RENAME = {
    'commandLine': 'command_line',
    'callbacks': 'webhooks',
    'workingDirectory': 'working_directory',
}
def get_job_post_data():
    data = request.json
    jsonschema.validate(data, _POST_JOB_SCHEMA)
    for old, new in _POST_JOB_KEYS_RENAME.iteritems():
        if old in data:
            data[new] = data.pop(old)
    return data
