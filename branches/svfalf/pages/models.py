
import sys
import os
import datetime
from itertools import groupby
from urllib import unquote


import zope.lifecycleevent
import zope.interface
import zope.component
from zope.interface import implements,Interface,providedBy
from zope.tales.engine import Engine
from zope.interface.declarations import getObjectSpecification
from zope.component import queryMultiAdapter

import repoze.bfg.interfaces
from repoze.bfg.traversal import model_path, find_model, find_root, traverse
from repoze.bfg.threadlocal import get_current_request
from repoze.bfg.url import model_url

from gae.pagetemplate import render_template_to_response, render_template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.ext.db import polymodel
from google.appengine.api import images

import schemaish.type

from gae.pagetemplate import get_template
try:
    from xml.etree import ElementTree
except:
    pass
from gae.utils import admin_required, Redirect,settings

from interfaces import IContentish
import interfaces
from repoze.bfg.threadlocal import get_current_registry

from gae.utils import BREAKPOINT

import utils
from utils import retry
import getimageinfo
import logging

#import registry

class DuplicateName(Exception):
    pass


class HasActions(object):
    
    def getActions(self,request,group=None,notag=False):
        
        root = self.getRoot()

        cache_key = '%s:action:%s:%s:%s' % (request.host,str(self.getPath()),str(group),str(users.get_current_user()))

        cached_result = root.getcached(cache_key)
        
        if cached_result:
            return cached_result 
        
        star_actions = Action.all().filter('content = ',"*")
        kind_actions = Action.all().filter('content = ',self.kind())
        
        if group:
            star_actions = star_actions.filter('group = ',group)
            kind_actions = kind_actions.filter('group = ',group)

        results = []
        all_actions = list(star_actions) + list(kind_actions)
        all_actions.sort(lambda x,y: cmp(int(x.display_order), int(y.display_order)))
        for action in all_actions:
            
            if action.allowed(self,request):
                results.append( action.resolve(self,request,notag) )

        root.setcached(cache_key,results)
        
        return results
    
def getPortlets(context,request,group=None,notag=False):
    root = context.getRoot()
        
##    cache_key = 'portlet:%s:%s:%s' % (str(context.getPath()),str(group),str(users.get_current_user()))
##
##    cached_result = root.getcached(cache_key)
##
##    if cached_result and not getattr(request.principal,'ADMIN',False):
##        return cached_result 

    star_portlets = Portlet.all().filter('content = ',"*")
    kind_portlets = Portlet.all().filter('content = ',context.kind())

    if group:
        star_portlets = star_portlets.filter('group = ',group)
        kind_portlets = kind_portlets.filter('group = ',group)

    results = []
    all_portlets = list(star_portlets) + list(kind_portlets)
    all_portlets.sort(lambda x,y: cmp(int(x.display_order), int(y.display_order)))
    #logging.info('***portlets2 (%s): %s' % (len(all_portlets),repr(all_portlets)))
    for portlet in all_portlets:
        if portlet.allowed(context,request):
            #logging.info('*Yep - Portlet %s allowed' % repr(portlet))
            results.append( portlet.resolve(context,request,notag))
    results = '\n'.join(results)
    
##    root.setcached(cache_key,results)

    #logging.info('***portlet results: %s' % repr(results))
    return results   

class FileTypeBlobProperty(db.BlobProperty):
    def validate(self,value):
        """Coerce values (except None) to self.data_type.

            Args:
              value: The value to be validated and coerced.

            Returns:
              The coerced and validated value.  It is guaranteed that this is
              either None or an instance of self.data_type; otherwise an exception
              is raised.

            Raises:
              BadValueError if the value could not be validated or coerced.
        """
        
        if value is not None and not isinstance(value, self.data_type):
          try:  
            value = value.file.read()
          except AttributeError:
            value = None
          
        value = super(FileTypeBlobProperty, self).validate(value)
          
        return value


class Reference(db.Model):

    """description"""

    implements(interfaces.IReference)


#===== BEGIN CUSTOM CODE HERE [after_implements] =====
#===== END CUSTOM CODE HERE [after_implements] =====

# Attributes

    src_id = db.StringProperty()
    target_id = db.StringProperty()
    reference_type = db.StringProperty()
    
    def __eq__(self,value):
        
        if self.__class__ == value.__class__:
            return self.key() == value.key()
        else:
            return False
    
    def __ne__(self,value):
        return not self.__eq__(value)
    
    def __hash__(self):
       
        return hash(str(self.key()))

