# -*- coding: utf-8 -*-

__all__ = [
    'route', 'run', 'static_file', 'error','get', 'post', 'put', 'delete', 'Mole',
    'request', 'response',
    'abort', 'redirect',
    'DEBUG', 'HTTP_CODES',
    '__version__',
]

from mole import route, run, static_file, error,get, post, put, delete, Mole
from mole import request, response
from mole import abort, redirect
from mole import DEBUG, HTTP_CODES

__version__ = "1.0.1"