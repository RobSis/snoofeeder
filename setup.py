#!/usr/bin/env python
# -*- coding: utf-8-*-
import os
from distutils.core import setup

setup(name='snoofeeder',
      version='1.0',
      description='Mirror rss/atom feed to given subreddit',
      long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
      url='http://github.com/RobSis/snoofeeder',
      author='http://github.com/RobSis',
      author_email='siska.robert@gmail.com',
      keywords = "reddit rss atom feed bot",

      license='GPLv3',
      scripts=['snoofeeder.py'])
