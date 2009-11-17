# Repoze BFG bindings

from webob import Response

from repoze.bfg.path import caller_path
from GAEPageTemplateFile import get_template

from gae.utils import BREAKPOINT
    
load_template = get_template


def get_template(path):
    """ Return a zope.pagetemplate template object at the package-relative path
    (may also be absolute) """
    
    return load_template(path)

def render_template(path, **kw):
    """ Render a zope.pagetemplate (ZPT) template at the package-relative path
    (may also be absolute) using the kwargs in ``*kw`` as top-level
    names and return a string. """
    
    template = get_template(path)
    return template.render(*[],**kw)

def render_template_to_response(path, **kw):
    """ Render a zope.pagetemplate (ZPT) template at the package-relative path
    (may also be absolute) using the kwargs in ``*kw`` as top-level
    names and return a Response object. """
    
    result = render_template(path, **kw)
    return Response(result)