class Base(db.Model):
    
    _template = "view.pt"
    
    name = db.StringProperty()
    title = db.StringProperty(default='')
    description = db.TextProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    

    def __get_name__(self):
        p= getattr(self,'_v_name',None)
        if p is None:
            val=getattr(self,'name',None)
            self._v_name = str(val)
            p = self._v_name 
        return p
    
    def __set_name__(self,name):
        setattr(self,'_v_name',name)
    
    __name__ = property(__get_name__,__set_name__)
    
    
    def __eq__(self,value):
        
        if self.__class__ == value.__class__:
            return self.key() == value.key()
        else:
            return False
    
    def __ne__(self,value):
        return not self.__eq__(value)
    
    def __hash__(self):
       
        return hash(str(self.key()))    
    
    @retry(Exception,tries=3,delay=0.5)   
    def __get_parent__(self):
        p= getattr(self,'_v_parent',None)
        if p is None:
            p=getattr(self,'parent_',None)
        return p
    
    def __set_parent__(self,parent):
        setattr(self,'_v_parent',parent)
        #setattr(self,'_v_parent',parent)
    
    __parent__ = property(__get_parent__,__set_parent__)
       
    @property
    def id(self):
        return self.__name__
   
    def session(self):
        return self._request().environ.get('beaker.session',None)
        
    def clearCache(self):
        """ """
        url = self.absolute_url(self._request())
        self.root.delcached(url.rstrip('/'))
        self.root.delcached(url+'view')
        
    def traverse(self,path):
        return find_model(self,unquote(path))
    
    def acquire(self,name):
        names = getattr(self,'contentNames',None)
        if names and name in names():
            return self[name]
        
        parent = self.getParent()
        if parent:
            return parent.acquire(name)
        
        return None
     
    def traverse_view(self,path,REQUEST=None):
        viewdef = traverse(self,path)
        if REQUEST is None:
            REQUEST=self._request()
        request = REQUEST
        #gsm = registry._registry
        #/gsm = zope.component.getSiteManager()
        try:
            reg = request.registry
        except AttributeError:
            reg = get_current_registry()

        context = viewdef['context']
        name = viewdef['view_name']
        provides = map(providedBy,(request,context))#BREAKPOINT()
        #view = gsm.getMultiAdapter((c,REQUEST),repoze.bfg.interfaces.IView,n)
        view = reg.adapters.lookup(provides,repoze.bfg.interfaces.IView,name=name)
        return view(context,request)

    def _request(self):
        return get_current_request()
        
    def absolute_url(self,request=None):
        if request is None:
            request = self._request()
        return model_url(self,request)
    
    def applyChanges(self,changes):

        names = []
        ispec = list(getObjectSpecification(self).interfaces())[0]
        for field,value in changes.items():
            
            if value is not None:
                setattr(self,field,value)
                names.append(field)
        if names:     
            if ispec:   
                description = [zope.lifecycleevent.Attributes(ispec, *names)]
                    # Send out a detailed object-modified event
                zope.event.notify(
                    zope.lifecycleevent.ObjectModifiedEvent(self, *description))
             
            if hasattr(self,'postApply'):
                self.postApply(changes) 
            
            self.put()
            
##            root = self.getRoot()
##            if root != self:
##                
##                root.setcached(str(self.key()),self)       
       
    def getPath(self):
        return model_path(self)
    
    def getRoot(self):

        return getRoot()
    
    root = property(getRoot)
    
    def getParent(self,trueParent=False):
        if not trueParent:
            if self.__parent__:
                return self.__parent__
        
        result = None
        result= getattr(self,'parent_',None) 
        return result 
    
    def getPathElements(self,trueParent=False):
        results = [self]
        parent = self.getParent(trueParent)
        while parent:
            results.append(parent)
            parent = parent.getParent(trueParent)             
    
        results.reverse()
        return results
    
    @property
    def path_elements(self):
        paths = [] 
        pe = self.getPathElements()
        for i in pe:
            paths.append(i.getPath())
        return paths
    
    def title_or_id(self):
        title = getattr(self,'title','')
        if not title or not title.strip():
            title = self.name
        return title
 
    
    def user(self):
        return users.get_current_user()
    
    def is_current_user_admin(self):
        return users.is_current_user_admin()
            
    def __repr__(self):
        if self.is_saved():
            
            return '<%s path="%s">' % (self.__class__.__name__,self.getPath())
        else:
            return '<%s path="%s">' % (self.__class__.__name__,'not saved')

    def template(self):
        return self._template
    
class MinimalTraversalMixin: 
    
    def __repr__(self):
        return """<%s key_name="%s"/>""" % (self.kind(),repr(self.key()))
       
    @property
    def __name__(self):
        return unicode(self.key())   
  
    def getPath(self):
        return model_path(self)
    
    def getRoot(self):
        return getRoot()
    
    root = property(getRoot)
    
    def getParent(self,trueParent=False):
        if trueParent:
            return None
        return self.__parent__  
    
    def absolute_url(self,request=None):
        if request is None:
            request = self._request()
        parent=self.getParent()
        url = "%s%s/" % (parent.absolute_url(request),str(self.key()))
        return url  

class NonContentishMixin(MinimalTraversalMixin,Base,HasActions):
    """ """
    implements(interfaces.INonContentish)
    
    
class PropertySheet(db.Expando,NonContentishMixin):
    """ provides entities for storing abitrary properties"""   
    
   
