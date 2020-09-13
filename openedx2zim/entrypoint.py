#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import argparse

from .constants import NAME, SCRAPER, getLogger, setDebug


def main():
    parser = argparse.ArgumentParser(
        prog=NAME,
        description="Scraper to create ZIM files MOOCs on openedx instances",
    )

    parser.add_argument(
        "--course-url",
        help="URL of the course you wnat to scrape",
        required=True,
    )

    parser.add_argument(
        "--email",
        help="Your registered e-mail ID on the platform. Used for authentication",
        required=True,
    )

    parser.add_argument(
        "--password",
        help="The password to your registered account on the platform. If you don't provide one here, you'll be asked for it later",
    )

    parser.add_argument(
        "--format",
        help="Format to download/transcode video to. webm is smaller",
        choices=["mp4", "webm"],
        default="webm",
        dest="video_format",
    )

    parser.add_argument(
        "--low-quality",
        help="Re-encode video using stronger compression",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--autoplay",
        help="Enable autoplay on videos. Behavior differs on platforms/browsers.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--name",
        help="ZIM name. Used as identifier and filename (date will be appended)",
        required=True,
    )

    parser.add_argument(
        "--title",
        help="Custom title for your ZIM. Based on MOOC otherwise.",
    )

    parser.add_argument(
        "--description",
        help="Custom description for your ZIM. Based on MOOC otherwise.",
    )

    parser.add_argument("--creator", help="Name of content creator", default="edX")

    parser.add_argument(
        "--publisher", help="Custom publisher name (ZIM metadata)", default="Kiwix"
    )

    parser.add_argument(
        "--tags",
        help="List of comma-separated Tags for the ZIM file. category:other, openedx, and _videos:yes (if present) added automatically",
    )

    parser.add_argument(
        "--ignore-missing-xblocks",
        help="Ignore unsupported content (xblock)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--instance-login-page",
        help="The login path in the instance. Must start with /",
        default="/login_ajax",
    )

    parser.add_argument(
        "--instance-course-page",
        help="The path to the course page after the course ID. Must start with /",
        default="/course",
    )

    parser.add_argument(
        "--instance-course-prefix",
        help="The prefix in the path before the course ID. Must start and end with /",
        default="/courses/",
    )

    parser.add_argument(
        "--favicon-url",
        help="URL pointing to a favicon image. Recommended size >= (48px x 48px)",
        default="https://github.com/edx/edx-platform/raw/master/lms/static/images/favicon.ico",
    )

    parser.add_argument(
        "--add-wiki",
        help="Add wiki (if available) to the ZIM",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--add-forum",
        help="Add forum (if available) to the ZIM",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--remove-seq-nav",
        help="Remove the top sequential navigation bar in the ZIM",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--optimization-cache",
        help="URL with credentials and bucket name to S3 Optimization Cache",
        dest="s3_url_with_credentials",
    )

    parser.add_argument(
        "--use-any-optimized-version",
        help="Use files on S3 cache if present, whatever the version",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--output",
        help="Output folder for ZIM file",
        default="output",
        dest="output_dir",
    )

    parser.add_argument(
        "--tmp-dir",
        help="Path to create temp folder in. Used for building ZIM file. Receives all data",
    )

    parser.add_argument(
        "--zim-file",
        help="ZIM file name (based on --name if not provided)",
        dest="fname",
    )

    parser.add_argument(
        "--no-fulltext-index",
        help="Don't index the scraped content in the ZIM",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--no-zim",
        help="Don't produce a ZIM file, create build folder only.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--keep",
        help="Don't remove build folder on start (for debug/devel)",
        default=False,
        action="store_true",
        dest="keep_build_dir",
    )

    parser.add_argument(
        "--debug", help="Enable verbose output", action="store_true", default=False
    )

    parser.add_argument(
        "--threads",
        help="Number of threads to use while offlining xblocks",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--version",
        help="Display scraper version and exit",
        action="version",
        version=SCRAPER,
    )

    args = parser.parse_args()
    setDebug(args.debug)
    logger = getLogger()

    from .scraper import Openedx2Zim

    try:
        scraper = Openedx2Zim(**dict(args._get_kwargs()))
        scraper.run()
    except Exception as exc:
        logger.error(f"FAILED. An error occurred: {exc}")
        if args.debug:
            logger.exception(exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
