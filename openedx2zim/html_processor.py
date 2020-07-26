import hashlib
import pathlib
import re
import urllib

import lxml.html

from .constants import DOWNLOADABLE_EXTENSIONS
from .utils import jinja, prepare_url


class HtmlProcessor:
    def __init__(self, scraper):
        self.scraper = scraper

    def download_and_get_filename(
        self, src, output_path, with_ext=None, filter_ext=None
    ):
        """ downloads a file from src and return the name of the downloaded file

            with_ext: ensure that downloaded file has the given extension
            filter_ext: download only if the file to download has an extension in this list """

        if with_ext:
            ext = with_ext
        else:
            ext = pathlib.Path(urllib.parse.urlparse(src).path).suffix
        filename = hashlib.sha256(str(src).encode("utf-8")).hexdigest() + ext
        output_file = output_path.joinpath(filename)
        if filter_ext and ext not in filter_ext:
            return None, None
        fresh_download = False
        if not output_file.exists():
            self.scraper.download_file(
                prepare_url(src, self.scraper.instance_url), output_file,
            )
            fresh_download = True
        return filename, fresh_download

    def download_dependencies_from_css(
        self, css_org_url, content, folder, path_from_css
    ):
        """ Download all dependencies from CSS file contained in url()

            - css_org_url: URL to the CSS file on the internet
            - content: CSS text to rewrite
            - folder: “parent” folder of CSS to download files to
            - path_from_css: path of the supplied folder from CSS """

        def encapsulate(url):
            return f"url({url})"

        # ensure the original CSS url has netloc
        css_org_url = prepare_url(css_org_url, self.scraper.instance_url)
        css_org_url = urllib.parse.urlparse(css_org_url)

        # split whole content on `url()` pattern to retrieve a list composed of
        # alternatively pre-pattern text and inside url() –– actual target text
        parts = re.split(r"url\((.+?)\)", content)
        for index, _ in enumerate(parts):
            if index % 2 == 0:  # skip even lines (0, 2, ..) as those are CSS code
                continue
            css_url = parts[index]  # css_urls are on odd lines

            # remove potential quotes (can be none, single or double)
            if css_url[0] and css_url[-1] == "'":
                css_url = css_url[1:-1]
            if css_url[0] and css_url[-1] == '"':
                css_url = css_url[1:-1]

            # don't rewrite data: and empty URLs
            if re.match(r"^(://|data:|#)", css_url):
                parts[index] = encapsulate(css_url)
                continue

            # add netloc if not present
            parsed_url = urllib.parse.urlparse(css_url)
            if parsed_url.netloc == "":
                if parsed_url.path.startswith("/"):
                    css_url = self.scraper.instance_url + css_url
                else:
                    css_url = css_org_url.netloc + str(
                        pathlib.Path(css_org_url.path).parent.joinpath(css_url)
                    )

            # download the file
            filename, _ = self.download_and_get_filename(css_url, folder)
            fixed = filename if not path_from_css else f"{path_from_css}/{filename}"
            parts[index] = encapsulate(fixed)
        return "".join(parts)

    def download_images_from_html(self, html_body, output_path, path_from_html):
        """ download images from <img> tag and fix path """

        imgs = html_body.xpath("//img")
        for img in imgs:
            if "src" in img.attrib:
                filename, _ = self.download_and_get_filename(
                    src=img.attrib["src"], output_path=output_path
                )
                if filename:
                    img.attrib["src"] = (
                        f"{filename}"
                        if not path_from_html
                        else f"{path_from_html}/{filename}"
                    )
                    if "style" in img.attrib:
                        img.attrib["style"] += " max-width:100%"
                    else:
                        img.attrib["style"] = " max-width:100%"
        return bool(imgs)

    def download_documents_from_html(self, html_body, output_path, path_from_html):
        """ download documents from <a> tag and fix path """

        anchors = html_body.xpath("//a")
        for anchor in anchors:
            if "href" in anchor.attrib:
                filename, _ = self.download_and_get_filename(
                    src=anchor.attrib["href"],
                    output_path=output_path,
                    filter_ext=DOWNLOADABLE_EXTENSIONS,
                )
                if filename:
                    anchor.attrib["href"] = (
                        f"{filename}"
                        if not path_from_html
                        else f"{path_from_html}/{filename}"
                    )
        return bool(anchors)

    def download_css_from_html(self, html_body, output_path, path_from_html):
        """ download css files from <link> tag and fix path """

        css_files = html_body.xpath("//link")
        for css in css_files:
            if "href" in css.attrib:
                filename, fresh_download = self.download_and_get_filename(
                    src=css.attrib["href"], output_path=output_path
                )
                if filename:
                    if fresh_download:
                        css_fpath = output_path.joinpath(filename)
                        with open(css_fpath, "r") as fh:
                            fixed = self.download_dependencies_from_css(
                                css.attrib["href"],
                                fh.read(),
                                folder=css_fpath.parent,
                                path_from_css="",
                            )
                        with open(css_fpath, "w") as fh:
                            fh.write(fixed)
                    css.attrib["href"] = (
                        f"{filename}"
                        if not path_from_html
                        else f"{path_from_html}/{filename}"
                    )
        return bool(css_files)

    def download_js_from_html(self, html_body, output_path, path_from_html):
        """ download javascript from <script> tag and fix path """

        js_files = html_body.xpath("//script")
        for js in js_files:
            if "src" in js.attrib:
                filename, _ = self.download_and_get_filename(
                    src=js.attrib["src"], output_path=output_path
                )
                if filename:
                    js.attrib["src"] = (
                        f"{filename}"
                        if not path_from_html
                        else f"{path_from_html}/{filename}"
                    )
        return bool(js_files)

    def download_sources_from_html(self, html_body, output_path, path_from_html):
        """ downloads content from <source> tags """

        sources = html_body.xpath("//source")
        for source in sources:
            if "src" in source.attrib:
                filename, _ = self.download_and_get_filename(
                    src=source.attrib["src"], output_path=output_path
                )
                if filename:
                    source.attrib["src"] = (
                        f"{filename}"
                        if not path_from_html
                        else f"{path_from_html}/{filename}"
                    )
        return bool(sources)

    def download_iframes_from_html(self, html_body, output_path, path_from_html):
        """ download youtube videos and pdf files from iframes in html content """

        iframes = html_body.xpath("//iframe")
        for iframe in iframes:
            if "src" in iframe.attrib:
                src = iframe.attrib["src"]
                if "youtube" in src:
                    filename, _ = self.download_and_get_filename(
                        src=src,
                        output_path=output_path,
                        with_ext=f".{self.scraper.video_format}",
                    )
                    if filename:
                        x = jinja(
                            None,
                            "video.html",
                            False,
                            format=self.scraper.video_format,
                            video_path=f"{filename}"
                            if not path_from_html
                            else f"{path_from_html}/{filename}",
                            subs=[],
                            autoplay=self.scraper.autoplay,
                        )
                        iframe.getparent().replace(iframe, lxml.html.fromstring(x))
                elif ".pdf" in src:
                    filename, _ = self.download_and_get_filename(
                        src=src, output_path=output_path
                    )
                    if filename:
                        iframe.attrib["src"] = (
                            f"{filename}"
                            if not path_from_html
                            else f"{path_from_html}/{filename}"
                        )
        return bool(iframes)

    def handle_jump_to_paths(self, target_path):
        """ return a fixed path in zim for a inter-xblock path containing jump_to """

        def check_descendants_and_return_path(xblock_extractor):
            if xblock_extractor.xblock_json["type"] in ["vertical", "course"]:
                return xblock_extractor.relative_path + "/index.html"
            if not xblock_extractor.descendants:
                return None
            return check_descendants_and_return_path(xblock_extractor.descendants[0])

        for xblock_extractor in self.scraper.xblock_extractor_objects:
            if (xblock_extractor.xblock_json["block_id"] == target_path.parts[-1]) or (
                urllib.parse.urlparse(xblock_extractor.xblock_json["lms_web_url"]).path
                == str(target_path)
            ):
                # we have a path match, we now check xblock type to redirect properly
                # Only vertical and course xblocks have HTMLs
                return check_descendants_and_return_path(xblock_extractor)

    def rewrite_internal_links(self, html_body, output_path):
        """ rewrites internal links and ensures no root-relative links are left behind """

        def relative_dots(output_path):
            """ generates a relative path to root from the output path
                automatically detects the path of HTML in zim from output path """

            relative_path = output_path.resolve().relative_to(
                self.scraper.build_dir.resolve()
            )
            path_length = len(relative_path.parts)
            if path_length >= 5:
                # from a vertical, the root is 5 jumps deep
                return "../" * 5
            return "../" * path_length

        def update_root_relative_path(anchor, fixed_path, output_path):
            """ updates a root-relative path to the fixed path in zim
                if fixed path is not available, adds the instance url as its netloc """

            if fixed_path:
                anchor.attrib["href"] = relative_dots(output_path) + fixed_path
            else:
                anchor.attrib["href"] = (
                    self.scraper.instance_url + anchor.attrib["href"]
                )

        anchors = html_body.xpath("//a")
        path_prefix = f"{self.scraper.instance_config['course_prefix']}{urllib.parse.unquote_plus(self.scraper.course_id)}"
        has_changed = False
        for anchor in anchors:
            if "href" not in anchor.attrib:
                continue
            src = urllib.parse.urlparse(anchor.attrib["href"])

            # ignore external links
            if src.netloc and src.netloc != self.scraper.instance_url:
                continue

            # fix root-relative internal urls first
            if src.path.startswith(path_prefix):
                if "jump_to" in src.path:
                    # handle jump to paths (to an xblock)
                    src_path = pathlib.Path(src.path)
                    path_fixed = self.handle_jump_to_paths(src_path)
                    if not path_fixed:
                        # xblock may be one of those from which a vertical is consisted of
                        # thus check if the parent has the valid path
                        # we only need to check one layer deep as there's single layer of xblocks beyond vertical
                        path_fixed = self.handle_jump_to_paths(src_path.parent)
                    update_root_relative_path(anchor, path_fixed, output_path)
                    has_changed = True
                else:
                    # handle tab paths
                    _, tab_path = self.scraper.get_tab_path_and_name(
                        tab_text="", tab_href=src.path
                    )
                    update_root_relative_path(anchor, tab_path, output_path)
                    has_changed = True
                continue

            # fix root-relative path if not downloaded for zim
            if src.path.startswith("/"):
                update_root_relative_path(anchor, None, output_path)
                has_changed = True

        return has_changed

    def dl_dependencies_and_fix_links(self, content, output_path, path_from_html):
        """ downloads all static dependencies from an HTML content, and fixes links """

        html_body = lxml.html.fromstring(str(content))
        imgs = self.download_images_from_html(html_body, output_path, path_from_html)
        docs = self.download_documents_from_html(html_body, output_path, path_from_html)
        css_files = self.download_css_from_html(html_body, output_path, path_from_html)
        js_files = self.download_js_from_html(html_body, output_path, path_from_html)
        sources = self.download_sources_from_html(
            html_body, output_path, path_from_html
        )
        iframes = self.download_iframes_from_html(
            html_body, output_path, path_from_html
        )
        rewritten_links = self.rewrite_internal_links(html_body, output_path)
        if any([imgs, docs, css_files, js_files, sources, iframes, rewritten_links]):
            content = lxml.html.tostring(html_body, encoding="unicode")
        return content
