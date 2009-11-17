import sys
from google.appengine.ext import db
import wsgiref.handlers


from google.appengine.ext import webapp

from gae.utils import settings 

from pages.models import getRoot

import zope.component
from zope.interface import directlyProvides, implementedBy

from gae.pagetemplate import get_template, Context 
from google.appengine.api import users         
from  pages import models
import logging
import load_data
from load_data import DBKeys

from logging import info

from gae.utils import BREAKPOINT
 
from repoze.bfg.router import make_app
import pages.models 
from pages.models import getRoot as get_root
from gae.utils import settings



def create_site(i,request):
    results = []
    
    info("class %s",str(i[0]))
    results.append("class %s"%str(i[0]))
    klass = i[0]
    entities = i[1]
    #BREAKPOINT()
    for args in entities:
        ref = None
        ref_key = None
        #BREAKPOINT()
        for arg in args:
            
            #if type(args[arg])== DBKeys:
            #    BREAKPOINT()
            
            if type(args[arg]) not in [ unicode,str,db.Email,DBKeys,list,int,bool]:
                #BREAKPOINT()
                ref=[i for i in list(args[arg].all()) if i.name == args[arg].name]
                ref_key = arg
                if ref:
                    ref = ref[0]
        
                args[ref_key]=ref
            
            if type(args[arg]) == DBKeys:
                args[arg] = list(args[arg])
        try:    
            info("obj is %s"%args['name'])
        except:
            info(str(args))
            
        results.append("obj is %s"%args['name'])
        if args.has_key('parent_'):    
            root = getRoot(request)
            path = args.get('parent_')
            kwargs = dict(args)
            del kwargs['parent_']
            del kwargs['name']
            #if klass == models.Scene:
            
            try:
                
                x = root.createContent(args['name'],klass,path,request,**kwargs)
            except Exception,e:
                info(str(e))
                logging.error(str(e))
        else:
            
            x=klass(**args)
            x.put()
            
    return results
     
      
def start_setup(request,data=load_data.data):
    if users.is_current_user_admin():
        root = getRoot(request)
        action = request.params.get('action')
        data_request=request.params.get('data',None)
        #BREAKPOINT()
        if action:
            if action == 'ALL':
                
                for i in data:
                    resp = create_site(i,request)
                    i[3].append(resp[0:min(10,len(resp))])
                    
            if action == 'data':
                
                if hasattr(backup_data,data_request):
                    data = getattr(backup_data,data_request).data

                    create_site(data,request) 
                    data = []       
            else:    
                for i in data:
                    if i[2] == action:
                        resp = create_site(i,request)
                        i[3].append(resp[0:min(10,len(resp))])
                        break
              
        return data
    else:
        return []