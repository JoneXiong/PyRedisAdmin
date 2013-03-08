# -*- coding: utf-8 -*-

from Cookie import SimpleCookie
import threading


import utils
from structs import MultiDict

class HeaderDict(MultiDict):
    """ Same as :class:`MultiDict`, but title()s the keys and overwrites by default. """
    def __contains__(self, key): return MultiDict.__contains__(self, self.httpkey(key))
    def __getitem__(self, key): return MultiDict.__getitem__(self, self.httpkey(key))
    def __delitem__(self, key): return MultiDict.__delitem__(self, self.httpkey(key))
    def __setitem__(self, key, value): self.replace(key, value)
    def get(self, key, default=None, index=-1): return MultiDict.get(self, self.httpkey(key), default, index)
    def append(self, key, value): return MultiDict.append(self, self.httpkey(key), str(value))
    def replace(self, key, value): return MultiDict.replace(self, self.httpkey(key), str(value))
    def getall(self, key): return MultiDict.getall(self, self.httpkey(key))
    def httpkey(self, key): return str(key).replace('_','-').title()
    
    
class Response(threading.local):
    """ Represents a single HTTP response using thread-local attributes.
    """

    def __init__(self):
        self.bind()

    def bind(self):
        """ Resets the Response object to its factory defaults. """
        self._COOKIES = None
        self.status = 200
        self.headers = HeaderDict()
        self.content_type = 'text/html; charset=UTF-8'

    @property
    def header(self):
        utils.depr("Response.header renamed to Response.headers")
        return self.headers

    def copy(self):
        ''' Returns a copy of self. '''
        copy = Response()
        copy.status = self.status
        copy.headers = self.headers.copy()
        copy.content_type = self.content_type
        return copy

    def wsgiheader(self):
        ''' Returns a wsgi conform list of header/value pairs. '''
        for c in self.COOKIES.values():
            if c.OutputString() not in self.headers.getall('Set-Cookie'):
                self.headers.append('Set-Cookie', c.OutputString())
        # rfc2616 section 10.2.3, 10.3.5
        if self.status in (204, 304) and 'content-type' in self.headers:
            del self.headers['content-type']
        if self.status == 304:
            for h in ('allow', 'content-encoding', 'content-language',
                      'content-length', 'content-md5', 'content-range',
                      'content-type', 'last-modified'): # + c-location, expires?
                if h in self.headers:
                     del self.headers[h]
        return list(self.headers.iterallitems())
    headerlist = property(wsgiheader)

    @property
    def charset(self):
        """ Return the charset specified in the content-type header.
        
            This defaults to `UTF-8`.
        """
        if 'charset=' in self.content_type:
            return self.content_type.split('charset=')[-1].split(';')[0].strip()
        return 'UTF-8'

    @property
    def COOKIES(self):
        """ A dict-like SimpleCookie instance. Use :meth:`set_cookie` instead. """
        if not self._COOKIES:
            self._COOKIES = SimpleCookie()
        return self._COOKIES

    def set_cookie(self, key, value, secret=None, **kargs):
        ''' Add a cookie. If the `secret` parameter is set, this creates a
            `Secure Cookie` (described below).

            :param key: the name of the cookie.
            :param value: the value of the cookie.
            :param secret: required for secure cookies. (default: None)
            :param max_age: maximum age in seconds. (default: None)
            :param expires: a datetime object or UNIX timestamp. (defaut: None)
            :param domain: the domain that is allowed to read the cookie.
              (default: current domain)
            :param path: limits the cookie to a given path (default: /)

            If neither `expires` nor `max_age` are set (default), the cookie
            lasts only as long as the browser is not closed.

            Secure cookies may store any pickle-able object and are
            cryptographically signed to prevent manipulation. Keep in mind that
            cookies are limited to 4kb in most browsers.
            
            Warning: Secure cookies are not encrypted (the client can still see
            the content) and not copy-protected (the client can restore an old
            cookie). The main intention is to make pickling and unpickling
            save, not to store secret information at client side.
        '''
        if secret:
            value = utils.touni(cookie_encode((key, value), secret))
        elif not isinstance(value, basestring):
            raise TypeError('Secret missing for non-string Cookie.')

        self.COOKIES[key] = value
        for k, v in kargs.iteritems():
            self.COOKIES[key][k.replace('_', '-')] = v

    def delete_cookie(self, key, **kwargs):
        ''' Delete a cookie. Be sure to use the same `domain` and `path`
            parameters as used to create the cookie. '''
        kwargs['max_age'] = -1
        kwargs['expires'] = 0
        self.set_cookie(key, '', **kwargs)

    def get_content_type(self):
        """ Current 'Content-Type' header. """
        return self.headers['Content-Type']

    def set_content_type(self, value):
        self.headers['Content-Type'] = value

    content_type = property(get_content_type, set_content_type, None,
                            get_content_type.__doc__)
