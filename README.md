Snoofeeder
==========

Bot that mirrors rss/atom feed to given subreddit.


Install dependencies
--------------------
    $ pip install -r requirements.txt


Usage
-----
  You can optionally install the package:

    $ python setup.py install [--user]
```
  Usage: snoofeeder.py [options]

  Options:
    -c CONFIG, --config=CONFIG  load a config file. Can be used multiple times.
    -o OUTPUT, --output=OUTPUT  output directory. Default is ~/.snoofeeder
    -v, --verbose               increase verbosity level. Can be called multiple times.
    --version                   show program's version number and exit
    -h, --help                  show this help message and exit
```
  If no `-c` argument is specified, the `OUTPUT` directory is searched for the config files.


Config file example
-------------------
```
{
    "username": "reddit_name",
    "password": "reddit_password",
    "feed_url": "http://some.magazine.com/?format=feed&type=rss",
    "subreddit": "subreddit_name"
}
```

`feed_url` field can be either URL or list of URLs. If more URLs
are specified, they're merged chronologically.


Licence
-------
GPLv3
