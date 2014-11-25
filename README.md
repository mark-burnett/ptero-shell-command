# PTero Shell Command Service
[![Build Status](https://travis-ci.org/genome/ptero-shell-command.svg?branch=master)](https://travis-ci.org/genome/ptero-shell-command)
[![Coverage Status](https://img.shields.io/coveralls/genome/ptero-shell-command.svg)](https://coveralls.io/r/genome/ptero-shell-command?branch=master)
[![Requirements Status](https://requires.io/github/genome/ptero-shell-command/requirements.svg?branch=master)](https://requires.io/github/genome/ptero-shell-command/requirements/?branch=master)

This project provides a way for the PTero workflow system to run shell commands
using [Celery](http://www.celeryproject.org/) via a REST API.

The API is currently described
[here](https://github.com/genome/ptero-apis/blob/master/shell-command.md).


## Testing

To run tests:

    pip install tox
    tox


## Development

To launch a development server:

    pip install -r requirements.txt
    pip install honcho
    honcho start -f Procfile.dev -c worker=4

You can then connect to the webserver at http://localhost:5200
