
import logging
import os.path
import os, sys
from datetime import datetime,timedelta
from time import mktime


import wsgiref.util
from wsgiref.handlers import format_date_time

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext.webapp import Request
from google.appengine.ext.webapp.util import run_wsgi_app


from repoze.bfg.registry import populateRegistry
from repoze.bfg.interfaces import IGETRequest,IPOSTRequest
from gae.utils import BREAKPOINT

from zope.component import getSiteManager        
from zope.tales.engine import Engine


       
class ActionContext(object):
    _engine = Engine
    
    def __init__(self,req,d={}):
        self.dicts = d
        self.vars = d
        self.request = req 
        

##def get_cache():
##    if users.is_current_user_admin():
##        return None
##    env = dict(os.environ)
##    env["wsgi.input"] = sys.stdin
##    env["wsgi.errors"] = sys.stderr
##    env["wsgi.version"] = (1, 0)
##    env["wsgi.run_once"] = True
##    env["wsgi.url_scheme"] = wsgiref.util.guess_scheme(env)
##    env["wsgi.multithread"] = False
##    env["wsgi.multiprocess"] = False
##    req = Request(env)
##    cached_resp = memcache.get(req.path_url.rstrip('/'))
##    
##    if cached_resp:
##        def cache_app(env,start_resp):
##            logging.info('returning cached page (%s)' % req.path_url)
##            #BREAKPOINT()
##            write_handle = start_resp(cached_resp.status,(cached_resp.headers.items()))
##            write_handle(cached_resp.body)
##        return cache_app
##    else:
##
##        return None


def cacheoutput(func):
    """ memcache caching decorator"""
    def _wrapper(context, REQUEST):
        
        output = func(context, REQUEST)
        if not getattr(REQUEST.principal,'ADMIN',False):
            key=REQUEST.path_url.rstrip('/')
            logging.debug('cacheoutput: %s - %s' % (key,repr(output)))
            memcache.set(key,output,86400)
        return output    
            
    return _wrapper


def cacheviewfragment(meth):
    def _wrapper(self):
        
        key = self.request.url.rstrip('/')+':FRAGMENT:'+repr(self.view.__class__) 
        isAdmin = getattr(self.request.principal,'ADMIN',False)
        
        if not isAdmin:
            
            output = memcache.get(key)
            if output:
                logging.debug('got from cacheviewfragment: %s' % (key))
                return output
            
        output = meth(self)
        
        if not isAdmin:
            logging.debug('cacheviewfragment: %s' % (key))
            memcache.set(key,output,86400)
            
        return output    
            
    return _wrapper

def cachemethodoutput(meth):
    def _wrapper(self):
        
        key = self.request.url.rstrip('/') 
        isAdmin = getattr(self.request.principal,'ADMIN',False)
        
        if not isAdmin:
            if IPOSTRequest.providedBy(self.request):
                key = key + ":POST:" + str(self.request.str_POST)
            
            
            
            output = memcache.get(key)
            if output:
                logging.debug('got from cachemethodoutput: %s' % (key))
                return output
            
        output = meth(self)
        
        if not isAdmin:
            logging.debug('cachemethodoutput: %s' % (key))
            memcache.set(key,output,86400)
            
        return output    
            
    return _wrapper

def cachefixedportlet(meth):
    
    def _wrapper(self):
        output = None
        isAdmin = getattr(self.request.principal,'ADMIN',False)
        
        key=self.request.SKIN_NAME+':PORTLET:'+self.portlet.getPath()
        
        if not isAdmin:
            output = memcache.get(key)
            if output:
                logging.debug('got from cachefixedportlet: %s' % (key))
                return output
        
        output = meth(self)
        
        if not isAdmin:
            logging.debug('cachefixedportlet: %s' % (key))
            memcache.set(key,output,86400)
            
        return output    
            
    return _wrapper

def cachefixedview(meth):
    
    def _wrapper(self):
        
        output = None
        isAdmin = getattr(self.request.principal,'ADMIN',False)
        
        key=self.request.SKIN_NAME+':VIEW:'+str(self.__class__)
        
        if not isAdmin:
            output = memcache.get(key)
            if output:
                return output
        
        output = meth(self)
        
        if not isAdmin:
            logging.debug('cachefixedview: %s' % (key))
            memcache.set(key,output,86400)
            
        return output    
            
    return _wrapper


##def cacheinstancemethodoutput(func):
##    """ memcache caching decorator for instance methods"""
##    def _wrapper(context, mcontext, REQUEST):
##        mcontext = context
##        if hasattr(context,'context'):
##            mcontext = context.context
##        output = func(context, mcontext, REQUEST)
##        if not getattr(REQUEST.principal,'ADMIN',False):
##            key=REQUEST.path_url.rstrip('/')
##            memcache.set(key,output,86400)
##            logging.info('cache key: %s' % key)
##        return output    
##            
##    return _wrapper


def make_time_header(thetime=None,add=0):
    
    if not thetime:
        thetime = datetime.now()
    
    if add:
        thetime = thetime + timedelta(days=add)
        
    return format_date_time(mktime(thetime.timetuple()))
