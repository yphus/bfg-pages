import os.path

import zope.component

from webob import Response
from google.appengine.api import memcache
from google.appengine.api import images

from gae.pagetemplate import render_template_to_response, render_template, TemplateDoesNotExist
from gae.utils import admin_required, BREAKPOINT
from gae.utils import Redirect,admin_required

from repoze.bfg.interfaces import IGETRequest,IPOSTRequest
from zope.configuration.xmlconfig import xmlconfig

import interfaces
import models
from utils import cacheoutput
from pages.utils import make_time_header
import pages

@admin_required
def setup_view(context, request):
    data = setup.start_setup(request)
    return render_template_to_response('setup.pt',
                                       request = request,
                                       context = context,
                                       project = 'test1',
                                       data = data,)
                                       

@admin_required
def add_view(context, request):
        
        import formish
        import schemaish
        import schema
        
        root = context.getRoot()
        kind = request.GET['content']
        new_cls = root.get_model(kind)
        fake_obj = new_cls()
        structure = zope.component.getAdapter(fake_obj,schema.IStructure)
        form = formish.Form(structure,name='form')
        applyWidgets(structure,form,context,request,ignore_readonly=True)

        defaults = schema.load_defaults(fake_obj,structure)
        form.defaults = defaults
        if IGETRequest.providedBy(request):
            pass
        elif IPOSTRequest.providedBy(request):
            try:
                changes = form.validate(request)
                name = changes.pop('name')
                new_obj = root.createContent(name,kind,context,request,**changes)
                return Redirect(new_obj.absolute_url(request)+'view')
            except formish.validation.FormError,e:
                pass
        else:
            """ An error, so redirect to error page"""
            pass 
        
        return render_template_to_response('base_add.pt',
                                           request = request,
                                           context = context,
                                           project = 'test1',
                                           form=form)                                                               

def call_callable(name,arg,field,context,request):
    if not callable(arg):
        return arg
    else:
        return arg(field,context,request)


def applyWidgets(structure,form,context,request,ignore_readonly=False):
    
    if hasattr(structure,'_widgets'):
        
        for field,widgetdef in structure._widgets.items():
            args = []
            kwargs = {}
            if 'args' in widgetdef:
                args=[callable(i) and i(field,context,request) or i for i in widgetdef['args']]
            if 'kwargs' in widgetdef:
            
                kwargs = dict([(name,call_callable(name,arg,field,context,request)) for name,arg in widgetdef['kwargs'].items()])
                    
            form[field].widget = widgetdef['widget'](*args,**kwargs)
            
    if not ignore_readonly:
        
        for field_name, field_def in form.structure.attrs:
            if getattr(field_def,'readonly',False):
                form[field_name].widget.readonly = True

@admin_required
def edit_view(context, request):
    
    import formish
    import schemaish
    import schema
    
    structure = zope.component.getAdapter(context,schema.IStructure)
    form = formish.Form(structure,name='form')
    
    applyWidgets(structure,form,context,request)

    defaults = schema.load_defaults(context,structure)
    form.defaults = defaults
    
    if IGETRequest.providedBy(request):
        pass
    elif IPOSTRequest.providedBy(request):
        try:

            changes = form.validate(request)
            
            # Edit forms that don't include the a new file upload
            # end up with a schemaish.type.File which has no file 
            # this causes problems later. So set it to None that
            # way the field won't get updated.
            # Need to find an alternate marker, as values deleted also 
            # end up as None
            for key in changes:
                if isinstance(changes[key],schemaish.type.File):
                    if changes[key].file is None:
                        changes[key] = None
                        
            context.applyChanges(changes)
            context.clearCache()
            
            return Redirect(context.absolute_url(request)+'view')
        
        except formish.validation.FormError,e:
            pass
    else:
        """ An error, so redirect to error page"""
        pass 
    
    return render_template_to_response('base_edit.pt',
                                       request = request,
                                       context = context,
                                       project = 'test1',
                                       form=form)    
@cacheoutput                                       
def root_view(context, request):
    
    return render_template_to_response('index.pt',
                                       request = request,
                                       context = context,
                                       )
@admin_required
def contents(context, request):
    
    return render_template_to_response('contents.pt',
                                       request = request,
                                       context = context,
                                       )
                                       
                                       
@cacheoutput                                        
def content_view(context, request):
    return render_template_to_response(context.template(),
                                   request = request,
                                   context = context)
  
