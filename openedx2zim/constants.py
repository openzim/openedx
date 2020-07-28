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

AUDIO_FORMATS = ["ogg", "mp3", "aif", "mpa", "wav", "wma"]

OPTIMIZER_VERSIONS = {
    "mp4": f"v{VideoMp4Low().VERSION}",
    "webm": f"v{VideoWebmLow().VERSION}",
    "png": "v1",
    "jpeg": "v1",
    "gif": "v1",
}

DOWNLOADABLE_EXTENSIONS = [
    ".doc",
    ".docx",
    ".pdf",
    ".mp4",
    ".webm",
    ".mp3",
    ".zip",
    ".txt",
    ".csv",
    ".r",
    ".aif",
    ".m4a",
    ".wav",
    ".wma",
    ".ogg",
]

UNSUPPORTED_XBLOCKS = {"grademebutton": "Grade Me (Unavailable Offline)"}


class Global:
    debug = False


def setDebug(debug):
    """ toggle constants global DEBUG flag (used by getLogger) """
    Global.debug = bool(debug)


def getLogger():
    """ configured logger respecting DEBUG flag """
    return lib_getLogger(NAME, level=logging.DEBUG if Global.debug else logging.INFO)
