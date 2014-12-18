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
import json
from optparse import OptionParser, OptionGroup
import sys
import os
import pickle as _pickle
import logging
import time


SNOOFEEDER_VERSION = '0.1'
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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("snoofeeder")
"""
Register logger.

@entrype: Logger
"""

optParser = OptionParser(usage=USAGE, version="%prog " + SNOOFEEDER_VERSION, description=DESCRIPTION)
"""
The parser used to handle command line arguments.

@type: OptionParser
"""


def handle_command_line_verbosity_option(option, opt, value, parser):
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
    @rtype: void
    """
    # Decrease the logger level.
    logger.setLevel(logger.level - 10)

def load_config(config):
    """
    Load configuration json.

    @param: config: path of file with configuration
    @type: config: str
    @return: config dictionary
    @rtype: dict
    """
    with open(config) as f:
        json_data = f.read()
        return json.loads(json_data)


def load_submitted(pickle):
    """
    Load pickled list with already processed urls.

    @param: pickle: path of file with pickle
    @type: pickle: str
    @return: list of already processed urls
    @rtype: [str]
    """
    if (os.path.isfile(pickle)):
        return _pickle.load(open(pickle, 'rb'))
    else:
        return []


def save_submitted(pickle, submitted):
    """
    Pickle the list with already processed urls.

    @param: pickle: path of file with pickle
    @type: pickle: string
    """
    with open(pickle,'w') as f:
        _pickle.dump(submitted, f)


def get_feed(url):
    """
    Return all the entries of given feed in (url, title) tuple.

    @param url: url of the feed
    @type url: str
    @return: (url, title) tuple.
    @rtype: (str, str)
    """
    feed = feedparser.parse(url)
    return [{'url': x.link, 'title': x.title} for x in feed.entries]


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
    optParser.add_option("-c",
                         "--config",
                         action="append",
                         dest="config",
                         type="string",
                         help="Load a config file.")
    optParser.add_option("-v",
                         "--verbose",
                         action="callback",
                         callback=handle_command_line_verbosity_option,
                         help="Turn on verbose mode.")

    # Parse command line options.
    (options, args) = optParser.parse_args()

    # If configs passed, process them.
    if options.config:
        for config in options.config:
            config_file = locate_config(config)
            if config_file:
                logger.debug("Config '%s' located at '%s'.", config, config_file)
                process_config(config_file,options)
            else:
                logger.error("Could not locate the config '%s'.", config)
    else:
        # find config in default location
        pass

    config = load_config('config.json')
    submitted = load_submitted('submitted.pickle')
    to_submit = []

    try:
        # get praw object
        reddit = praw.Reddit(user_agent='snoofeeder /u/%s' % config['username'])
        reddit.login(config['username'], config['password'])
        sub = reddit.get_subreddit(config['subreddit'])

        # collect new posts from feed
        entries = get_feed(config['feed_url'])
        entries.reverse()
        for entry in entries:
            if entry['url'] not in submitted and entry['url'] not in to_submit:
                to_submit.append(entry)

                logger.debug('"' + entry['title'] + '" will be processed.')

        # post the entries
        for entry in to_submit:
            try:
                submission = subreddit.submit(title=entry['title'], url=entry['url'])
                submitted.append(entry['url'])

                logger.info('"' + entry['title'] + '" submitted as ' + submission.short_link)
            except praw.errors.RateLimitExceeded:
                logger.warn('Rate limit exceeded. Waiting one minute.')
                time.sleep(60)

        save_submitted('submitted.pickle', submitted)
        logger.info('Everything up to date.')

    # Raise an error for any other exception.
    except Exception as exc:
        logger.error("%s", exc)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
