from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='gaesession',
      version=version,
      description="A beaker.session backend using memcache in google app engine",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='google appengine beaker session memcache',
      author='Tim Hoffman',
      author_email='zutesmog@gmail.com',
      url='http://code.google.com/p/bfg-pages/',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
