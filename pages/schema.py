
import uuid
import copy

import schemaish
from schemaish.type import File as SchemaFile
import formish
import validatish

import zope.interface
from zope.component import provideUtility,adapts
from zope.interface import implements

from google.appengine.api import memcache
from StringIO import StringIO

import pages
from pages import interfaces
from pages.interfaces import IStructure

from gae.utils import BREAKPOINT


def makeSchemaFile(context,key): 
    """ Factory to make SchemaFile objects for formish file store"""
    data = getattr(context,key)
    file_data = StringIO(data)
    file_name = context.filename
    mime_type = context.mimetype    
    store = MemcacheFileStore(None,context,None)
    store.put(context.filename, StringIO(data), uuid.uuid4().hex,{'Content-Type':mime_type})
    return SchemaFile(file_data,file_name,mime_type)
    

type_converters = {
    'File': makeSchemaFile
}


def load_defaults(context,structure):
    defaults = {}
    
    for key,field_def in structure.attrs:
        if field_def.type in type_converters:
            defaults[key] = type_converters[field_def.type](context,key)
        else:
            defaults[key] = getattr(context,key)

    return defaults


class MemcacheFileStore(object):
    
    def __init__(self,field,context,request,prefix='_fileupload_widget',timeout=3600):
        """field, context, request are being passed to __init__ 
        because be default all callables in the _widget dict
        in the schema declarations are sent these args"""
        self.prefix = prefix
        self.timeout = timeout
        
    def put(self, key, src, cache_tag, headers=None):
        
        file_contents=src.read()
        memcache.set('%s.%s' % (self.prefix,key),{'file':file_contents,
            'cache_tag':cache_tag,
            'headers':headers },time=self.timeout)
    
    def get(self, key, cache_tag=None):

        cached_file = memcache.get('%s.%s' % (self.prefix,key))
        if cached_file:
            if cache_tag and cached_file['cache_tag'] == cache_tag:
                return (cache_tag, None, None)
            return (cached_file['cache_tag'], cached_file['headers'], StringIO(cached_file['file']))
        else:
            return (None,None,None)
        
    def delete(self, key, glob=False):
        
        memcache.delete('%s.%s' % (self.prefix,key))



class BaseStructure(schemaish.Structure):
    
    def __init__(self,context,*args,**kw):
        self.__context = context
        super(BaseStructure,self).__init__(*args,**kw)
        self.title=''
        
    name = schemaish.String(validator=validatish.Required())
    name.readonly = True
    
    title = schemaish.String()
    description = schemaish.String()
    display_order = schemaish.Integer()
    
    _widgets = {
        'description':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},
            },
       
        }
        
def list_contents(field,context,request):
    contents= [i for i in context.contentNames()]
    contents.insert(0,'-- no content --')
    return contents        

class FolderStructure(BaseStructure):
    
    hidden = schemaish.Boolean()
    default_content = schemaish.String()
    heading_tab = schemaish.Boolean()
    custom_view = schemaish.String()
    _widgets = copy.copy(BaseStructure._widgets)
    _widgets.update( 
        {'default_content':{'widget':formish.SelectChoice,
            'kwargs':{ 
                'options':list_contents
                },
            },
         'hidden':{
                'widget':formish.Checkbox
            },
         'heading_tab':{
                'widget':formish.Checkbox
            }
        }
    ) 
    
class PageStructure(BaseStructure):
    
    body = schemaish.String()
    hidden = schemaish.Boolean()   
    _widgets = copy.copy(BaseStructure._widgets)
    _widgets.update( 
        {'body':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':25,'empty':''},},
        'hidden':{
                'widget':formish.Checkbox
            },
        }
    )
            
            
class NewsStructure(PageStructure):
    
    author = schemaish.String()
    news_date = schemaish.Date()
    
    _widgets = copy.copy(PageStructure._widgets) 
    
    _widgets.update({'news_date':{'widget':formish.DateParts,}})         
  
class FileStructure(BaseStructure):
   
    file = schemaish.File()
 
    _widgets = copy.copy(BaseStructure._widgets)
    _widgets.update( 
        {'file':{'widget':formish.FileUpload,'args':[MemcacheFileStore,],
            'kwargs':{'show_download_link':False,
                    'url_base':''}}
        }
    )
    
class ImageStructure(FileStructure):
    
    _widgets = copy.copy(FileStructure._widgets)
    _widgets['file']['kwargs']['show_image_thumbnail']=True

def list_content_types(field,context,request):
    
    contents= [i for i in context.getRoot().models().keys()]
    contents.append('*')
    return contents

def list_query_types(field,context,request):
    
    contents= [i for i in context.getRoot().models().keys()]
    return contents



class ActionStructure(BaseStructure):
    
    label = schemaish.String()
    expr = schemaish.String()
    guard_expr = schemaish.String()
    css_class = schemaish.String()
    group = schemaish.String()
    content = schemaish.Sequence(schemaish.String())
    
    _widgets = copy.copy(BaseStructure._widgets)
    _widgets.update( 
        {'content':{'widget':formish.CheckboxMultiChoice,
            'kwargs':{ 
                'options':list_content_types,
                
                },
            }
        }
    )

class PortletStructure(ActionStructure):
    
    portlet_template = schemaish.String()
    _widgets = copy.copy(ActionStructure._widgets)
    

class QueryViewStructure(BaseStructure):
    
    find_kind = schemaish.String(validator=validatish.Required())
    body = schemaish.String()
    hidden = schemaish.Boolean()
    reparent = schemaish.Boolean()
    filters = schemaish.String()
    order_by = schemaish.String()
    group_by = schemaish.String()
    custom_view = schemaish.String()
    
    _widgets = copy.copy(BaseStructure._widgets)
    _widgets.update( 
        {'body':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':25,'empty':''},},
         'hidden': {'widget':formish.Checkbox},
         'reparent': {'widget':formish.Checkbox},
         'filters':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},},
         'order_by':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},},
         'group_by':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},},
         'find_kind':{'widget':formish.SelectChoice,
            'kwargs':{ 
                'options':list_query_types,
                
                },
            }
        }
    )    
        
class PicassaGalleryStructure(PageStructure):
    
    gallery_template =  schemaish.String()      
    gallery = schemaish.String(validator=validatish.Required())
    
    _widgets = copy.copy(PageStructure._widgets)
    _widgets.update( 
        {'filters':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},},
        }
    )

class RootStructure(schemaish.Structure):
    
    def __init__(self,context,*args,**kw):
        self.__context = context
        super(RootStructure,self).__init__(*args,**kw)
        
    name = schemaish.String()
    title = schemaish.String()
    description = schemaish.String()
    site_title = schemaish.String()
    body = schemaish.String()
    email = schemaish.String()
    analytics_code = schemaish.String()
    verification_code = schemaish.String()
    copyright_statement = schemaish.String()
    thumbnail_size = schemaish.Sequence(schemaish.Integer())
    
    _widgets = {
        'description':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},
            },
            
        'body':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':15,'empty':''},
            },
            
        'analytics_code':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},
            },
            
        'verification_code':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':80,'rows':5,'empty':''},
            },
        'thumbnail_size':{'widget':formish.TextArea,
            'args':[],
            'kwargs':{'cols':10,'rows':3,'empty':''},
            },
        }
    
    