class ContentishMixin(Base,HasActions):
    
    implements(interfaces.IContentish)

    parent_ = db.ReferenceProperty(collection_name='children_')
    path_elements_ = db.StringListProperty(default=[])
    display_order = db.IntegerProperty(default=5)
    
    def setParent(self,obj):
        self.parent_ = obj
     
    
        
    
    def postApply(self,changes): 
        self.path_elements_ = self.path_elements
        
        
        
class FolderishMixin(db.Model):
    
    implements(interfaces.IFolderish)
    folderish = True
    
    children_keys = db.ListProperty(db.Key,default=[])
    children_names = db.StringListProperty(str,default=[])
    
    _template = "folder.pt"

    def clearCache(self):
        
        url = self.absolute_url(self._request())
        path = self.getPath().rstrip()
        self.root.delcached(url.rstrip('/'))
        self.root.delcached(url+"view")
        self.root.delcached(path+":summary")
        self.root.delcached(path+":links")
        
      
    def contentValues(self,REQUEST=None,kind=None):

        ct = []
        if kind and type(kind) == type(''):
            ct = [kind]
        elif kind:
            ct = kind
        
        if self.children_keys:
            results= [i for i in db.get( self.children_keys) if i != None]
            if ct:
                results= [i for i in results if i.kind() in ct]
            for i in results:
                try:
                    i.__parent__ = self
                except AttributeError:
                    logging.info('***could not set parent on %s' % repr(i))
            results.sort(lambda x,y: cmp(int(x.display_order), int(y.display_order)))
            
            return results
        else:
            return []
    
    def contentNames(self):
        
        return list(self.children_names)
    
    @retry(Exception,tries=3,delay=0.5)
    def _get(self,key):
        root = self.root
        kind = key.kind()
        result= root.models()[kind].get(key)
        
        return result
        
    def contentItems(self,REQUEST=None):
        
        for i in self.contentValues(REQUEST):            
            yield i.name,i
            
    def content_summary(self,REQUEST=None,limit=None,kind=None):
        
        results = []
        root = self.getRoot()
        request =None
        if REQUEST:
            request = REQUEST
        else:
            request = self._request()
            
            
        cache_key = str(self.absolute_url().rstrip('/'))+":summary"
        cached_result = root.getcached(cache_key)
       
        if cached_result and not getattr(request.principal,'ADMIN',False) :
            return cached_result 
        values = self.contentValues(request,kind=kind)
        
        if limit:
            values = values[0:min(limit,len(values))]
        
        for i in self.contentValues(request,kind=kind):
            url = i.absolute_url(request)
            title = i.title_or_id()
            description = i.description or ''
            summary={'name':i.name,'url':url,'title':title,
                'description':description,
                'kind':i.kind(),
                'hidden':getattr(i,'hidden',False),
                'modified': i.modified,
                'isfolder':interfaces.IFolderish.providedBy(i),
                'display_order': getattr(i,'display_order',5)}
            summary['heading_tab'] = getattr(i,'heading_tab',False)
            results.append(summary)
            
            if hasattr(i,'image_thumbnail'):
                summary['thumbnail']=i.thumb_tag()
            if hasattr(i,'image'):
                        summary['thumbnail']=url + 'mini'
        if not getattr(request.principal,'ADMIN',False):   
            root.setcached(cache_key,results)
            
        return results            
    
    def content_links(self,REQUEST):
        
        results = []
        root = self.getRoot()
        
        cache_key = str(self.getPath())+":links"
        cached_result = root.getcached(cache_key)
        
        if cached_result:
            return cached_result 
        
        for i in self.contentValues(REQUEST):
            url = i.absolute_url(REQUEST)
            title = i.title_or_id()
            
            link = '<a href="%s" title="%s">%s</a>' % (url,title,title)
            results.append(link)
            
        root.setcached(cache_key,results)
        return results 
    
    def addContent(self,obj,name,REQUEST):

        if name in self.contentNames():
            raise DuplicateName('duplicate name %s'%name)
        
        self.children_keys.append(obj.key())
        
        self.children_names.append(name)
        
        obj.put()
        # Can't set the parent until the object has been saved !! Need to check this again
        obj.setParent(self)
        obj.path_elements_ = self.path_elements
        obj.put()
        
        self.put()
        
        if REQUEST is not None:
            self.clearCache()
        
    def delContent(self,name,REQUEST):
        idx = self.children_names.index(name)
        obj = self[name]
        
        if isinstance(obj,FolderishMixin):
            
            for i in obj.contentNames():
                obj.delContent(i,REQUEST)
        
        name,key= self.popItem(idx)
        
        #self.save()
        if REQUEST:
            self.clearCache()
        
        obj.parent_ = None
        obj.delete()
        
        return obj
            
    def moveContent(self,idx_from,idx_to):
        
        name,obj = self.popItem(idx_from)
        self.children_names.insert(idx_to,name)
        self.children_keys.insert(idx_to,obj)
        self.put()
    
    def popItem(self,idx):
        
        obj = self.children_keys.pop(idx)
        name = self.children_names.pop(idx)
        self.put()
        return name,obj
    
    
    def __getitem__(self,name):
        #BREAKPOINT()
        name = unquote(unicode(name))
        
        if name in self.children_names:
            idx = self.children_names.index(name)
            result = self._get(self.children_keys[idx])
            result.__parent__ = self
            return result
        else:
            raise KeyError(name)
        
    def __contains__(self,name):
        if name in self.children_names:
            return True
        else:
            return False
    
    def __iter__(self):
        for i in self.contentValues():
            yield i
    
    #@property    
    #def __parent__(self):
    #    return self.parent_
        
     
