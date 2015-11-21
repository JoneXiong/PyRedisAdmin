# coding=utf-8

import gettext
from functools import wraps
# import jinja2
from mole.template import BaseTemplate
import config

def to_unicode(v, encoding='utf8'):
    if isinstance(v, unicode):
        return v
    try:
        return v.decode(encoding)
    except (AttributeError, UnicodeEncodeError):
        return unicode(v)
    
def to_bytes(v, encoding='utf8'):
    if isinstance(v, bytes):
        return v
    try:
        return v.encode(encoding, errors='ignore')
    except AttributeError:
        return unicode(v).encode(encoding)

    
class Lazy(object):
    """
    Lazy proxy object. This proxy always evaluates the function when it is
    used.
    Any positional and keyword arguments that are passed to the constructor are
    stored and passed to the function except the ``_func`` argument which is
    the function itself. Because of this, the wrapped callable cannot use an
    argument named ``_func`` itself.
    """

    def __init__(self, _func, *args, **kwargs):
        self._func = _func
        self._args = args
        self._kwargs = kwargs

    def _eval(self):
        return self._func(*self._args, **self._kwargs)

    @staticmethod
    def _eval_other(other):
        try:
            return other._eval()
        except AttributeError:
            return other

    def __getattr__(self, attr):
        obj = self._eval()
        return getattr(obj, attr)

    # We don't need __setattr__ and __delattr__ because the proxy object is not
    # really an object.

    def __getitem__(self, key):
        obj = self._eval()
        return obj.__getitem__(key)

    @property
    def __class__(self):
        return self._eval().__class__

    def __repr__(self):
        return repr(self._eval())

    def __str__(self):
        return to_unicode(self._eval())

    def __bytes__(self):
        return to_bytes(self._eval())

    def __call__(self):
        return self._eval()()

    def __format__(self, format_spec):
        return self._eval().__format__(format_spec)

    def __mod__(self, other):
        return self._eval().__mod__(other)

    # Being explicit about all comparison methods to avoid double-calls

    def __lt__(self, other):
        other = self._eval_other(other)
        return self._eval() < other

    def __le__(self, other):
        other = self._eval_other(other)
        return self._eval() <= other

    def __gt__(self, other):
        other = self._eval_other(other)
        return self._eval() > other

    def __ge__(self, other):
        other = self._eval_other(other)
        return self._eval() >= other

    def __eq__(self, other):
        other = self._eval_other(other)
        return self._eval() == other

    def __ne__(self, other):
        other = self._eval_other(other)
        return self._eval() != other

    # We mostly use this for strings, so having just __add__ is fine

    def __add__(self, other):
        other = self._eval_other(other)
        return self._eval() + other

    def __radd__(self, other):
        return self._eval_other(other) + self._eval()

    def __bool__(self):
        return bool(self._eval())

    __nonzero__ = __bool__

    def __hash__(self):
        return hash(self._eval())
    
def lazy(fn):
    """
    Convert a function into lazily evaluated version. This decorator causes the
    function to return a :py:class:`~Lazy` proxy instead of the actual results.
    Usage is simple::
        @lazy
        def my_lazy_func():
            return 'foo'
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return Lazy(fn, *args, **kwargs)
    return wrapper



api = gettext.translation('PyRedisAdmin', 'locale', languages=[config.lang])

@lazy
def lazy_gettext(message):
    return to_unicode(api.gettext(message))

BaseTemplate.defaults.update({
    'trans': lazy_gettext,
})

# _ = gettext.gettext

# SimpleTemplate.global_config('_', _)

# jjenv = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'),extensions=['jinja2.ext.i18n'])
# 
# def set_lang(lang):
#        #'lang'表示语言文件名为lang.mo，'i18n'表示语言文件名放在‘i18n'目录下，比如：
#        #中文翻译目录和文件：i18n\zh-cn\LC_MESSAGES\lang.mo
#        gettext.install('lang', 'i18n', unicode=True)
#        tr = gettext.translation('lang', 'i18n', languages=[lang])
#        tr.install(True)
#        jjenv.install_gettext_translations(tr)