# -*- coding: utf-8 -*-
    
    
import const
from response import HeaderDict
    
class MoleException(Exception):
    """ A base class for exceptions used by Mole. """
    pass

class HTTPResponse(MoleException):
    """ Used to break execution and immediately finish the response """
    def __init__(self, output='', status=200, header=None):
        super(MoleException, self).__init__("HTTP Response %d" % status)
        self.status = int(status)
        self.output = output
        self.headers = HeaderDict(header) if header else None

    def apply(self, response):
        if self.headers:
            for key, value in self.headers.iterallitems():
                response.headers[key] = value
        response.status = self.status
        
class HTTPError(HTTPResponse):
    """ Used to generate an error page """
    def __init__(self, code=500, output='Unknown Error', exception=None, traceback=None, header=None):
        super(HTTPError, self).__init__(output, code, header)
        self.exception = exception
        self.traceback = traceback

    def __repr__(self):
        from template import template
        return template(const.ERROR_PAGE_TEMPLATE, e=self)
    