class Root(FolderishMixin, ContentishMixin, HasActions):
    """ """
    
    __models = {}
    _v_cache = {}

    
    _template = "root.pt"
    
    implements( interfaces.IRoot)  
    
    site_title = db.StringProperty(default='')
    body = db.TextProperty()
    email=db.EmailProperty()
    thumbnail_size = db.ListProperty(int,default=[64,64])
    analytics_code=db.TextProperty()
    verification_code=db.TextProperty()
    copyright_statement = db.StringProperty(default='')
    
    
    parent_ = None
    environ = None
    
    
    def __repr__(self):
        return '<Root name="%s">' % self.name
    
    @property
    def settings(self):
        return settings
        
    @classmethod
    def kinds(cls):
        return cls.__models.keys()
    
    def get_model(self,type_name):
        return self.__models.get(type_name)
    
    def portlets(self,context,REQUEST,group=None):
        
        return getPortlets(context,REQUEST,group)
    
    def heading_tabs(self,REQUEST,group="admin"):
        
        cache_key = "heading_tabs"
        cached_result = self.getcached(cache_key)
        
        if cached_result:
            return cached_result 
        
        results = self.folder_tabs(REQUEST) + list(self.getActions(REQUEST,group='heading'))
        self.setcached(cache_key,results)
        return results    
    
    def folder_tabs(self,REQUEST):
        template = """<a href="%s" name="%s" title="%s">%s</a>"""
        result = []
        for i in Folder.all().filter('heading_tab = ',True).order('display_order'):
            result.append(template % (i.absolute_url(REQUEST),i.name,i.title_or_id(),i.title_or_id()))
        return result
    

    
    def logout_url(self,dest_url):
        return users.create_logout_url(dest_url)
    
##    def applyChanges(self,changes):
##        
##        names = []
##        ispec = list(getObjectSpecification(self).interfaces())[0]
##        for field,value in changes.items():
##            if value is not None:
##                setattr(self,field,value)
##                names.append(field)
##        if names:     
##            if ispec:   
##                description = [zope.lifecycleevent.Attributes(ispec, *names)]
##                    # Send out a detailed object-modified event
##                zope.event.notify(
##                    zope.lifecycleevent.ObjectModifiedEvent(self, *description)) 
##            
##            self.put()       
    
    
    def createContent(self,name,content_type,obj_location,REQUEST,**kwargs): 
        """ """
     
        if isinstance(content_type,basestring):
            klass = self.get_model(content_type)
        else:
            klass = content_type
            
        if type(obj_location) == str:   
            obj_location = find_model(self,obj_location)
           
        newobj = klass(name=name)
        newobj.put()
        # Hook content up to traveral machinery locations etc.. before
        # applying all the data
        if IContentish.providedBy(newobj):
            if obj_location:
                obj_location.addContent(newobj,name,REQUEST) 
                zope.event.notify(zope.lifecycleevent.ObjectCreatedEvent(self)) 
                self.setcached(str(obj_location.getPath()),None)
        elif isinstance(newobj,NonContentishMixin):
            newobj.__parent__ = obj_location    
            
        newobj.applyChanges(kwargs)
        newobj.put()
            
        return newobj   
     

    @classmethod
    def register_models(cls,model):
        if hasattr(model,'init_class'):
            model.init_class()
            
        kind = model.kind()
        
        if issubclass(model,polymodel.PolyModel):
            kind = model.class_name()    
        cls.__models[kind] = model    

    def filteredQuery(self,content_type,parent=None):
        root = self.getRoot()
        root.models()
        cls = root.get_model(content_type)
        filter = cls.all()
        if parent:
            filter = filter.filter('parent_ =',parent)
            
        return filter
    
    def getcached(self,key):
        
        return memcache.get(key)
    
    def _iterate_props(self,obj):
        results = []
        for i in dir(obj):
            results.append((i, type(getattr(obj,i))))
        return results
    
    def setcached(self,key,obj,timeout=36000):
        #BREAKPOINT()
        try:
            memcache.set(key,obj,timeout)
        except Exception,e:
            logging.warning('Failed to cache key "%s": %s, Exception: %s' % \
                                                 (repr(key),repr(obj),repr(e)))
        
    def delcached(self,key):
        
        memcache.set(key,None)
    
    def models(self):
       
        return self.__models
    
    @property
    def __name__(self):
        return ''   
    
    def getParent(self,trueParent=False):
        return None
    
    def dbGet(self,key):
        return db.get(key)
    
    def getPathElements(self,trueParent=False):
        return [self]
    
    def get_banner(self,context,request):
        """Get a dynamic piece of html representing a banner. this may for
           example be a style fragment with a random banner image string used
           as part of the main_template header.
        """
        ba = queryMultiAdapter((context,request), interfaces.IBanner)
        if not ba:
            return ''
        return ba()
    
    def get_context_portlets(self,context,request):
        """Get dynamic portlet replacements for a given context.
        """
        pa = queryMultiAdapter((context,request), interfaces.IPortletChange)
        if not pa:
            #logging.info('***No pa adapter for %s' % repr(context))
            return ''
        return pa()
    

