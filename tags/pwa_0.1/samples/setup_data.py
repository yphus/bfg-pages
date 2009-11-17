import config
from gae import initialise

import sys
import wsgiref.handlers
from repoze.bfg.router import make_app
from testing.models import get_root
from gae.utils import settings

import testing

def main():
   
    application = make_app(get_root,testing)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main() 