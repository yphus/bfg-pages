"""
 TALES expression engine for GAE, adapted from Django Page Templates

"""

from zope.interface import implements
from zope.tales.interfaces import ITALESExpression
from zope.tales.tales import ExpressionEngine
from zope.tales.expressions import PathExpr as BasePathExpr
from zope.tales.expressions import StringExpr, NotExpr, DeferExpr
from zope.tales.expressions import SimpleModuleImporter
from zope.tales.pythonexpr import PythonExpr

_marker = object()
from gae.utils import BREAKPOINT

def simpleTraverse(object, path_items, econtext):
    """Traverses a sequence of names, first trying attributes then items.
    """
    for name in path_items:
        next = getattr(object, name, _marker)
        if next is not _marker:
            object = next
        elif hasattr(object, '__getitem__'):
            
            object = object[name]
        else:
            # Allow AttributeError to propagate
            object = getattr(object, name)
    return object


class PathExpr(BasePathExpr):
    """One or more subpath expressions, separated by '|'.

    This class comes with a custom traverser, as the one in zope.tales
    acts funny if objects don't implement __getitem__.
    """
    implements(ITALESExpression)

    def __init__(self, name, expr, engine, traverser=simpleTraverse):
        BasePathExpr.__init__(self, name, expr, engine, traverser)


def Engine():
    """Constructs the TALES engine."""
    e = ExpressionEngine()
    for name in PathExpr._default_type_names:
        e.registerType(name, PathExpr)
    e.registerType('string', StringExpr)
    e.registerType('python', PythonExpr)
    e.registerType('not', NotExpr)
    e.registerType('defer', DeferExpr)
    e.registerBaseName('modules', SimpleModuleImporter())
    return e


Engine = Engine()

