# -*- coding: utf-8 -*-
"""
Request

Request class for wsgi
"""
import sys
import cgi
import threading
import base64
import tempfile
from urlparse import urlunsplit
from urllib import quote as urlquote
try: from collections import MutableMapping as DictMixin
except ImportError: # pragma: no cover
    from UserDict import DictMixin
    
try: from urlparse import parse_qs
except ImportError: # pragma: no cover
    from cgi import parse_qs
from StringIO import StringIO as BytesIO
from tempfile import TemporaryFile
from Cookie import SimpleCookie

if sys.version_info >= (3,0,0): # pragma: no cover
    # See Request.POST
    from io import TextIOWrapper
    class NCTextIOWrapper(TextIOWrapper):
        ''' Garbage collecting an io.TextIOWrapper(buffer) instance closes the
            wrapped buffer. This subclass keeps it open. '''
        def close(self): pass
else:
    NCTextIOWrapper = None
    
import utils
from cookie import cookie_decode
from structs import DictProperty,MultiDict
import const

def parse_auth(header):
    """ Parse rfc2617 HTTP authentication header string (basic) and return (user,pass) tuple or None"""
    try:
        method, data = header.split(None, 1)
        if method.lower() == 'basic':
            name, pwd = base64.b64decode(data).split(':', 1)
            return name, pwd
    except (KeyError, ValueError, TypeError):
        return None
    
class WSGIHeaderDict(DictMixin):
    ''' This dict-like class wraps a WSGI environ dict and provides convenient
        access to HTTP_* fields. Keys and values are native strings
        (2.x bytes or 3.x unicode) and keys are case-insensitive. If the WSGI
        environment contains non-native string values, these are de- or encoded
        using a lossless 'latin1' character set.

        The API will remain stable even on changes to the relevant PEPs.
        Currently PEP 333, 444 and 3333 are supported. (PEP 444 is the only one
        that uses non-native strings.)
     '''

    def __init__(self, environ):
        self.environ = environ

    def _ekey(self, key): # Translate header field name to environ key.
        return 'HTTP_' + key.replace('-','_').upper()

    def raw(self, key, default=None):
        ''' Return the header value as is (may be bytes or unicode). '''
        return self.environ.get(self._ekey(key), default)

    def __getitem__(self, key):
        return utils.tonat(self.environ[self._ekey(key)], 'latin1')

    def __setitem__(self, key, value):
        raise TypeError("%s is read-only." % self.__class__)

    def __delitem__(self, key):
        raise TypeError("%s is read-only." % self.__class__)

    def __iter__(self):
        for key in self.environ:
            if key[:5] == 'HTTP_':
                yield key[5:].replace('_', '-').title()

    def keys(self): return list(self)
    def __len__(self): return len(list(self))
    def __contains__(self, key): return self._ekey(key) in self.environ
    
