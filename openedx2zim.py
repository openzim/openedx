#!/usr/bin/env python3
# -*-coding:utf8 -*
"""openedx2zim.

Usage:
  openedx2zim <course_url> <publisher> <email> [--password=<pass>] [--nozim] [--zimpath=<zimpath>] [--nofulltextindex] [--transcode2webm] [--ignore-unsupported-xblocks]
  openedx2zim (-h | --help)
  openedx2zim --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --password=<pass> you can specify password as arguments or you'll be asked for password
  --nozim       doesn't make zim file, output will be in work/ in normal html
  --zimpath=<zimpath>   Final path of the zim file
  --nofulltextindex        Dont index content
  --transcode2webm  Transcode videos in webm
  --ignore-unsupported-xblocks  Ignore unsupported content (xblock)

"""
"""
import json
import re
from http.cookiejar import LWPCookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import (
    urlencode,
    quote_plus,
    unquote,
)
from urllib.request import (
    urlopen,
    build_opener,
    install_opener,
    HTTPCookieProcessor,
    Request,
    urlretrieve,
)
import ssl
import sys
import os
import bs4 as BeautifulSoup

from lxml.etree import parse as string2xml
from lxml.html import fromstring as string2html
from lxml.html import tostring as html2string
from webvtt import WebVTT
import youtube_dl

"""

from docopt import docopt
import sys
import os
import logging

from openedxtozim.utils import check_missing_binary,jinja_init
from openedxtozim.connection import Connection
from openedxtozim.mooc import Mooc

def run():
    arguments = docopt(__doc__, version='0.1')
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    logging.info("Test (missing) bin")
    check_missing_binary(arguments['--nozim'])
    logging.info("Testing connection")
    c=Connection(arguments["--password"], arguments["<course_url>"], arguments["<email>"])

    jinja_init(os.path.join(os.path.abspath(os.path.dirname(__file__)),"openedxtozim","templates/"))

    mooc=Mooc(c,arguments["<course_url>"], arguments["--transcode2webm"], arguments["--ignore-unsupported-xblocks"])
    mooc.parser_json()
    mooc.annexe(c)
    mooc.download(c)
    mooc.render()
    mooc.make_welcome_page(c)
    if not arguments['--nozim']:
        mooc.zim("eng",arguments["<publisher>"],arguments["--zimpath"],arguments["--nofulltextindex"])

if __name__ == '__main__':
    run()

