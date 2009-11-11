"""
GAE Page Templates

Adapted from DJango PageTemplates but removing all of the Django specific stuff
"""


import logging
logging.getLogger().setLevel(logging.DEBUG)
from os import getcwd 
from os.path import join, isfile, isabs, basename, dirname

from engine import Engine

from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from repoze.bfg.threadlocal import get_current_request
from gae import utils
TEMPLATE_DIRS = utils.settings['template_path']

# Module level cach for loaded page templates
# PageTemplateFiles refresh from disk automatically.

_cache = {}

class TemplateDoesNotExist(Exception):
    pass

# The factory method, aka "template loader".
def get_template(template_name):
    
    """Returns a GAEPageTemplateFile object."""
    request = get_current_request()
    cache_key = "%s:%s" % (getattr(request,'SKIN_NAME','default'),template_name)
    t = _cache.get(cache_key,None)
    logging.debug('get_template %s'%cache_key)
    if t is None:
        t = GAEPageTemplateFile(template_name)
        _cache[cache_key] = t
    return t
    
class Context(object):
    def __init__(self,req,d=[]):
        self.dicts = d
        self.request = req
        
class GAEPageTemplateFile(PageTemplateFile):
    """A PageTemplateFile that can be rendered with a repoze context"""

    def __init__(self, filename):
        if not isabs(filename):
            filename = findtemplate(filename)
        
        super(GAEPageTemplateFile,self).__init__(filename)

    def render(self,*args, **kwargs):

        kwargs['template_path'] = MacroLoader()
        kwargs['loadmacro'] = loadmacro
        return super(GAEPageTemplateFile,self).__call__(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        
        kwargs['context']=self    
        kwargs['template_path'] = MacroLoader()
        kwargs['loadmacro'] = loadmacro
        return self.pt_render(self.pt_getContext(*args, **kwargs))

    def pt_getContext(self, args=(), options={}, **ignored):
        # Make all keyword arguments to __call__() available in the
        # top-level namespace. As per zope.pagetemplate.readme.txt.
        options.update(super(GAEPageTemplateFile,self).pt_getContext(args))
        return options

    def pt_getEngine(self):
        # Return custom TALES engine
        return Engine


def findtemplate(template_name, _ext='.pt'):
    """Locates a template on template path."""
    request = get_current_request()
    template_dirs = getattr(request,'SKIN_PATH',TEMPLATE_DIRS)
    
    if not template_name.endswith(_ext):
        template_name += _ext
    template_name = template_name.split('/')
    tried = []
    curdir = getcwd()    
    for dir in template_dirs:
        filepath = join(curdir,dir, *template_name)
        if isfile(filepath):
            logging.debug('Found template %s' % filepath)
            return filepath
        else:
            tried.append(filepath)
    if template_dirs:
        error_msg = "Tried %s" % tried
    else:
        error_msg = "Your TEMPLATE_DIRS setting is empty. Change it to point to at least one template directory."
    raise TemplateDoesNotExist, error_msg


def loadmacro(template_name, macro_name):
    """Loads a macro from a GAEPageTemplate."""

    t = get_template(template_name)
    logging.debug('loading macro %s from %s' % (macro_name,t.filename))
    if t.macros is None or t._v_errors:
        error_msg = "Template '%s' is broken. %s" % (template_name, t.pt_errors({}))
    else:
        m = t.macros.get(macro_name)
        if m is not None:
            return m
        error_msg = "'%s/macros/%s'" % (template_name, macro_name)
    raise MacroDoesNotExist, error_msg


class MacroLoaderError(Exception):
    pass

class MacroDoesNotExist(Exception):
    pass


class MacroLoader(object):
    """Macro loader disguised as a template container

    This loader can be used in TALES path expressions.
    """

    def __getitem__(self, name):
        
        if name == 'macros':
            return _Next([], True)
        else:
            return _Next([name], False)

    def __call__(self, *args, **kw):
        # This is called if the path expression ends prematurely
        raise MacroLoaderError, 'Malformed path expression. ' \
                    'The expression does not contain a template name.'


class _Next(object):
    """Macro loader for path expressions
    """

    def __init__(self, path, done):
        self.path = path
        self.done = done

    def __getitem__(self, name):
        if self.done:
            return self._loadmacro(name)
        elif name == 'macros':
            self.done = True
        else:
            self.path.append(name)
        return _Next(self.path, self.done)

    def _loadmacro(self, name):
        if self.path:
            return loadmacro('/'.join(self.path), name)
        raise MacroLoaderError, 'Malformed path expression. ' \
                    'The expression does not contain a template name.'

    def __call__(self, *args, **kw):
        # This is called if the path expression ends prematurely
        raise MacroLoaderError, 'Malformed path expression. ' \
                    'The expression does not contain a macro name.'


# BBB
try:
    reversed
except NameError:
    def reversed(list):
        r = list[:]
        r.reverse()
        return r
