
from google.appengine.ext import gql,db
from pages import models
import copy
from pages.models import DBKeys
data = [

(models.Root,( {
    'title':"Testing repoze-bfg-gae",
    'description':"""""",
    'email':'me@somewhere.com',
    'default_image':'default.jpg',
    'site_email':'me@somewhere.com',
    'name':'home',
    'picasa_user':'',
    },),   "ROOT" ,[],lambda x: not list(models.Root.all())
),

(models.Folder, [
          {'name':'news','key_name':'news','parent_':'/','display_order':15}, 
          #{'name':'galleries','key_name':'galleries','parent_':'/','display_order':9}, 
          {'name':'actions','key_name':'actions','parent_':'/','display_order':99},
          #{'name':'portlets','key_name':'portlets','parent_':'/','display_order':99}
        ] , "FOLDERS",[],lambda x: not list(models.Folder.all()),
),
          
(models.Action,[{ 'name':'view_', 'label':'View','parent_':'/actions',
                    'expr':"python: context.absolute_url(request)+'view'",
                    'guard_expr':'python: 1',
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                    
                { 'name':'fcontents_', 'label':'Contents','parent_':'/actions',
                    'expr':"python: context.absolute_url(request)+'contents'",
                    'guard_expr':"python: hasattr(context,'contentValues') ",
                    'group':'admin','class':'yuimenuitemlabel'
                    }, 
                    
                { 'name':'pcontents_', 'label':'Contents','parent_':'/actions',
                    'expr':"python: context.getParent().absolute_url(request)+'contents'",
                    'guard_expr':"python: not hasattr(context,'contentValues') ",
                    'group':'admin','class':'yuimenuitemlabel'
                    },     
                       
                { 'name':'edit_', 'label':'Edit',
                    'expr':"python: context.absolute_url(request)+'edit'",'parent_':'/actions',
                    'guard_expr':'',
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                    
                { 'name':'delete_', 'label':'Delete',
                    'expr':"python: '%sdelete_content?name=%s' % (context.getParent().absolute_url(request),context.id)",
                    'parent_':'/actions',
                    'guard_expr':"python: context != context.getRoot()",
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                    
                { 'name':'add_page_', 'label':'Add Page',
                    'expr':"python: context.absolute_url(request)+'add?content=Page'",
                    'parent_':'/actions',
                    'guard_expr':'python: context != context.getRoot()','content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                    
                { 'name':'add_folder_', 'label':'Add Folder',
                    'expr':"python: context.absolute_url(request)+'add?content=Folder'",
                    'parent_':'/actions',
                    'guard_expr':'python: context != context.getRoot()','content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                     
                { 'name':'add_news_', 'label':'Add News',
                    'expr':"python: context.absolute_url(request)+'add?content=News'",
                    'parent_':'/actions',
                    'guard_expr':'python: context != context.getRoot()','content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                { 'name':'add_file_', 'label':'Add File',
                    'expr':"python: context.absolute_url(request)+'add?content=File'",
                    'parent_':'/actions',
                    'guard_expr':'python: context != context.getRoot()','content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                { 'name':'add_image_', 'label':'Add Image',
                    'expr':"python: context.absolute_url(request)+'add?content=Image'",
                    'parent_':'/actions',
                    'guard_expr':'python: context != context.getRoot()','content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                   
                { 'name':'add_actions_', 'label':'Add Action',
                    'expr':"python: context.absolute_url(request)+'add?content=Action'",
                    'parent_':'/actions',
                    'guard_expr':"python: context.name == 'actions'",'content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                { 'name':'add_portets_', 'label':'Add Portlet',
                    'expr':"python: context.absolute_url(request)+'add?content=Portlet'",
                    'parent_':'/actions',
                    'guard_expr':"python: context.name == 'portlets'",'content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },    
                { 'name':'add_query_', 'label':'Add Query',
                    'expr':"python: context.absolute_url(request)+'add?content=QueryView'",
                    'parent_':'/actions',
                    'guard_expr':"python: 1",'content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                { 'name':'add_gallery_', 'label':'Add Gallery',
                    'expr':"python: context.absolute_url(request)+'add?content=PicassaGallery'",
                    'parent_':'/actions',
                    'guard_expr':"python: 1",'content':['Folder',],
                    'group':'admin','class':'yuimenuitemlabel'
                    },
                    
                { 'name':'logout_', 'label':'Logout',
                    'expr':"python: context.getRoot().logout_url(context.absolute_url(request))",
                    'parent_':'/actions',
                    'guard_expr':"python:1",
                    'group':'admin','class':'yuimenuitemlabel'
                    },
              
                
               ],"ACTIONS",[],lambda x: not list(models.Action.all()),
        ),


]


