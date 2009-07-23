import logging
logging.getLogger().setLevel(logging.DEBUG)

import config
from gae import initialise
from gae.utils import BREAKPOINT
import wsgiref.handlers

from repoze.bfg.router import make_app
from google.appengine.ext.webapp.util import run_wsgi_app
from pages.utils import get_cache


def main():

    cached_result = get_cache()

    if not cached_result:
        logging.debug('Starting main import')
        import config
        from gae import initialise
        from repoze.bfg.router import make_app
        from testing.models import get_root
        import testing
        logging.debug('about to make app')
        application = make_app(get_root,testing)
        wsgiref.handlers.CGIHandler().run(application)
        
    else:
        run_wsgi_app(cached_result)

if __name__ == '__main__':
  main() 