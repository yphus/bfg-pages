
import logging
import os.path
from datetime import datetime,timedelta
from time import mktime

from wsgiref.handlers import format_date_time

from google.appengine.api import memcache

from repoze.bfg.registry import populateRegistry

from gae.utils import BREAKPOINT

from zope.component import getSiteManager        
from zope.tales.engine import Engine


       
class ActionContext(object):
    _engine = Engine
    
    def __init__(self,req,d={}):
        self.dicts = d
        self.vars = d
        self.request = req 
        



def cacheoutput(func):
    """ memcache caching decorator"""
    def _wrapper(context, REQUEST):
        output = func(context, REQUEST)
        if not getattr(REQUEST.principal,'ADMIN',False):
            key=REQUEST.path_url
            memcache.set(key,output,86400)
        return output    
            
    return _wrapper

##def init_editing(packages):
##    
##    logging.debug('Loading editing')
##    sm = getSiteManager()
##    for zcmlfile,packagespace in packages:
##        populateRegistry(sm,zcmlfile,packagespace)
##    logging.debug('Loaded editing')


def make_time_header(thetime=None,add=0):
    
    if not thetime:
        thetime = datetime.now()
    
    if add:
        thetime = thetime + timedelta(days=add)
        
    return format_date_time(mktime(thetime.timetuple()))