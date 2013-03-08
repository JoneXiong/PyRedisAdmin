# -*- coding: utf-8 -*-

import warnings
import sys




def depr(message, critical=False):
    if critical: raise DeprecationWarning(message)
    warnings.warn(message, DeprecationWarning, stacklevel=3)
    
def tob(data, enc='utf8'):
    """ Convert anything to bytes """
    return data.encode(enc) if isinstance(data, unicode) else bytes(data)

def _lscmp(a, b):
    ''' Compares two strings in a cryptographically save way:
        Runtime is not affected by a common prefix. '''
    return not sum(0 if x==y else 1 for x, y in zip(a, b)) and len(a) == len(b)



if sys.version_info >= (3,0,0):
    def touni(x, enc='utf8'):
        """ Convert anything to unicode """
        return str(x, encoding=enc) if isinstance(x, bytes) else str(x)
else:
    def touni(x, enc='utf8'):
        """ Convert anything to unicode """
        return x if isinstance(x, unicode) else unicode(str(x), encoding=enc)
    
# Convert strings and unicode to native strings
if sys.version_info >= (3,0,0):
    tonat = touni
else:
    tonat = tob
tonat.__doc__ = """ Convert anything to native strings """