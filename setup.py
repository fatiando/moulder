#!/usr/bin/env python

from distutils.core import setup


setup(name='moulder',
      version='draft-01',
      description='Interactive 2D Forward Gravity Modeller',
      author='',
      author_email='',
      url='http://www.fatiando.org',
      packages=['moulder'],
      entry_points={
          'console_scripts': ['moulder=moulder.__init__:main']
      }
      )
