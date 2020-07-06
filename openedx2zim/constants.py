#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import pathlib
import logging

from zimscraperlib.logging import getLogger as lib_getLogger
from zimscraperlib.video.presets import VideoMp4Low, VideoWebmLow

ROOT_DIR = pathlib.Path(__file__).parent
NAME = ROOT_DIR.name

with open(ROOT_DIR.joinpath("VERSION"), "r") as fh:
    VERSION = fh.read().strip()

SCRAPER = f"{NAME} {VERSION}"

VIDEO_FORMATS = ["webm", "mp4"]

IMAGE_FORMATS = ["png", "jpeg", "jpg", "gif"]

OPTIMIZER_VERSIONS = {
    "mp4": f"v{VideoMp4Low().VERSION}",
    "webm": f"v{VideoWebmLow().VERSION}",
}


class Global:
    debug = False


def setDebug(debug):
    """ toggle constants global DEBUG flag (used by getLogger) """
    Global.debug = bool(debug)


def getLogger():
    """ configured logger respecting DEBUG flag """
    return lib_getLogger(NAME, level=logging.DEBUG if Global.debug else logging.INFO)


from .xblocks_extractor.Course import Course
from .xblocks_extractor.Chapter import Chapter
from .xblocks_extractor.Sequential import Sequential
from .xblocks_extractor.Vertical import Vertical
from .xblocks_extractor.Video import Video
from .xblocks_extractor.Libcast import Libcast
from .xblocks_extractor.Html import Html
from .xblocks_extractor.Problem import Problem
from .xblocks_extractor.Discussion import Discussion
from .xblocks_extractor.FreeTextResponse import FreeTextResponse
from .xblocks_extractor.Unavailable import Unavailable
from .xblocks_extractor.Lti import Lti
from .xblocks_extractor.DragAndDropV2 import DragAndDropV2

XBLOCK_EXTRACTORS = {
    "course": Course,
    "chapter": Chapter,
    "sequential": Sequential,
    "vertical": Vertical,
    "video": Video,
    "libcast_xblock": Libcast,
    "html": Html,
    "problem": Problem,
    "discussion": Discussion,
    "qualtricssurvey": Html,
    "freetextresponse": FreeTextResponse,
    "grademebutton": Unavailable,
    "drag-and-drop-v2": DragAndDropV2,
    "lti": Lti,
    "unavailable": Unavailable,
}
