from zope.interface import Interface


class IStructure(Interface):
    """Formish interface marker"""
    
 
class IContent(Interface):
    """ Content objects"""
    
class IFolderish(Interface):
    """ Objects that are folderish"""

class IContentish(Interface):
    """Base for all content types that support containment and traversal"""
    
 
class INonContentish(Interface):
    """ Content that doesn't have a true folder heirarchy - ie non 
    explicit parent"""
     
class IReference(Interface):
    """ Marker interface""" 

class INews(IContentish):
    
    """News content"""


class IFolder(IContentish):   
     
    """Folder entities"""


      
class IRoot(IFolder):

    """Root"""

class IFile(IContentish):
    """File like"""
    
class IImage(IFile):
    """Image object"""
        
    
class IPage(IContentish):
    """Page"""

        
class IAction(IContentish):
    
    """Action"""

class IPortlet(IAction):
    
    """Viewlet"""
class IPortletContext(Interface):
    """ portlet context """        
          
class IStaticListView(IContentish):
    """ list of items defined by a static list of keys or paths"""
    
class IQueryView(IContentish):
    """Query entity"""
        
class IPicassaGallery(IContentish):
    """Gallery"""
   

class IBanner(Interface):
    """Marker for dynamic html to display a banner.
    """
               
