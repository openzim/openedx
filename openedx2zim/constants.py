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
    "png": "v1",
    "jpeg": "v1",
    "gif": "v1",
}

DOWNLOADABLE_CONTENT = [
    ".doc",
    ".docx",
    ".pdf",
    ".DOC",
    ".DOCX",
    ".PDF",
    ".mp4",
    ".MP4",
    ".webm",
    ".WEBM",
    ".mp3",
    ".MP3",
    ".zip",
    ".ZIP",
    ".TXT",
    ".txt",
    ".CSV",
    ".csv",
    ".R",
    ".r",
]

INSTANCE_CONFIGS = {
    "courses.edx.org": {
        "login_page": "/login_ajax",
        "account_page": "/account/settings",
        "course_page_name": "/course",
        "course_prefix": "/courses/",
        "instance_url": "https://courses.edx.org",
    },
    "courses.edraak.org": {
        "login_page": "/login_ajax",
        "account_page": "/account/settings",
        "course_page_name": "/",
        "course_prefix": "/courses/",
        "instance_url": "https://courses.edraak.org",
    },
    "default": {
        "login_page": "/login_ajax",
        "account_page": "/account/settings",
        "course_page_name": "/info",
        "course_prefix": "/courses/",
        "instance_url": "",
    },
}

UNSUPPORTED_XBLOCKS = {"grademebutton": "Grade Me (Unavialable Offline)"}


class Global:
    debug = False


def setDebug(debug):
    """ toggle constants global DEBUG flag (used by getLogger) """
    Global.debug = bool(debug)


def getLogger():
    """ configured logger respecting DEBUG flag """
    return lib_getLogger(NAME, level=logging.DEBUG if Global.debug else logging.INFO)
