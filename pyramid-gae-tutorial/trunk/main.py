import logging

logging.getLogger().setLevel(logging.INFO)

import sys,os

sys.path.insert(0,'lib/dist')

import utils

from pyramid.configuration import Configurator
from models import get_root
from google.appengine.ext.webapp.util import run_wsgi_app



def main():
    """ This function returns a Pyramid WSGI application.
    """
    logging.warning('Starting main')
    config = Configurator(root_factory=get_root,settings=utils.settings)
    config.add_view('views.my_view',
                    context='models.MyModel',
                    renderer='templates/mytemplate.pt')
    app= config.make_wsgi_app()
    run_wsgi_app(app)
            
if __name__ == '__main__':
  main() 