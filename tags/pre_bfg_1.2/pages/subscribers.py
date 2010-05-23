from zope.interface import alsoProvides
from zope.interface import Interface

from google.appengine.api import users
from google.appengine.api import memcache


from repoze.bfg.traversal import model_path, find_model, find_root

import models
import interfaces

def annotate_request(event):
    request = event.request
    user = users.get_current_user()
    
    if not user:
        user = users.User('anonymous')
        
    if users.is_current_user_admin():
        setattr(user,'ADMIN',True)
        
    setattr(request,'principal',user)
    
def init_session(event):
    """Subscriber hook to initialise/manipulate the session on a new request.
    """
    request = event.request
    session = request.environ.get('beaker.session',None)
    if session:
        user = users.get_current_user()
        if users.is_current_user_admin():
            # Initialise/reset cache_info
            session['cache_info'] = dict()
            session.save()
    
def manage_cache(event):
    if not event.object.is_saved():
        return
    
    root =event.object.getRoot()
    
    if interfaces.IAction.providedBy(event.object):
        memcache.flush_all()
   
    if not interfaces.IFolder.providedBy(event.object):
        root.delcached('%s:summary' % event.object.getParent().getPath())
    
    if interfaces.IPicassaGallery.providedBy(event.object):
        
        event.object.update_elements()
