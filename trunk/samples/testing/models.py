
from zope.interface import implements,Interface

from gae.utils import BREAKPOINT

from pages import interfaces, getimageinfo
from pages.models import getRoot, Root


def get_root(environ):
    
    return getRoot(environ)

