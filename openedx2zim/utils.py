import html
import mimetypes
import os
import re
import shlex
import subprocess
import urllib
import zlib
import sys

import requests

import magic
import mistune  # markdown
from jinja2 import Environment, FileSystemLoader
from slugify import slugify
from webvtt import WebVTT

from .constants import getLogger

logger = getLogger()

renderer = mistune.HTMLRenderer()
MARKDOWN = mistune.Markdown(renderer)


def exec_cmd(cmd, timeout=None):
    try:
        return subprocess.call(shlex.split(cmd), timeout=timeout)
    except Exception as e:
        logger.error(e)
        pass


def bin_is_present(binary):
    try:
        subprocess.Popen(
            binary,
            universal_newlines=True,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
    except OSError:
        return False
    else:
        return True


def check_missing_binary(no_zim):
    if not no_zim and not bin_is_present("zimwriterfs"):
        sys.exit("zimwriterfs is not available, please install it.")
    for bin in ["jpegoptim", "pngquant", "advdef", "gifsicle", "mogrify"]:
        if not bin_is_present(bin):
            sys.exit(bin + " is not available, please install it.")
    if not (bin_is_present("ffmpeg") or bin_is_present("avconv")):
        sys.exit("You should install ffmpeg or avconv")


def markdown(text):
    return MARKDOWN(text)[3:-5].replace("\n", "<br>")


def remove_newline(text):
    return text.replace("\n", "")


def prepare_url(url, instance_url):
    if url[0:2] == "//":
        url = "http:" + url
    elif url[0] == "/":
        url = instance_url + url

    # for IRI
    split_url = list(urllib.parse.urlsplit(url))
    # split_url[2] = urllib.parse.quote(split_url[2])    # the third component is the path of the URL/IRI
    return urllib.parse.urlunsplit(split_url)


def download_and_convert_subtitles(path, lang_and_url, instance_connection):
    real_subtitles = {}
    for lang in lang_and_url:
        path_lang = os.path.join(path, lang + ".vtt")
        if not os.path.exists(path_lang):
            try:
                subtitle = instance_connection.get_page(lang_and_url[lang])
                subtitle = re.sub(r"^0$", "1", str(subtitle), flags=re.M)
                subtitle = html.unescape(subtitle)
                with open(path_lang, "w") as f:
                    f.write(subtitle)
                if not is_webvtt(path_lang):
                    webvtt = WebVTT().from_srt(path_lang)
                    webvtt.save()
                real_subtitles[lang] = lang + ".vtt"
            except urllib.error.HTTPError as e:
                if e.code == 404 or e.code == 403:
                    logger.error(
                        "Fail to get subtitle from {}".format(lang_and_url[lang])
                    )
                    pass
            except Exception as e:
                logger.error(
                    "Error when converting subtitle {} : {}".format(
                        lang_and_url[lang], e
                    )
                )
                pass
        else:
            real_subtitles[lang] = lang + ".vtt"
    return real_subtitles


def is_webvtt(path):
    f = open(path, "r")
    first_line = f.readline()
    f.close()
    return "WEBVTT" in first_line or "webvtt" in first_line


def get_filetype(headers, path):
    extensions = ("png", "jpeg", "gif")
    content_type = headers.get("content-type", "").lower().strip()
    for ext in extensions:
        if ext in content_type:
            return ext
    if "jpg" in content_type:
        return "jpeg"
    mime = magic.from_file(path)
    for ext in extensions:
        if ext.upper() in mime:
            return ext
    return "none"


def jinja(output, template, deflate, **context):
    template = ENV.get_template(template)
    page = template.render(**context, output_path=str(output))
    if output is None:
        return page
    with open(output, "w") as f:
        if deflate:
            f.write(zlib.compress(page.encode("utf-8")))
        else:
            f.write(page)


def jinja_init():
    global ENV
    templates = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates/")
    ENV = Environment(loader=FileSystemLoader((templates,)))
    filters = dict(
        slugify=slugify,
        markdown=markdown,
        remove_newline=remove_newline,
        first_word=first_word,
        clean_top=clean_top,
    )
    ENV.filters.update(filters)


def clean_top(t):
    return "/".join(t.split("/")[:-1])


def first_word(text):
    return " ".join(text.split(" ")[0:5])


def get_meta_from_url(url):
    def get_response_headers(url):
        for attempt in range(5):
            try:
                return requests.head(url=url, allow_redirects=True, timeout=30).headers
            except requests.exceptions.Timeout:
                logger.error(f"{url} > HEAD request timed out ({attempt})")
        raise Exception("Max retries exceeded")

    try:
        response_headers = get_response_headers(url)
    except Exception as exc:
        logger.error(f"{url} > Problem with head request\n{exc}\n")
        return None, None
    else:
        content_type = mimetypes.guess_extension(
            response_headers.get("content-type", None).split(";", 1)[0].strip()
        )[1:]
        if response_headers.get("etag", None) is not None:
            return response_headers["etag"], content_type
        if response_headers.get("last-modified", None) is not None:
            return response_headers["last-modified"], content_type
        if response_headers.get("content-length", None) is not None:
            return response_headers["content-length"], content_type
    return None, content_type
