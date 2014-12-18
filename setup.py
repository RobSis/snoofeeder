#!/usr/bin/env python
import os
from distutils.core import setup

setup(name='snoofeeder',
      version='0.1',
      description='Mirror rss/atom feed to given subreddit',
      long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
      url='http://github.com/RobSis/snoofeeder',
      author='http://github.com/RobSis',
      author_email='siska.robert@gmail.com',
      license='GPLv3',
      scripts=['snoofeeder.py']
)