class Action(ContentishMixin):
    """ """
    
    content_type = "action" 
    _template = "action.pt"
    
    
    implements(interfaces.IAction)
    
    label = db.StringProperty()
    expr = db.StringProperty()
    guard_expr = db.StringProperty()
    css_class = db.StringProperty(default='')
    group = db.StringProperty()
    content = db.StringListProperty(default=["*",])
    
    engine = Engine
    
    def allowed(self,context,request):

        if ( not (self.guard_expr is None)) and len(unicode(self.guard_expr)):
            container = context
            if context.kind() not in ['Folder','Root']:    
                container = context.getParent()
                
            ac = utils.ActionContext(request,{'context':context,'object':context,'container':container,'request':request})
            gexpr = self.engine.compile(self.guard_expr)
            return gexpr(ac)  
        else:
            
            return True
        

    def resolve(self, context, request, notag=False):
        
        container = context
        if context.kind() not in ['Folder','Root']:    
            container = context.getParent()
            
        ac = utils.ActionContext(request,{'context':context,'object':context,'request':request,'container':container})    
        expr = self.engine.compile(self.expr) 
        resolved_expr = None
              
        try:
            resolved_expr = expr(ac)
        except AttributeError:
            # Don't break on invalid expression.
            # Note: Change to log stack trace.
            logging.error('Broken expression on action "%s"' % self.name)
            if notag:
                return {}
            else:
                return ''
        if notag:
            result = {'class': self.css_class,
                      'href':resolved_expr,
                      'url':resolved_expr,
                      'name':self.name,
                      'label':self.label,
                      'title':self.title,
                      'display_order':self.display_order,
                      'description':self.description}
        else:
            result = """<a href="%(href)s" class="%(class)s" name="%(name)s" title="%(label)s">%(label)s</a>""" % {'class':self.css_class, 
                                      'href':resolved_expr,
                                      'name':self.name,
                                      'label':self.label}
        
        return result

class PortletContext(object):
    implements(interfaces.IPortletContext)
    
    def __init__(self,context,portlet):
        self.context = context
        self.portlet = portlet
    
    
class Portlet(Action):
    content_type = "portlet" 
    _template = "portlet.pt"
    
    portlet_template = db.StringProperty()
    
    implements(interfaces.IPortlet)

    def resolve(self, context, request, notag=False):
        
        #BREAKPOINT()
        
        container = context
        if context.kind() not in ['Folder','Root']:    
            container = context.getParent()
            
        ac = utils.ActionContext(request,{'context':context,'object':context,'request':request,'container':container})    
        expr = self.engine.compile(self.expr)       
        name = expr(ac)

        #gsm = zope.component.getSiteManager()
        try:
            reg = request.registry
        except AttributeError:
            reg = get_current_registry()
        pc = PortletContext(context,self)
        provides=map(zope.interface.providedBy,(request,pc))
        #objs = map(zope.interface.providedBy,(PortletContext(context,self),request))
        #result = zope.component.queryMultiAdapter((PortletContext(context,self),request),repoze.bfg.interfaces.IView,name)
        #result = reg.queryMultiAdapter((PortletContext(context,self),request),repoze.bfg.interfaces.IView)
        #result = reg.queryMultiAdapter((PortletContext(context,self),request),interfaces.IPortlet,name)
        #result = zope.component.queryMultiAdapter(objs,repoze.bfg.interfaces.IView,name)
        result = reg.adapters.lookup(provides,repoze.bfg.interfaces.IView,name=name)
        
        if result is None:
            result = ""
        else:
            result = result(pc,request)
        #logging.info('***resolved portlet (%s): %s - %s' % (name,type(result),repr(result)))
        return result


class File(ContentishMixin):
    """ """
    
    implements(interfaces.IFile)  
    _template = "file.pt"
   
   
    file = FileTypeBlobProperty(required=False)
    filename = db.StringProperty(default='')
    filesize = db.IntegerProperty(default=0)
    mimetype = db.StringProperty(default="application/octet-stream")
    custom_view = db.StringProperty(default=u'')
    
    def __init__(self,*args,**kwargs):
        
        super(File,self).__init__(*args,**kwargs)
                
    def __call__(self,request):
        
        return self.file
    
    def update_file(self,changes):
        
        self.filename = changes['file'].filename
        self.mimetype = changes['file'].mimetype
    
    def postApply(self,changes):  
        super(File,self).postApply(changes)      
        if changes.get('file',None):
            if changes['file'].file:
                self.update_file(changes)
    

    