class Request(threading.local, DictMixin):
    """ Represents a single HTTP request using thread-local attributes.
        The Request object wraps a WSGI environment and can be used as such.
    """
    def __init__(self, environ=None):
        """ Create a new Request instance.
        
            You usually don't do this but use the global `mole.request`
            instance instead.
        """
        self.bind(environ or {},)

    def bind(self, environ):
        """ Bind a new WSGI environment.
            
            This is done automatically for the global `mole.request`
            instance on every request.
        """
        self.environ = environ
        # These attributes are used anyway, so it is ok to compute them here
        self.path = '/' + environ.get('PATH_INFO', '/').lstrip('/')
        self.method = environ.get('REQUEST_METHOD', 'GET').upper()

    @property
    def _environ(self):
        utils.depr("Request._environ renamed to Request.environ")
        return self.environ

    def copy(self):
        ''' Returns a copy of self '''
        return Request(self.environ.copy())

    def path_shift(self, shift=1):
        ''' Shift path fragments from PATH_INFO to SCRIPT_NAME and vice versa.

           :param shift: The number of path fragments to shift. May be negative
                         to change the shift direction. (default: 1)
        '''
        script_name = self.environ.get('SCRIPT_NAME','/')
        self['SCRIPT_NAME'], self.path = path_shift(script_name, self.path, shift)
        self['PATH_INFO'] = self.path

    def __getitem__(self, key): return self.environ[key]
    def __delitem__(self, key): self[key] = ""; del(self.environ[key])
    def __iter__(self): return iter(self.environ)
    def __len__(self): return len(self.environ)
    def keys(self): return self.environ.keys()
    def __setitem__(self, key, value):
        """ Shortcut for Request.environ.__setitem__ """
        self.environ[key] = value
        todelete = []
        if key in ('PATH_INFO','REQUEST_METHOD'):
            self.bind(self.environ)
        elif key == 'wsgi.input': todelete = ('body','forms','files','params')
        elif key == 'QUERY_STRING': todelete = ('get','params')
        elif key.startswith('HTTP_'): todelete = ('headers', 'cookies')
        for key in todelete:
            if 'mole.' + key in self.environ:
                del self.environ['mole.' + key]

    @property
    def query_string(self):
        """ The part of the URL following the '?'. """
        return self.environ.get('QUERY_STRING', '')

    @property
    def fullpath(self):
        """ Request path including SCRIPT_NAME (if present). """
        return self.environ.get('SCRIPT_NAME', '').rstrip('/') + self.path

    @property
    def url(self):
        """ Full URL as requested by the client (computed).

            This value is constructed out of different environment variables
            and includes scheme, host, port, scriptname, path and query string. 
        """
        scheme = self.environ.get('wsgi.url_scheme', 'http')
        host   = self.environ.get('HTTP_X_FORWARDED_HOST')
        host   = host or self.environ.get('HTTP_HOST', None)
        if not host:
            host = self.environ.get('SERVER_NAME')
            port = self.environ.get('SERVER_PORT', '80')
            if (scheme, port) not in (('https','443'), ('http','80')):
                host += ':' + port
        parts = (scheme, host, urlquote(self.fullpath), self.query_string, '')
        return urlunsplit(parts)

    @property
    def content_length(self):
        """ Content-Length header as an integer, -1 if not specified """
        return int(self.environ.get('CONTENT_LENGTH', '') or -1)

    @property
    def header(self):
        utils.depr("The Request.header property was renamed to Request.headers")
        return self.headers

    @DictProperty('environ', 'mole.headers', read_only=True)
    def headers(self):
        ''' Request HTTP Headers stored in a :cls:`HeaderDict`. '''
        return WSGIHeaderDict(self.environ)

    @DictProperty('environ', 'mole.get', read_only=True)
    def GET(self):
        """ The QUERY_STRING parsed into an instance of :class:`MultiDict`. """
        data = parse_qs(self.query_string, keep_blank_values=True)
        get = self.environ['mole.get'] = MultiDict()
        for key, values in data.iteritems():
            for value in values:
                get[key] = value
        return get

    @DictProperty('environ', 'mole.post', read_only=True)
    def POST(self):
        """ The combined values from :attr:`forms` and :attr:`files`. Values are
            either strings (form values) or instances of
            :class:`cgi.FieldStorage` (file uploads).
        """
        post = MultiDict()
        safe_env = {'QUERY_STRING':''} # Build a safe environment for cgi
        for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
            if key in self.environ: safe_env[key] = self.environ[key]
        if NCTextIOWrapper:
            fb = NCTextIOWrapper(self.body, encoding='ISO-8859-1', newline='\n')
        else:
            fb = self.body
        data = cgi.FieldStorage(fp=fb, environ=safe_env, keep_blank_values=True)
        for item in data.list or []:
            post[item.name] = item if item.filename else item.value
        return post

    @DictProperty('environ', 'mole.forms', read_only=True)
    def forms(self):
        """ POST form values parsed into an instance of :class:`MultiDict`.

            This property contains form values parsed from an `url-encoded`
            or `multipart/form-data` encoded POST request bidy. The values are
            native strings.
        """
        forms = MultiDict()
        for name, item in self.POST.iterallitems():
            if not hasattr(item, 'filename'):
                forms[name] = item
        return forms

    @DictProperty('environ', 'mole.files', read_only=True)
    def files(self):
        """ File uploads parsed into an instance of :class:`MultiDict`.

            This property contains file uploads parsed from an
            `multipart/form-data` encoded POST request body. The values are
            instances of :class:`cgi.FieldStorage`.
        """
        files = MultiDict()
        for name, item in self.POST.iterallitems():
            if hasattr(item, 'filename'):
                files[name] = item
        return files
        
    @DictProperty('environ', 'mole.params', read_only=True)
    def params(self):
        """ A combined :class:`MultiDict` with values from :attr:`forms` and
            :attr:`GET`. File-uploads are not included. """
        params = MultiDict(self.GET)
        for key, value in self.forms.iterallitems():
            params[key] = value
        return params

    @DictProperty('environ', 'mole.body', read_only=True)
    def _body(self):
        """ The HTTP request body as a seekable file-like object.

            This property returns a copy of the `wsgi.input` stream and should
            be used instead of `environ['wsgi.input']`.
         """
        maxread = max(0, self.content_length)
        stream = self.environ['wsgi.input']
        body = BytesIO() if maxread < const.MEMFILE_MAX else TemporaryFile(mode='w+b')
        while maxread > 0:
            part = stream.read(min(maxread, const.MEMFILE_MAX))
            if not part: break
            body.write(part)
            maxread -= len(part)
        self.environ['wsgi.input'] = body
        body.seek(0)
        return body
    
    @property
    def body(self):
        self._body.seek(0)
        return self._body

    @property
    def auth(self): #TODO: Tests and docs. Add support for digest. namedtuple?
        """ HTTP authorization data as a (user, passwd) tuple. (experimental)

            This implementation currently only supports basic auth and returns
            None on errors.
        """
        return parse_auth(self.headers.get('Authorization',''))

    @DictProperty('environ', 'mole.cookies', read_only=True)
    def COOKIES(self):
        """ Cookies parsed into a dictionary. Secure cookies are NOT decoded
            automatically. See :meth:`get_cookie` for details.
        """
        raw_dict = SimpleCookie(self.headers.get('Cookie',''))
        cookies = {}
        for cookie in raw_dict.itervalues():
            cookies[cookie.key] = cookie.value
        return cookies

    def get_cookie(self, key, secret=None):
        """ Return the content of a cookie. To read a `Secure Cookies`, use the
            same `secret` as used to create the cookie (see
            :meth:`Response.set_cookie`). If anything goes wrong, None is
            returned.
        """
        value = self.COOKIES.get(key)
        if secret and value:
            dec = cookie_decode(value, secret) # (key, value) tuple or None
            return dec[1] if dec and dec[0] == key else None
        return value or None

    @property
    def is_ajax(self):
        ''' True if the request was generated using XMLHttpRequest '''
        #TODO: write tests
        return self.header.get('X-Requested-With') == 'XMLHttpRequest'