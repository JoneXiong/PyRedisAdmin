# -*- coding: utf-8 -*-

import re


from common import HTTPError,MoleException
from structs import lazy_attribute


class RouteError(MoleException):
    """ This is a base class for all routing related exceptions """

class RouteSyntaxError(RouteError):
    """ The route parser found something not supported by this router """

class RouteBuildError(RouteError):
    """ The route could not been built """

class Router(object):
    ''' 
     A route is defined by a path-rule and a HTTP method.
     wildcards consume characters up to the next slash (`/`).
     The path-rule is either a static path  or a dynamic path
          
        The path-rule is either a static path (e.g. `/contact`) or a dynamic
        path that contains wildcards (e.g. `/wiki/:page`). By default, wildcards
        consume characters up to the next slash (`/`). To change that, you may
        add a regular expression pattern (e.g. `/wiki/:page#[a-z]+#`).

        For performance reasons, static routes (rules without wildcards) are
        checked first. Dynamic routes are tested in order and the first
        matching rule returns. Try to avoid ambiguous or overlapping rules.

        The HTTP method string matches only on equality, with two exceptions:
          * ´GET´ routes also match ´HEAD´ requests if there is no appropriate
            ´HEAD´ route installed.
          * ´ANY´ routes do match if there is no other suitable route installed.
    '''
    default = '[^/]+'

    @lazy_attribute
    def syntax(cls):
        return re.compile(r'(?<!\\):([a-zA-Z_][a-zA-Z_0-9]*)?(?:#(.*?)#)?')

    def __init__(self):
        self.routes = {}  # A {rule: {method: target}} mapping
        self.rules  = []  # An ordered list of rules
        self.named  = {}  # A name->(rule, build_info) mapping
        self.static = {}  # Cache for static routes: {path: {method: target}}
        self.dynamic = [] # Cache for dynamic routes. See _compile()

    def add(self, rule, method, target, name=None):
        ''' Add a new route or overwrite an existing target. '''
        if rule in self.routes:#self.routes.has_key(rule)
            self.routes[rule][method.upper()] = target
        else:
            self.routes[rule] = {method.upper(): target}
            self.rules.append(rule)
            if self.static or self.dynamic: # Clear precompiler cache.
                self.static, self.dynamic = {}, {}
        if name:
            self.named[name] = (rule, None)

    def delete(self, rule, method=None):
        ''' Delete an existing route. Omit `method` to delete all targets. '''
        if rule not in self.routes and rule in self.named:
            rule = self.named[rule][0]
        if rule in self.routes:
            if method: del self.routes[rule][method]
            else: self.routes[rule].clear() #清空字典
            if not self.routes[rule]:
                del self.routes[rule]
                self.rules.remove(rule)

    def build(self, _name, *anon, **args):
        from urllib import urlencode
        print '*anon, **args',anon,args
        ''' Return a string that matches a named route. Use keyword arguments
            to fill out named wildcards. Remaining arguments are appended as a
            query string. Raises RouteBuildError or KeyError.'''
        if _name not in self.named:
            raise RouteBuildError("No route with that name.", _name)
        rule, pairs = self.named[_name]
        if not pairs:
            token = self.syntax.split(rule)
            parts = [p.replace('\\:',':') for p in token[::3]]
            names = token[1::3]
            if len(parts) > len(names): names.append(None)
            pairs = zip(parts, names)
            print 'build build_info...',pairs
            self.named[_name] = (rule, pairs)
        try:
            anon = list(anon)   # * 参数的处理
            url = [s if k is None
                   else s+str(args.pop(k)) if k else s+str(anon.pop())
                   for s, k in pairs]
        except IndexError:
            msg = "Not enough arguments to fill out anonymous wildcards.缺少参数匹配"
            raise RouteBuildError(msg)
        except KeyError, e:
            raise RouteBuildError(*e.args)
        
        if args: url += ['?', urlencode(args)]
        print 'build url_list...',url
        return ''.join(url)

    def match(self, environ):
        ''' Return a (target, url_agrs) tuple or raise HTTPError(404/405). '''
        targets, urlargs = self._match_path(environ)
        if not targets:
            raise HTTPError(404, "Not found: " + environ.get('PATH_INFO',''))
        environ['router.url_args'] = urlargs
        method = environ['REQUEST_METHOD'].upper()
        if method in targets:
            return targets[method], urlargs
        if method == 'HEAD' and 'GET' in targets:
            return targets['GET'], urlargs
        if 'ANY' in targets:
            return targets['ANY'], urlargs
        allowed = [verb for verb in targets if verb != 'ANY']
        if 'GET' in allowed and 'HEAD' not in allowed:
            allowed.append('HEAD')
        raise HTTPError(405, "Method not allowed.",
                        header=[('Allow',",".join(allowed))])

    def _match_path(self, environ):
        ''' Optimized PATH_INFO matcher. '''
        path = environ['PATH_INFO'] or '/'
        # Assume we are in a warm state. Search compiled rules first.
        match = self.static.get(path)
        if match: return match, {}
        for combined, rules in self.dynamic:
            match = combined.match(path)
            if not match: continue
            gpat, match = rules[match.lastindex - 1]
            return match, gpat.match(path).groupdict() if gpat else {}
        # Lazy-check if we are really in a warm state. If yes, stop here.
        if self.static or self.dynamic or not self.routes: return None, {}
        # Cold state: We have not compiled any rules yet. Do so and try again.
        if not environ.get('wsgi.run_once'):
            self._compile()
            return self._match_path(environ)
        # For run_once (CGI) environments, don't compile. Just check one by one.
        epath = path.replace(':','\\:') # Turn path into its own static rule.
        match = self.routes.get(epath) # This returns static rule only.
        if match: return match, {}
        for rule in self.rules:
            #: Skip static routes to reduce re.compile() calls.
            if rule.count(':') < rule.count('\\:'): continue
            match = self._compile_pattern(rule).match(path)
            if match: return self.routes[rule], match.groupdict()
        return None, {}

    def _compile(self):
        ''' Prepare static and dynamic search structures. '''
        self.static = {}
        self.dynamic = []
        def fpat_sub(m):
            return m.group(0) if len(m.group(1)) % 2 else m.group(1) + '(?:'
        for rule in self.rules:
            target = self.routes[rule]
            if not self.syntax.search(rule):
                self.static[rule.replace('\\:',':')] = target
                continue
            gpat = self._compile_pattern(rule)
            fpat = re.sub(r'(\\*)(\(\?P<[^>]*>|\((?!\?))', fpat_sub, gpat.pattern)
            gpat = gpat if gpat.groupindex else None
            try:
                combined = '%s|(%s)' % (self.dynamic[-1][0].pattern, fpat)
                self.dynamic[-1] = (re.compile(combined), self.dynamic[-1][1])
                self.dynamic[-1][1].append((gpat, target))
            except (AssertionError, IndexError), e: # AssertionError: Too many groups
                self.dynamic.append((re.compile('(^%s$)'%fpat),
                                    [(gpat, target)]))
            except re.error, e:
                raise RouteSyntaxError("Could not add Route: %s (%s)" % (rule, e))

    def _compile_pattern(self, rule):
        ''' Return a regular expression with named groups for each wildcard. '''
        out = ''
        for i, part in enumerate(self.syntax.split(rule)):
            if i%3 == 0:   out += re.escape(part.replace('\\:',':'))
            elif i%3 == 1: out += '(?P<%s>' % part if part else '(?:'
            else:          out += '%s)' % (part or '[^/]+')
        return re.compile('^%s$'%out)