class Image(File):
    """ """
    implements(interfaces.IImage) 
    _template = "image.pt"
     
    image_thumbnail = db.BlobProperty(required=False)
    image_size = db.StringProperty(default='0,0')
    thumbnail_size = db.StringProperty(default='0,0')
    
    def clearCached(self):
        super(Image,self).clearCached()
        url = self.absolute_url(self._request())
        self.root.delcached(url+"thumbnail")
        
    
    def postApply(self,changes):
        
        if changes.get('file',None):
            if changes['file'].file:
                self.update_file(changes)
                self.update_image()
    
    def update_image(self):
        
        image_type,width,height = getimageinfo.getImageInfo(self.file)
        self.mimetype = image_type
        self.image_size = '%d,%d' % (width,height)
        width,height = self.getRoot().thumbnail_size
        thumbnail = images.resize(self.file,width,height,images.JPEG)
        self.image_thumbnail = db.Blob(thumbnail)
        image_type,width,height = getimageinfo.getImageInfo(thumbnail)
        self.thumbnail_size = '%d,%d' % (width,height)
        

    def thumb_size(self):
        if self.thumbnail_size:
            width,height=self.thumbnail_size.split(',')
            return (int(width),int(height))
        else:
            return (0,0)
        
    def img_size(self):
        if self.image_size:
            width,height=self.image_size.split(',')
            return (int(width),int(height))
        else:
            return (0,0)


    def thumb_tag(self,css_class=""):
        return self.img_tag(css_class,thumbnail=True)

    def img_tag(self,css_class="",thumbnail=False):
        tag=""
        size=""
        
        if self.file:
            width,height=self.getRoot().thumbnail_size
            path = self.getPath()
            if not thumbnail:
                width,height = self.img_size()
                if int(width) and int(height):
                    size = 'width="%s" height="%s"' % (width,height)
            else:
                path = path + '/thumbnail'
                width,height = self.thumb_size()
                if int(width) and int(height):
                    size = 'width="%s" height="%s"' % (width,height)
                    
            tag = '<img src="%s" class="%s" alt="%s" %s>' % (path,css_class,self.title_or_id(),size)
        return tag 

class Page(ContentishMixin):
    """ """
    
    implements(interfaces.IPage)  
    _template = "page.pt"
    
    body = db.TextProperty()
    hidden = db.BooleanProperty(default=False)
    custom_view = db.StringProperty(default=u'')


class News(Page):
    """ A time based posting about the film """
    
    implements(interfaces.INews)
    _template = "news.pt"
    
    author = db.StringProperty(default='')
    news_date = db.DateProperty(auto_now_add=True)


class Folder(FolderishMixin,ContentishMixin):
    """ """ 
    
    implements(interfaces.IFolder)  
    _template = "folder.pt"
    
    hidden = db.BooleanProperty()
    default_content = db.StringProperty()
    custom_view = db.StringProperty(default=u'')
    heading_tab = db.BooleanProperty(default=False)
 
    def template(self):
        return self._template
 
    def __repr__(self):
        return '<Folder path="%s">' % self.getPath()

    
##    def __call__(self,REQUEST=None):
##        if self.default_content:
##            if  self.default_content in self.contentNames():
##                obj = self[self.default_content]
##                return obj(REQUEST)
##        
##        #return super(Folder,self).__call__(REQUEST)
    

class ResultAdapter(dict):
    """Wraps result sets"""
    def __init__(self,obj,dct):
        self._obj = obj
        super(ResultAdapter,self).__init__(dct)

    def __getattribute__(self,name):
        if name in self:
            return self[name]
        else:
            try:
                return super(ResultAdapter,self).__getattribute__(name)
            except AttributeError:
                return getattr(self._obj,name)

    def mediaBoxInfo(self):
        return {}

    
    
