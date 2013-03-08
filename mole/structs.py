# -*- coding: utf-8 -*-

import functools
try: from collections import MutableMapping as DictMixin
except ImportError: # pragma: no cover
    from UserDict import DictMixin
    
    
class MultiDict(DictMixin):
    """ A dict that remembers old values for each key """
    # collections.MutableMapping would be better for Python >= 2.6
    def __init__(self, *a, **k):
        self.dict = dict()
        for k, v in dict(*a, **k).iteritems():
            self[k] = v

    def __len__(self): return len(self.dict)
    def __iter__(self): return iter(self.dict)
    def __contains__(self, key): return key in self.dict
    def __delitem__(self, key): del self.dict[key]
    def keys(self): return self.dict.keys()
    def __getitem__(self, key): return self.get(key, KeyError, -1)
    def __setitem__(self, key, value): self.append(key, value)

    def append(self, key, value): self.dict.setdefault(key, []).append(value)
    def replace(self, key, value): self.dict[key] = [value]
    def getall(self, key): return self.dict.get(key) or []

    def get(self, key, default=None, index=-1):
        if key not in self.dict and default != KeyError:
            return [default][index]
        return self.dict[key][index]

    def iterallitems(self):
        for key, values in self.dict.iteritems():
            for value in values:
                yield key, value
                
                
class DictProperty(object):
    ''' Property that maps to a key in a local dict-like attribute. '''
    def __init__(self, attr, key=None, read_only=False):
        self.attr, self.key, self.read_only = attr, key, read_only

    def __call__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.getter, self.key = func, self.key or func.__name__
        return self

    def __get__(self, obj, cls):
        if not obj: return self
        key, storage = self.key, getattr(obj, self.attr)
        if key not in storage: storage[key] = self.getter(obj)
        return storage[key]

    def __set__(self, obj, value):
        if self.read_only: raise AttributeError("Read-Only property.")
        getattr(obj, self.attr)[self.key] = value

    def __delete__(self, obj):
        if self.read_only: raise AttributeError("Read-Only property.")
        del getattr(obj, self.attr)[self.key]
        
def cached_property(func):
    ''' A property that, if accessed, replaces itself with the computed
        value. Subsequent accesses won't call the getter again. '''
    return DictProperty('__dict__')(func)

class lazy_attribute(object): # Does not need configuration -> lower-case name
    ''' A property that caches itself to the class object. '''
    def __init__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.getter = func
    
    def __get__(self, obj, cls):
        value = self.getter(cls)
        setattr(cls, self.__name__, value)
        return value