@cacheoutput                                                                                   
def folder_view(context, request):
 
    template = context.template()
    
    if context.custom_view:
        template = context.custom_view
        
    default_content = None
    result = ""
    alt_body = ""
    
    if context.default_content and context.default_content in context.contentNames():
        default_content=context[context.default_content]
        alt_body  = render_template('replaceable_body.pt',
                                       request = request,
                                       context = default_content,
                                       template_name = default_content.template()
                                       )
        
    result = render_template_to_response(template,
                                       request = request,
                                       context = context,
                                       alt_body = alt_body
                                       )
    
    return result                                                                          
                                       
@cacheoutput 
def query_view(context, request):
    template = context._template
    if context.custom_view:
        template = context.custom_view
    
    try:
        return render_template_to_response(template,
                                       request = request,
                                       context = context,
                                       ) 
    except TemplateDoesNotExist:
        return render_template_to_response(context._template,
                                       request = request,
                                       context = context,
                                       ) 
                
@admin_required
def query_contents_view(context, request):
    
    return render_template_to_response('query_contents.pt',
                                       request = request,
                                       context = context,
                                       )


def sitemap_view(context, request):
    
    return render_template_to_response('sitemap.pt',
                                       request = request,
                                       context = context,
                                       )
                                                                              

@cacheoutput                                    
def download(context, request):

    resp =  Response(str(context(request)),content_type = str(context.mimetype))
    resp.expires = make_time_header(add=30)
    return resp   

@cacheoutput 
def image_thumbnail(context, request):

    resp =  Response(str(context.image_thumbnail),content_type = 'image/jpeg')
    resp.expires = make_time_header(add=30)
    return resp  

def fileupload_cache_view(context, request):
    """{'file':file_contents,
            'cache_tag':cache_tag,
            'content_type':content_type,
            'headers':headers }"""
    
    import schema        
    store = schema.MemcacheFileStore(None,context,request)
    
    if request.path_info_peek() == '@tmp':
        request.path_info_pop()
        key = request.path_info_pop()
        tag, content_type, image_data = store.get(key)
        
        image_data = image_data.read()
        if 'size' in request.GET:
            width,height=request.GET['size'].split('x')
            image_data = images.resize(image_data,width=int(width),height=int(height))
            content_type = 'image/png'
        resp = Response(image_data,content_type = content_type)
        return resp                                 
                                   
@admin_required                                   
def delete_content(context, request):
    
    try:
        name = request.GET['name']
        
        if name:
            context.delContent(name,request)
    except KeyError:
        key = request.GET['key']
        if key:
            context.delContent(key,request)
            
    return Redirect(context.absolute_url(request))      



@admin_required
def backup(context,REQUEST):
    """ backup models
        OLD CODE probably doesn't work at the moment"""

    results = []
    root = context.getRoot()
    models = self.models()

    kind= REQUEST.form.get('kind',None)
    start = int(REQUEST.form.get('start',-1))
    length = int(REQUEST.form.get('end',-1))
    name =  REQUEST.form.get('name',None)
    
    if kind in models:
        items = []
        if start > -1 and length > 1:
            items = models[kind].all()[start:length]
        elif start > -1:
            items = models[kind].all()[start:]
        elif name:
            items = models[kind].all().filter('name = ',name)
        else:
            items = models[kind].all()

        for obj in items:
            result = {}
            parent = None

            try:
                parent = obj.parent_
            except:
                pass
            if parent:
                
                result['parent_'] = parent.getPath()
            for prop in obj.properties().items():
                if prop[0].startswith('_'):
                    continue
                
                if prop[0] in ['slides','resolved_gallery','template']:
                    continue
                if prop[0] == 'parent_':
                    continue
                propval = getattr(obj,prop[0])
                if propval is None:
                    continue
                
                if isinstance(prop[1],db.ListProperty):
                    if not propval:
                        continue
                    proplist = []
                    
                    for i in propval:
                        try:
                            obb = db.get(i)
                            proplist.append('models.%s(name="%s")' % (obb.kind(),obb.name))
                            propval = 'DBKeys(['+','.join((proplist))+'])'
                        except db.BadKeyError:
                            proplist.append(repr(propval))
                            break
                    
                if isinstance(prop[1],db.ReferenceProperty):
                    propval = '%s(name="%s")' % (propval.kind(),propval.name)
                    
                result[prop[0]] = propval
            results.append(repr(result))
    
    return 'data = (models.%s, (%s),)' % (kind,',\n'.join(results))                                    