class StaticList(FolderishMixin,ContentishMixin):
    """ """
    zope.interface.implements(interfaces.IStaticListView) 
    _template = "query"    

    body = db.TextProperty(default=u'')
    hidden=db.BooleanProperty(default=False)
    reparent=db.BooleanProperty(default=False)
    list_items = db.TextProperty(default=u'')
    custom_view = db.StringProperty(default=u'')

    def template(self):
        if self.custom_view:
            return self.custom_view
        return super(StaticList,self).template() 

    
    def reparent_absolute_url(self,obj,request):
        url = "%s%s/" % (self.absolute_url(request),str(obj.key()))
        return url

    def resultwrapper(self,item):
        """Place holder method."""
        return ResultAdapter(self,dict())

    def content_summary(self,REQUEST=None,limit=None):
        
        results = []
        root = self.getRoot()
        request =None
        if REQUEST:
            request = REQUEST
        else:
            request = self._request()
            
            
        cache_key = str(self.absolute_url().rstrip('/'))+":summary"
        cached_result = root.getcached(cache_key)
       
        if cached_result and not getattr(request.principal,'ADMIN',False) :
            return cached_result 
        values = self.contentValues(request)
        
        if limit:
            values = values[0:min(limit,len(values))]
        
        for i in self.contentValues(request):
            if self.reparent:
                i.__parent__ = self
                i.__name__ = str(i.key())
                url = self.reparent_absolute_url(i,request)
            else:
                url = i.absolute_url(request)
            title = i.title_or_id()
            description = i.description or ''
            summary={'name':i.name,'url':url,'title':title,
                'key':str(i.key()),'description':description,
                'kind':i.kind(),
                'hidden':getattr(i,'hidden',False),
                'modified': i.modified,
                'isfolder':interfaces.IFolderish.providedBy(i)}
            summary['heading_tab'] = getattr(i,'heading_tab',False)
            results.append(summary)
            
            if hasattr(i,'image_thumbnail'):
                summary['thumbnail']=i.thumb_tag()
                
            
            if hasattr(i,'image'):
                summary['thumbnail']=url + 'mini'
        
        if not getattr(request.principal,'ADMIN',False):   
            root.setcached(cache_key,results)
            
        return results  

    def contentValues(self,REQUEST=None,kind=None):
        results=[]
        for i in self.list_items.split('\n'):
            try:
                method,key = i.strip().split(':',1)
            except ValueError:
                continue
            
            item = None
            
            try:
                
                if method=='key':
                   
                        item = self[key]
                        
                elif method=='path':
                     item = self.traverse(key)
                     
            except KeyError:
                    continue
                         
            if item:
                if isinstance(item,NonContentishMixin) or self.reparent:
                    try:
                        item.__parent__self
                        item.__name__ = str(item.key())
                    except AttributeError:
                        pass
                
                results.append(item)
        
        return results        

    def contentNames(self):
        return [i.key for i in self.contentValues()]   
        
    def __repr__(self):
        return '<StaticList path="%s">' % self.getPath()
    
    def __getitem__(self,name):
        
        root = self.getRoot()
        
        try:
            key = db.Key(name)
        except db.BadKeyError:
            raise KeyError
        
        
        cache_key = str(key)
        obj = root.getcached(cache_key)
        
        if not obj:
                         
            obj = db.get(name)
            root.setcached(cache_key,obj)
            
        
        if obj:
            if isinstance(obj,NonContentishMixin) or self.reparent:
                try:
                    obj.__parent__ = self
                    obj.__name__ = str(obj.key())
                except AttributeError:
                    pass
            return obj
        else:
            raise KeyError('Object not found')



class QueryView(FolderishMixin,ContentishMixin):
    """ """
    
    zope.interface.implements(interfaces.IQueryView) 
    _template = "query"
    body = db.TextProperty(default=u'')
    hidden=db.BooleanProperty(default=False)
    reparent=db.BooleanProperty(default=False)
    find_kind = db.StringProperty()
    filters = db.TextProperty(default=u'')
    order_by = db.TextProperty(default=u'')
    group_by = db.TextProperty(default=u'')
    custom_view = db.StringProperty(default=u'')
  
    def template(self):
        if self.custom_view:
            return self.custom_view
        return super(QueryView,self).template() 
  
    def delContent(self,key,request):
        
        obj = db.get(key)
        path = obj.getPath()
        self.getRoot().setcached(path,None)
        obj.delete()
        
    def reparent_absolute_url(self,obj,request):
        

        url = "%s%s/" % (self.absolute_url(request),str(obj.key()))
        return url
 
    
    def __getitem__(self,name):
        
        find_kind = self.find_kind.strip()
        root = self.getRoot()
        kind = root.get_model(find_kind)
        
        try:
            key = db.Key(name)
        except db.BadKeyError:
            raise KeyError
        
        if ( key.kind() != find_kind ):
            if issubclass(kind,polymodel.PolyModel):
                if kind.class_name() != find_kind:
                    raise KeyError('Entity key not valid for query (%s)' % find_kind) 
                
            else:
                raise KeyError('Entity key not valid for query (%s)' % find_kind)
        
        cache_key = str(key)
        obj = root.getcached(cache_key)
        
        if not obj:
            obj = db.get(name)
            root.setcached(cache_key,obj)
            
        if obj:
            if isinstance(obj,NonContentishMixin) or self.reparent:
                try:
                    obj.__parent__ = self
                    obj.__name__ = str(obj.key())
                except AttributeError:
                    pass
            return obj
        else:
            raise KeyError('Object not found')
        
    def content_summary(self,request,limit=None):
        results = []
        
        if not request: 
            request = self._request()
        
        root = self.getRoot()
        cache_key = str(self.absolute_url().rstrip())+":summary"
        cached_result = root.getcached(cache_key)
        
        if cached_result and not getattr(request.principal,'ADMIN',False) :
            if limit:
                cached_result = cached_result[0:min(len(cached_result),limit)]
            return cached_result 
        
        kind = root.get_model(self.find_kind)
        #BREAKPOINT()
        query = kind.all()
        if self.filters:
            for i in self.filters.split('\n'):
                if i:
                    lhs,rhs=i.split(',',1)
                    query=query.filter(lhs.strip(),eval(rhs.strip()))
            
        if self.order_by:
            for i in self.order_by.split('\n'):
               
                if i:
                    query = query.order(i.strip())
        
        for i in query:
            summary = {}
            #BREAKPOINT()
            if isinstance(i,NonContentishMixin) or self.reparent:
                i.__name__ = str(i.key())
                i.__parent__ = self
            summary['key']=str(i.key())
            if not getattr(i,'hidden',False):
                url = ""
                if self.reparent:
                    url = self.reparent_absolute_url(i,request)
                else:    
                    url = i.absolute_url(request)
                
                if hasattr(i,'item_summary'):
                    summary = i.item_summary()
                    summary['url']=url
                else:
                    try:
                        title = i.title_or_id()
                    except AttributeError:
                        title = i.key()
                        
                    description = getattr(i,'description','')
                    name = getattr(i,'name',i.key())
                    summary={'name':name,'url':url,'title':title,'description':description,'kind':i.kind(),'key':i.key()}
                    
                    if hasattr(i,'image_thumbnail'):
                        summary['thumbnail']=url + 'thumbnail'
                    
                    if hasattr(i,'image'):
                        summary['thumbnail']=url + 'mini'
                
                results.append(summary)
        
        if not getattr(request.principal,'ADMIN',False):   
            root.setcached(cache_key,results)
              
        root.setcached(cache_key,results)
        
        if limit:
            results = results[0:min(len(results),limit)]
        return results    
    
    def groupby(self,results):
        #BREAKPOINT()
        groupby_keys = [i.strip() for i in self.group_by.split('\n') if i.strip()]
        if not groupby_keys:
            groupby_keys = ['Kind',]
        
        def makekeyfunc(groupkeys):
            def groupkey(item):
                return tuple([item[i] for i in groupkeys])
            return groupkey
        
        return groupby(results,makekeyfunc(groupby_keys))            
         
            
    def groupit(self,results):
        gresults = []#BREAKPOINT()
        for name,i in self.groupby(results):
            gresults.append({'name':name,'group':[]})#print name
            n = 0
            for i1 in i:
                if n == 0:
                    gresults[-1]['item'] = i1
                gresults[-1]['group'].append(i1)
                n=n+1
        return gresults
                
                        
