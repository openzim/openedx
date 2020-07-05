#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import re
import sys
import uuid
import shutil
import urllib
import pathlib
import datetime
import tempfile

from bs4 import BeautifulSoup
from slugify import slugify
from zimscraperlib.zim import ZimInfo, make_zim_file
from zimscraperlib.video.encoding import reencode
from zimscraperlib.video.presets import VideoWebmLow, VideoMp4Low

from .utils import (
    check_missing_binary,
    jinja_init,
    download,
    dl_dependencies,
    jinja,
    get_meta_from_url,
    is_optimizable,
)
from .connection import Connection
from .constants import ROOT_DIR, SCRAPER, XBLOCK_EXTRACTORS, getLogger
from .annex import wiki, forum, booknav, render_wiki, render_forum, render_booknav


logger = getLogger()


class Openedx2Zim:
    def __init__(
        self,
        course_url,
        email,
        password,
        video_format,
        low_quality,
        autoplay,
        name,
        title,
        description,
        creator,
        publisher,
        tags,
        ignore_missing_xblocks,
        lang,
        add_wiki,
        add_forum,
        s3_url_with_credentials,
        use_any_optimized_version,
        output_dir,
        tmp_dir,
        fname,
        no_fulltext_index,
        no_zim,
        keep_build_dir,
        debug,
    ):

        # video-encoding info
        self.video_format = video_format
        self.low_quality = low_quality
        self.autoplay = autoplay

        # zim params
        self.fname = fname
        self.tags = [] if tags is None else [t.strip() for t in tags.split(",")]
        self.title = title
        self.description = description
        self.creator = creator
        self.publisher = publisher
        self.name = name
        self.lang = lang or "en"
        self.no_fulltext_index = no_fulltext_index

        # directory setup
        self.output_dir = pathlib.Path(output_dir).expanduser().resolve()
        if tmp_dir:
            pathlib.Path(tmp_dir).mkdir(parents=True, exist_ok=True)
        self.build_dir = pathlib.Path(tempfile.mkdtemp(dir=tmp_dir))

        # zim info
        self.zim_info = ZimInfo(
            tags=self.tags + ["_category:openedx", "openedx"],
            publisher=self.publisher,
            name=self.name,
            scraper=SCRAPER,
            favicon="favicon.png",
            language="eng",
        )

        # scraper options
        self.course_url = course_url
        self.add_wiki = add_wiki
        self.add_forum = add_forum
        self.ignore_missing_xblocks = ignore_missing_xblocks

        # authentication
        self.email = email
        self.password = password

        # optimization cache
        self.s3_url_with_credentials = s3_url_with_credentials
        self.use_any_optimized_version = use_any_optimized_version
        self.s3_storage = None

        # debug/developer options
        self.no_zim = no_zim
        self.debug = debug
        self.keep_build_dir = keep_build_dir

        # course info
        self.course_id = None
        self.instance_url = None
        self.course_info = None
        self.course_name_slug = None
        self.has_homepage = True

        # scraper data
        self.xblock_extractor_objects = []
        self.head_course_xblock = None
        self.annexed_pages = []
        self.book_lists = []
        self.course_tabs = {}
        self.course_xblocks = None
        self.root_xblock_id = None

        # forum related stuff
        self.forum_thread = None
        self.forum_category = None
        self.staff_user_forum = None

    def get_course_id(self, url, course_page_name, course_prefix, instance_url):
        clean_url = re.match(
            instance_url + course_prefix + ".*" + course_page_name, url
        )
        clean_id = clean_url.group(0)[
            len(instance_url + course_prefix) : -len(course_page_name)
        ]
        if "%3" in clean_id:  # course_id seems already encode
            return clean_id
        else:
            return urllib.parse.quote_plus(clean_id)

    def prepare_mooc_data(self, connection):
        self.instance_url = connection.conf["instance_url"]
        self.course_id = self.get_course_id(
            self.course_url,
            connection.conf["course_page_name"],
            connection.conf["course_prefix"],
            self.instance_url,
        )
        logger.info("Getting course info ...")
        self.course_info = connection.get_api_json(
            "/api/courses/v1/courses/" + self.course_id + "?username=" + connection.user
        )
        self.course_name_slug = slugify(self.course_info["name"])
        logger.info("Getting course xblocks ...")
        xblocks_data = connection.get_api_json(
            "/api/courses/v1/blocks/?course_id="
            + self.course_id
            + "&username="
            + connection.user
            + "&depth=all&requested_fields=graded,format,student_view_multi_device&student_view_data=video,discussion&block_counts=video,discussion,problem&nav_depth=3"
        )
        self.course_xblocks = xblocks_data["blocks"]
        self.root_xblock_id = xblocks_data["root"]
        # self.info == course_info
        # self.name == name_slug
        # self.json == blocks_json

    def parse_course_xblocks(self):
        def make_objects(current_path, current_id, root_url):
            current_xblock = self.course_xblocks[current_id]
            xblock_path = current_path.joinpath(slugify(current_xblock["display_name"]))

            # update root url respective to the current xblock
            root_url = root_url + "../"
            random_id = str(uuid.uuid4())
            descendants = None

            # recursively make objects for all descendents
            if "descendants" in current_xblock:
                descendants = []
                for next_xblock_id in current_xblock["descendants"]:
                    descendants.append(
                        make_objects(xblock_path, next_xblock_id, root_url)
                    )

            # create objects of respective xblock_extractor if available
            if current_xblock["type"] in XBLOCK_EXTRACTORS:
                obj = XBLOCK_EXTRACTORS[current_xblock["type"]](
                    current_xblock, xblock_path, root_url, random_id, descendants, self,
                )
            else:
                if not self.ignore_missing_xblocks:
                    logger.error(
                        f"Unsupported xblock: {current_xblock['type']} URL: {current_xblock['student_view_url']}"
                        f"  You can open an issue at https://github.com/openzim/openedx/issues with this log and MOOC URL"
                        f"  You can ignore this message by passing --ignore-missing-xblocks in atguments"
                    )
                    sys.exit(1)
                else:
                    logger.warning(
                        f"Ignoring unsupported xblock: {current_xblock['type']} URL: {current_xblock['student_view_url']}"
                    )
                    # make an object of unavailable type
                    obj = XBLOCK_EXTRACTORS["unavailable"](
                        current_xblock,
                        xblock_path,
                        root_url,
                        random_id,
                        descendants,
                        self,
                    )

            if current_xblock["type"] == "course":
                self.head_course_xblock = obj
            self.xblock_extractor_objects.append(obj)
            return obj

        logger.info("Parsing xblocks and preparing extractor objects")
        make_objects(pathlib.Path("course"), self.root_xblock_id, "../")

    def annex(self, connection):
        logger.info("Getting course tabs ...")
        content = connection.get_page(self.course_url)
        soup = BeautifulSoup(content, "lxml")
        course_tabs = (
            soup.find("ol", attrs={"class": "course-material"})
            or soup.find("ul", attrs={"class": "course-material"})
            or soup.find("ul", attrs={"class": "navbar-nav"})
            or soup.find("ol", attrs={"class": "course-tabs"})
        )
        if course_tabs is not None:
            for tab in course_tabs.find_all("li"):
                tab = tab.find("a")
                if tab["href"][-1] == "/":
                    tab_path = tab["href"][:-1].split("/")[-1]
                else:
                    tab_path = tab["href"].split("/")[-1]
                if tab_path == "course" or "courseware" in tab_path:
                    name = tab.get_text().replace(", current location", "")
                    self.course_tabs[name] = (
                        "course/" + self.head_course_xblock.folder_name + "/index.html"
                    )
                if "info" in tab_path:
                    name = tab.get_text().replace(", current location", "")
                    self.course_tabs[name] = "/index.html"
                if (
                    tab_path == "course"
                    or "edxnotes" in tab_path
                    or "progress" in tab_path
                    or "info" in tab_path
                    or "courseware" in tab_path
                ):
                    continue
                if "wiki" in tab_path and self.add_wiki:
                    self.wiki, self.wiki_name, tab_path = wiki(connection, self)
                elif "forum" in tab_path and self.add_forum:
                    tab_path = "forum/"
                    (
                        self.forum_thread,
                        self.forum_category,
                        self.staff_user_forum,
                    ) = forum(
                        connection, self.build_dir, self.instance_url, self.course_id
                    )
                elif ("wiki" not in tab_path) and ("forum" not in tab_path):
                    output_path = self.build_dir.joinpath(tab_path)
                    output_path.mkdir(parents=True, exist_ok=True)
                    page_content = connection.get_page(self.instance_url + tab["href"])
                    soup_page = BeautifulSoup(page_content, "lxml")
                    just_content = soup_page.find(
                        "section", attrs={"class": "container"}
                    )
                    if just_content is not None:
                        html_content = dl_dependencies(
                            str(just_content), output_path, "", connection
                        )
                        self.annexed_pages.append(
                            {
                                "output_path": output_path,
                                "content": html_content,
                                "title": soup_page.find("title").get_text(),
                            }
                        )
                    else:
                        book = soup_page.find(
                            "section", attrs={"class": "book-sidebar"}
                        )
                        if book is not None:
                            self.book_lists.append(
                                {
                                    "output_path": output_path,
                                    "book_list": booknav(self, book, output_path),
                                    "dir_path": tab_path,
                                }
                            )
                        else:
                            logger.warning(
                                "Oh it's seems we does not support one type of extra content (in top bar) :"
                                + tab_path
                            )
                            continue
                self.course_tabs[tab.get_text()] = tab_path + "/index.html"

    def get_content(self, connection):

        # download favicon
        download(
            "https://www.google.com/s2/favicons?domain=" + self.instance_url,
            self.build_dir.joinpath("favicon.png"),
            None,
        )

        logger.info("Getting homepage ...")
        content = connection.get_page(self.course_url)
        self.build_dir.joinpath("home").mkdir(parents=True, exist_ok=True)
        self.html_homepage = []
        soup = BeautifulSoup(content, "lxml")
        html_content = soup.find("div", attrs={"class": "welcome-message"})
        if html_content is None:
            html_content = soup.find_all(
                "div", attrs={"class": re.compile("info-wrapper")}
            )
            if html_content == []:
                self.has_homepage = False
            else:
                for x in range(0, len(html_content)):
                    article = html_content[x]
                    dismiss = article.find("div", attrs={"class": "dismiss-message"})
                    if dismiss is not None:
                        dismiss.decompose()
                    bookmark = article.find(
                        "a", attrs={"class": "action-show-bookmarks"}
                    )
                    if bookmark is not None:
                        bookmark.decompose()
                    buttons = article.find_all(
                        "button", attrs={"class": "toggle-visibility-button"}
                    )
                    if buttons is not None:
                        for button in buttons:
                            button.decompose()
                    article["class"] = "toggle-visibility-element article-content"
                    self.html_homepage.append(
                        dl_dependencies(
                            article.prettify(),
                            self.build_dir.joinpath("home"),
                            "home",
                            connection,
                        )
                    )
        else:
            dismiss = html_content.find("div", attrs={"class": "dismiss-message"})
            if dismiss is not None:
                dismiss.decompose()
            bookmark = html_content.find("a", attrs={"class": "action-show-bookmarks"})
            if bookmark is not None:
                bookmark.decompose()
            buttons = html_content.find_all(
                "button", attrs={"class": "toggle-visibility-button"}
            )
            if buttons is not None:
                for button in buttons:
                    button.decompose()
            self.html_homepage.append(
                dl_dependencies(
                    html_content.prettify(),
                    self.build_dir.joinpath("home"),
                    "home",
                    connection,
                )
            )
        logger.info("Getting content for supported xblocks ...")
        for obj in self.xblock_extractor_objects:
            obj.download(connection)

    def s3_credentials_ok(self):
        logger.info("Testing S3 Optimization Cache credentials")
        self.s3_storage = KiwixStorage(self.s3_url_with_credentials)
        if not self.s3_storage.check_credentials(
            list_buckets=True, bucket=True, write=True, read=True, failsafe=True
        ):
            logger.error("S3 cache connection error testing permissions.")
            logger.error(f"  Server: {self.s3_storage.url.netloc}")
            logger.error(f"  Bucket: {self.s3_storage.bucket_name}")
            logger.error(f"  Key ID: {self.s3_storage.params.get('keyid')}")
            logger.error(f"  Public IP: {get_public_ip()}")
            return False
        return True

    def download_from_cache(self, key, fpath, meta):
        """ whether it downloaded from S3 cache """

        if self.use_any_optimized_version:
            if not self.s3_storage.has_object(key, self.s3_storage.bucket_name):
                return False
        else:
            if not self.s3_storage.has_object_matching_meta(
                key, tag="encoder_version", value=f"v{encoder_version}"
            ):
                return False
        fpath.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.s3_storage.download_file(key, fpath)
        except Exception as exc:
            logger.error(f"{key} failed to download from cache: {exc}")
            return False
        logger.info(f"downloaded {fpath} from cache at {key}")
        return True

    def upload_to_cache(self, key, fpath, meta):
        """ whether it uploaded to S3 cache """

        try:
            self.s3_storage.upload_file(
                fpath, key, meta=meta
            )
        except Exception as exc:
            logger.error(f"{key} failed to upload to cache: {exc}")
            return False
        logger.info(f"uploaded {fpath} to cache at {key}")
        return True

    def downlaod_form_url(self, url, fpath):
        download_path = fpath
        if filetype and fpath.suffix != filetype:
            download_path = pathlib.Path(tempfile.NamedTemporaryFile(suffix=f".{filetype}", dir=fpath.parent, delete=False).name)
        save_large_file(url, download_path)
        return download_path

    def convert_video(self, downloaded_file, fpath):
        if (downloaded_file.suffix != self.video_format) or self.low_quality:
            preset = VideoWebmLow() if self.video_format == "webm" else VideoMp4Low()
            reencode(
                pathlib.Path(downloaded_file),
                pathlib.Path(fpath),
                preset.to_ffmpeg_args(),
                delete_src=True,
                failsafe=False,
            )

    def optimize_image(self, downloaded_file, fpath, resize=None):
        if resize:
            resize_image()
        if downloaded_file.suffix == "jpeg":
            exec_cmd("jpegoptim --strip-all -m50 " + str(downloaded_file), timeout=10)
        elif downloaded_file.suffix == "png":
            exec_cmd("pngquant --verbose --nofs --force --ext=.png " + str(downloaded_file), timeout=10)
            exec_cmd("advdef -q -z -4 -i 5  " + str(downloaded_file), timeout=10)
        elif downloaded_file.suffix == "gif":
            exec_cmd("gifsicle --batch -O3 -i " + str(downloaded_file), timeout=10)
        shutil.move(downloaded_file, fpath)

    def optimize_file(self, downloaded_file, fpath):
        if downloaded_file.suffix in VIDEO_FORMATS:
            self.convert_video(downloaded_file, fpath)
        else:
            self.optimize_image(downloaded_file, fpath)


    def generate_s3_key(self, url, fpath):
        if fpath.suffix in VIDEO_FORMATS:
            quality = "low" if self.low_quality else "high"
        else:
            quality = "default"
        src_url = urllib.parse.urlparse(url)
        prefix = f"{src_url.scheme}://{src_url.netloc}/"
        safe_url = f"{src_url.netloc}/{urllib.parse.quote_plus(src_url.geturl()[len(prefix):])}"
        # safe url looks similar to ww2.someplace.state.gov/data%2F%C3%A9t%C3%A9%2Fsome+chars%2Fimage.jpeg%3Fv%3D122%26from%3Dxxx%23yes
        return f"{fpath.suffix}/{safe_url}/{quality}"

    def download_file(self, url, fpath, scraper):
        youtube = False
        if "youtube" in url:
            youtube = True
        downloaded_from_cache = False
        meta, filetype = get_meta_from_url(url)
        if scraper.s3_storage:
            s3_key = self.generate_s3_key(url, fpath)
            downloaded_from_cache = self.download_from_cache(s3_key, fpath, meta)
        if not downloaded_from_cache:
            try:
                if youtube:
                    downloaded_file = self.downlaod_form_youtube(url, fpath)
                else:
                    downloaded_file = self.downlaod_form_url(url, fpath, filetype)
            except Exception as exc:
                logger.error(f"Error while downloading {fpath}: {exc}")
                os.unlink(downloaded_file, ignore_errors=True)
                return
            if is_optimizable(fpath):
                try:
                    self.optimize_file(downloaded_file, fpath)
                except Exception:
                    logger.error(f"Error while optimizing {fpath}: {exc}")
                    return
                else:
                    if s3_storage:
                        upload_to_cache(s3_key, fpath, meta)


    def render(self):
        # Render course
        self.head_course_xblock.render()

        # Render annexed pages
        for page in self.annexed_pages:
            jinja(
                page["output_path"].joinpath("index.html"),
                "specific_page.html",
                False,
                title=page["title"],
                mooc=self,
                content=page["content"],
                rooturl="../../",
            )

        # render wiki if available
        if hasattr(self, "wiki"):
            render_wiki(self)

        # render forum if available
        if self.forum_category:
            render_forum(self)

        # render book lists
        if len(self.book_lists) != 0:
            render_booknav(self)
        if self.has_homepage:
            # render homepage
            jinja(
                self.build_dir.joinpath("index.html"),
                "home.html",
                False,
                messages=self.html_homepage,
                mooc=self,
                render_homepage=True,
            )
        shutil.copytree(
            ROOT_DIR.joinpath("static"), self.build_dir.joinpath("static"),
        )

    def update_zim_info(self):
        if not self.has_homepage:
            homepage = f"{self.head_course_xblock.relative_path}/index.html"
        else:
            homepage = "index.html"

        self.zim_info.update(
            description=self.description
            if self.description
            else self.course_info["short_description"],
            title=self.title if self.title else self.course_info["name"],
            creator=self.creator if self.creator else self.course_info["org"],
            homepage=homepage,
        )

    def run(self):
        logger.info(
            f"Starting {SCRAPER} with:\n"
            f"  Course URL: {self.course_url}\n"
            f"  Email ID: {self.email}"
        )
        logger.debug("Checking for missing binaries")
        check_missing_binary(self.no_zim)
        logger.info("Checking S3 cache credentials")
        if self.s3_url_with_credentials and not self.s3_credentials_ok():
            raise ValueError("Unable to connect to Optimization Cache. Check its URL.")
        if self.s3_storage:
            logger.info(
                f"Using cache: {self.s3_storage.url.netloc} with bucket: {self.s3_storage.bucket_name}"
            )
        logger.debug("Testing credentials")
        connection = Connection(self.password, self.course_url, self.email)
        jinja_init()
        self.prepare_mooc_data(connection)
        self.parse_course_xblocks()
        self.annex(connection)
        self.download(connection)
        self.render()
        if not self.no_zim:
            self.fname = (
                self.fname or f"{self.name.replace(' ', '-')}_{{period}}.zim"
            ).format(period=datetime.datetime.now().strftime("%Y-%m"))
            logger.info("building ZIM file")
            self.update_zim_info()
            logger.debug(self.zim_info.to_zimwriterfs_args())
            if not self.output_dir.exists():
                self.output_dir.mkdir(parents=True)
            make_zim_file(
                self.build_dir,
                self.output_dir,
                self.fname,
                self.zim_info,
                withoutFTIndex=True if self.no_fulltext_index else False,
            )
            if not self.keep_build_dir:
                logger.info("Removing temp folder...")
                shutil.rmtree(self.build_dir, ignore_errors=True)
        logger.info("Done everything")
