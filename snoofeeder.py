#!/usr/bin/env python
# -*- coding: utf-8-*-
"""
Snoofeeder - An RSS/Atom-to-reddit bot.
Copyright © 2014, Robert Šiška <http://github.com/RobSis>
Licensed under the GNU GPL Licence v3.

http://github.com/RobSis/snoofeeder
"""

import praw
import feedparser
from optparse import OptionParser, OptionGroup
import sys
import os
import json
import pickle as _pickle
import logging
import time

SNOOFEEDER_VERSION = '1.0'
"""
The script version number.

@type: string
"""

USAGE = "%prog [options] "
"""
A string showing the script usage syntax.

@type: string
"""

DESCRIPTION = """Mirror rss/atom feed to subreddit."""
"""
A string describing the script.

@type: string
"""

USER_CONFIGS_HOME = os.path.expanduser('~/.snoofeeder')
"""
The location where the pickles and configurations are stored.

@type: string
"""

USER_AGENT = 'snoofeeder /u/%s'
"""
The user agent of the bot. The string will be replaced with username
from configfile.

@type: string
"""


logging_level = logging.WARN
logging.basicConfig(level=logging_level)
logger = logging.getLogger('snoofeeder')
"""
Register logger.

@entrype: Logger
"""

optParser = OptionParser(usage=USAGE, version='%prog ' + SNOOFEEDER_VERSION, description=DESCRIPTION)
"""
The parser used to handle command line arguments.

@type: OptionParser
"""


def insort(a, x, cmp=cmp):
    """
    Insort x to a through bisection with given comparison function.

    @param a: the list of items
    @type a: [object]
    @param x: the object to be insorted
    @type x: object
    @param cmp: the comparison function on objects
    @type cmp: lambda
    @return: the list with object insorted
    @rtype: [object]
    """
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if cmp(x, a[mid]) < 0:
            hi = mid
        else:
            lo = mid + 1
    return a.insert(lo, x)


def verbosity_handler(option, opt, value, parser):
    """
    Handle a command line option increasing the logger verbosity.

    @param option: the Option instance calling the callback.
    @type option: Option
    @param opt: the option string seen on the command-line.
    @type opt: string
    @param value: the argument to this option seen on the command-line.
    @type value: string
    @param parser: the OptionParser instance.
    @type parser: OptionParser
    """
    # Decrease the logger level.
    global logging_level
    logging_level -= 10
    logger.setLevel(logging_level)


def load_config(config):
    """
    Load configuration json.

    @param: config: path of file with configuration
    @type: config: str
    @return: config dictionary
    @rtype: dict
    """
    logger.debug('Processing config file ' + config)
    with open(config) as f:
        json_data = f.read()
        try:
            return json.loads(json_data)
        except ValueError:
            logger.debug('Skipping non-valid json file ' + config)
            return None


def get_configs(path):
    """
    Load all non-pickle files from given folder.

    @param: path: path to search in
    @type: path: str
    @return: config paths
    @rtype: [str]
    """
    config_files = []
    for config_file in os.listdir(path):
        if not config_file.endswith('pickle'):
            config_files.append(path + "/" + config_file)
    return config_files


def load_pickle(pickle):
    """
    Load pickled list with already processed urls.

    @param: pickle: path of file with pickle
    @type: pickle: str
    @return: list of already processed urls
    @rtype: [str]
    """
    logger.debug('Loading list of already submitted from pickle ' + pickle)
    if (os.path.isfile(pickle)):
        return _pickle.load(open(pickle, 'rb'))
    else:
        return []


def save_pickle(pickle, submitted):
    """
    Pickle the list with already processed urls.

    @param: pickle: path of file with pickle
    @type: pickle: string
    @param: submitted: list of already processed urls
    @type: submitted: [str]
    """
    logger.debug('Saving list of already submitted to pickle ' + pickle)
    dirname = os.path.dirname(pickle)
    if (not os.path.exists(dirname)):
        os.makedirs(dirname)
    with open(pickle, 'w') as f:
        _pickle.dump(submitted, f)


def main():
    """
    Snoofeeder program entry point.

    @return: the exit code of the program.
    @rtype: int
    """
    # Setup the command line option parser.
    optParser.formatter.max_help_position = 50
    optParser.formatter.width = 150

    # Register the command line options.
    optParser.add_option('-c',
                         '--config',
                         action='append',
                         dest='config',
                         type='string',
                         help='load a config file. Can be used multiple times.')
    optParser.add_option('-o',
                         '--output',
                         dest='output',
                         type='string',
                         help='output directory. Default is ~/.snoofeeder')
    optParser.add_option('-v',
                         '--verbose',
                         action='callback',
                         callback=verbosity_handler,
                         help='increase verbosity level. Can be called multiple times.')

    # Parse command line options.
    options, args = optParser.parse_args()

    output_directory = USER_CONFIGS_HOME
    if options.output:
        output_directory = os.path.expanduser(options.output)

    configurations = []
    config_set = []
    # If configs passed, process them,
    if options.config:
        config_set = options.config
    else:
        # otherwise find config in default location.
        config_set = get_configs(output_directory)

    for config_file in config_set:
        config_json = load_config(config_file)
        if config_json:
            configurations.append((os.path.basename(config_file), config_json))

    if not configurations:
        logger.error('No configurations to process.')
        return 2

    for configuration in configurations:
        name, config = configuration
        pickle_path = output_directory + '/' + name + '.pickle'
        to_submit = []
        already_submitted = load_pickle(pickle_path)

        # Get all feeds from the configuration.
        feeds = config['feed_url']
        if type(feeds) is not list:
            feeds = [feeds]

        # Collect new posts from feed.
        for feed in feeds:
            entries = feedparser.parse(feed).entries
            for entry in entries:
                if entry.link not in already_submitted and entry.link not in to_submit:
                    insort(to_submit, entry, lambda x, y: cmp(x.published_parsed, y.published_parsed))

        if to_submit:
            # Get praw object.
            reddit = praw.Reddit(user_agent=USER_AGENT % config['username'])
            reddit.login(config['username'], config['password'])
            subreddit = reddit.get_subreddit(config['subreddit'])

            # Post the entries.
            for entry in to_submit:
                try:
                    submission = subreddit.submit(title=entry['title'], url=entry.link)
                    already_submitted.append(entry.link)
                    logger.debug('"' + entry['title'] + '" submitted as ' + submission.short_link)
                except praw.errors.RateLimitExceeded:
                    logger.warn('Rate limit exceeded. Waiting one minute.')
                    time.sleep(60)

            save_pickle(pickle_path, already_submitted)
    logger.info('Everything up to date.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    # Raise an error for any other exception.
    except Exception as exc:
        logger.error('%s', exc)
        sys.exit(1)