##    def __call__(self,request=None):
##        template = self._template
##        if self.custom_view:
##            template = self.custom_view
##        
##        output = render_template(template,
##                                request = request,
##                                context =self)    
    
    
class PicassaGallery(Page):
    """ """
    
    zope.interface.implements(interfaces.IPicassaGallery)
    _template = "gallery.pt"
     
    gallery = db.LinkProperty(default=u'http://null')
    slides = db.ListProperty(str,default=[])
    resolved_gallery = db.TextProperty()
    
    gallery_template = db.TextProperty(required=False,default="")
    
    default_template = """<div class="thumbnail" style="margin-right: 10px;margin-bottom: 10px;">
		<a href="%s?imgmax=800" class="visualIconPadding" rel="lightbox[photo-gallery]" title="%s">
         <img src="%s" alt="%s" title="%s" height="%s" width="%s" border="0">
         </a><div style="margin:0px;padding:0px;">%s</div>
     </div>
    
"""
    
    
    def update_elements(self):
        
        """ Update the slide elements"""
        
        if self.gallery != 'http://null':
            result = urlfetch.fetch(self.gallery)
            if result.status_code == 200:
                #BREAKPOINT()
                self.resolved_gallery = self.unpick_rss(result)
                self.put()
           
            
        
    def unpick_rss(self,rss):
        
        prefix = "{http://search.yahoo.com/mrss/}"
        et = ElementTree.fromstring(rss.content)
        groups = et.findall(".//%sgroup"%prefix)
        results = []
        template = self.gallery_template.strip()
        
        if not template:
            template = self.default_template
            
        for i in groups:
            title= i.find("%stitle"% prefix).text
            description= i.find("%sdescription"%prefix)
            if description.text in [None,'None']:
                description.text = ''
            thumbnail= i.findall("%sthumbnail"%prefix)[1]
            content= i.find("%scontent"%prefix)
            #BREAKPOINT()
            args = (content.attrib['url'],
                description.text,
                thumbnail.attrib['url'].replace('/s144/','/s160-c/'),
                description.text,
                description.text,
                '160',
                '160',
                description.text)
            results.append(template % args)
            
        return '\n'.join(results)         

Root.register_models(Root)
Root.register_models(Folder)
Root.register_models(Page)
Root.register_models(News)
Root.register_models(File)
Root.register_models(Image)
Root.register_models(Action)
Root.register_models(Portlet)
Root.register_models(StaticList)
Root.register_models(QueryView)
Root.register_models(PicassaGallery)
Root.register_models(PropertySheet)

def getRoot(environ=None,cache=True):
    
    root = None
    
    root= Root.all().get()
    if root:    
        root.environ = environ      
    else:
        root = Root()   
    
    return root


class DBKeys(object):
    
    def __init__(self,objs):
        self.objs = objs
        
    def __iter__(self):
        for obj in self.objs:
            x = obj.all().filter('name',obj.name)
            for x1 in x:
                yield x1.key()
    
