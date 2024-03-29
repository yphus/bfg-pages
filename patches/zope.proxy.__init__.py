##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""More convenience functions for dealing with proxies.

$Id: __init__.py 75661 2007-05-10 05:31:51Z baijum $
"""
from zope.interface import moduleProvides
from zope.proxy.interfaces import IProxyIntrospection

try:
    from zope.proxy._zope_proxy_proxy import *
    from zope.proxy._zope_proxy_proxy import _CAPI
except ImportError,NotImplementedError:
    pass


from peak.util.proxies import ObjectProxy
 
class ProxyBase(ObjectProxy):
     pass
 
def getProxiedObject(obj):
     
     if hasattr(obj,'__subject__'):
         return obj.__subject__
     else:
         return obj

def removeAllProxies(obj):
    return getProxiedObject(obj)


def sameProxiedObjects(obj1,obj2):
    if getProxiedObject(obj1) == getProxiedObject(obj2):
        return True
    else:
        return False    
        
        
    
    
    
    
moduleProvides(IProxyIntrospection)
__all__ = tuple(IProxyIntrospection)

def ProxyIterator(p):
    yield p
    while isProxy(p):
        p = getProxiedObject(p)
        yield p

def non_overridable(func):
    return property(lambda self: func.__get__(self))
