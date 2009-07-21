""" utils"""
from yaml import load, dump

import os

from google.appengine.api import users

from decorator import *
from webob.exc import HTTPFound,HTTPTemporaryRedirect, HTTPSeeOther

def Redirect(location):
    
    return HTTPSeeOther(location=location)

def BREAKPOINT():
      import sys
      import pdb
      p = pdb.Pdb(None, sys.__stdin__, sys.__stdout__)
      p.set_trace() 

_modsettings = {}

def loadSettings(settings='settings.yaml'):
    
    x= _modsettings
    if not x:
        _modsettings.update(load(open(settings,'r').read()))
        
    return _modsettings

settings = loadSettings()


def public(func):
    """ """
    setattr(func,'_is_public',True)
    return func


def admin_required(func):
    """ """
    def _wrapper(context, REQUEST):
        """ admin required decorator """
        is_admin = users.is_current_user_admin()
        if is_admin:
            return func(context, REQUEST)
        else:
            return HTTPTemporaryRedirect(location=users.create_login_url(REQUEST.url))
      
    
    return _wrapper

    

