import sys
from gae.utils import settings

_marker = None

def setup():
    
    zipimports = settings.get('zipimports',[])
    for i in zipimports:
        sys.path.append(i)
    _marker = True


if not _marker:

    setup()