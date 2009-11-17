import logging
logging.getLogger().setLevel(logging.DEBUG)
import os, sys
import wsgiref.handlers

from google.appengine.ext.webapp import Request
from google.appengine.api import users
from google.appengine.api import memcache


from google.appengine.ext.webapp.util import run_wsgi_app



def get_cache():
    if users.is_current_user_admin():
        return None
    env = dict(os.environ)
    env["wsgi.input"] = sys.stdin
    env["wsgi.errors"] = sys.stderr
    env["wsgi.version"] = (1, 0)
    env["wsgi.run_once"] = True
    env["wsgi.url_scheme"] = wsgiref.util.guess_scheme(env)
    env["wsgi.multithread"] = False
    env["wsgi.multiprocess"] = False
    req = Request(env)
    cached_resp = memcache.get(req.path_url.rstrip('/'))
    
    if cached_resp:
        def cache_app(env,start_resp):
            logging.info('returning cached page (%s)' % req.path_url)
            #BREAKPOINT()
            write_handle = start_resp(cached_resp.status,(cached_resp.headers.items()))
            write_handle(cached_resp.body)
        return cache_app
    else:

        return None


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