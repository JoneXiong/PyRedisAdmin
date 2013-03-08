# -*- coding: utf-8 -*-
"""
Server

a list Server Adapter for wsgi
"""
import sys
import os

class ServerAdapter(object):
    quiet = False   # 是否禁用标准输出和错误输出
    def __init__(self, host='127.0.0.1', port=8080, **config):
        self.options = config
        self.host = host
        self.port = int(port)

    def run(self, handler): # pragma: no cover
        pass
        
    def __repr__(self):
        ''' 返回一个对象的字符串表示 '''
        args = ', '.join(['%s=%s'%(k,repr(v)) for k, v in self.options.items()])
        return "%s(%s)" % (self.__class__.__name__, args)
    
    
class BjoernServer(ServerAdapter):
    """ Screamingly fast server written in C: https://github.com/jonashaag/bjoern """
    def run(self, handler):
        from bjoern import run
        run(handler, self.host, self.port)

class UVWebServer(ServerAdapter):
    """ Screamingly fast server written in C: https://github.com/jonashaag/bjoern """
    def run(self, handler):
        from uvweb import run
        run(handler, self.host, self.port)
        
class CGIServer(ServerAdapter):
    quiet = True
    def run(self, handler): # pragma: no cover
        from wsgiref.handlers import CGIHandler
        CGIHandler().run(handler) # Just ignore host and port here
        
        
class FlupFCGIServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        import flup.server.fcgi
        kwargs = {'bindAddress':(self.host, self.port)}
        kwargs.update(self.options) # allow to override bindAddress and others
        flup.server.fcgi.WSGIServer(handler, **kwargs).run()


class WSGIRefServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        srv = make_server(self.host, self.port, handler, **self.options)
        srv.serve_forever()


class CherryPyServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        from cherrypy import wsgiserver
        server = wsgiserver.CherryPyWSGIServer((self.host, self.port), handler)
        server.start()


class PasteServer(ServerAdapter):
    def run(self, handler): # pragma: no cover
        from paste import httpserver
        if not self.quiet:
            from paste.translogger import TransLogger
            handler = TransLogger(handler)
        httpserver.serve(handler, host=self.host, port=str(self.port),
                         **self.options)
                         
class MeinheldServer(ServerAdapter):
    def run(self, handler):
        from meinheld import server
        server.listen((self.host, self.port))
        server.run(handler)

class FapwsServer(ServerAdapter):
    """ Extremely fast webserver using libev. See http://www.fapws.org/ """
    def run(self, handler): # pragma: no cover
        import fapws._evwsgi as evwsgi
        from fapws import base, config
        port = self.port
        if float(config.SERVER_IDENT[-2:]) > 0.4:
            # fapws3 silently changed its API in 0.5
            port = str(port)
        evwsgi.start(self.host, port)
        # fapws3 never releases the GIL. Complain upstream. I tried. No luck.
        if 'MOLE_CHILD' in os.environ and not self.quiet:
            print "WARNING: Auto-reloading does not work with Fapws3."
            print "         (Fapws3 breaks python thread support)"
        evwsgi.set_base_module(base)
        def app(environ, start_response):
            environ['wsgi.multiprocess'] = False
            return handler(environ, start_response)
        evwsgi.wsgi_cb(('', app))
        evwsgi.run()


class TornadoServer(ServerAdapter):
    """ The super hyped asynchronous server by facebook. Untested. """
    def run(self, handler): # pragma: no cover
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop
        container = tornado.wsgi.WSGIContainer(handler)
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port=self.port)
        tornado.ioloop.IOLoop.instance().start()


class AppEngineServer(ServerAdapter):
    """ Adapter for Google App Engine. """
    quiet = True
    def run(self, handler):
        from google.appengine.ext.webapp import util
        # A main() function in the handler script enables 'App Caching'.
        # Lets makes sure it is there. This _really_ improves performance.
        module = sys.modules.get('__main__')
        if module and not hasattr(module, 'main'):
            module.main = lambda: util.run_wsgi_app(handler)
        util.run_wsgi_app(handler)


class TwistedServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        from twisted.web import server, wsgi
        from twisted.python.threadpool import ThreadPool
        from twisted.internet import reactor
        thread_pool = ThreadPool()
        thread_pool.start()
        reactor.addSystemEventTrigger('after', 'shutdown', thread_pool.stop)
        factory = server.Site(wsgi.WSGIResource(reactor, thread_pool, handler))
        reactor.listenTCP(self.port, factory, interface=self.host)
        reactor.run()


class DieselServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        from diesel.protocols.wsgi import WSGIApplication
        app = WSGIApplication(handler, port=self.port)
        app.run()


class GeventServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        from gevent import wsgi
        #from gevent.hub import getcurrent
        #self.set_context_ident(getcurrent, weakref=True) # see contextlocal
        wsgi.WSGIServer((self.host, self.port), handler).serve_forever()


class GunicornServer(ServerAdapter):
    """ Untested. """
    def run(self, handler):
        from gunicorn.arbiter import Arbiter
        from gunicorn.config import Config
        handler.cfg = Config({'bind': "%s:%d" % (self.host, self.port), 'workers': 4})
        arbiter = Arbiter(handler)
        arbiter.run()


class EventletServer(ServerAdapter):
    """ Untested """
    def run(self, handler):
        from eventlet import wsgi, listen
        wsgi.server(listen((self.host, self.port)), handler)


class RocketServer(ServerAdapter):
    """ Untested. As requested in issue 63
        https://github.com/defnull/mole/issues/#issue/63 """
    def run(self, handler):
        from rocket import Rocket
        server = Rocket((self.host, self.port), 'wsgi', { 'wsgi_app' : handler })
        server.start()

class AutoServer(ServerAdapter):
    """ Untested. """
    adapters = [PasteServer, CherryPyServer, TwistedServer, WSGIRefServer]
    def run(self, handler):
        for sa in self.adapters:
            try:
                return sa(self.host, self.port, **self.options).run(handler)
            except ImportError:
                pass
            
            
server_names = {
    'cgi': CGIServer,
    'flup': FlupFCGIServer,
    'wsgiref': WSGIRefServer,
    'cherrypy': CherryPyServer,
    'paste': PasteServer,
    'fapws3': FapwsServer,
    'tornado': TornadoServer,
    'gae': AppEngineServer,
    'twisted': TwistedServer,
    'diesel': DieselServer,
    'meinheld': MeinheldServer,
    'gunicorn': GunicornServer,
    'eventlet': EventletServer,
    'gevent': GeventServer,
    'rocket': RocketServer,
    'bjoern' : BjoernServer,
    'uvweb' : UVWebServer,
    'auto': AutoServer,
}
