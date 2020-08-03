from .base_xblock import BaseXblock
from bs4 import BeautifulSoup
from ..utils import jinja
import html


class Vertical(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )
        self.extra_head_content = []
        self.body_end_scripts = []
        self.verts = []

        # set icon
        if self.xblock_json["block_counts"]["video"] != 0:
            self.icon_type = "fa-video"
        elif self.xblock_json["block_counts"]["problem"] != 0:
            self.icon_type = "fa-question-circle"
        elif self.xblock_json["block_counts"]["discussion"] != 0:
            self.icon_type = "fa-comment"
        else:
            self.icon_type = "fa-book"

    def remove_head_and_html_tags(self, html_string):
        """ removes <head> and <html> tags from endpoints of a string """
        if html_string.startswith("<html>"):
            html_string = html_string[6:]
        if html_string.endswith("</html>"):
            html_string = html_string[:-7]
        if html_string.startswith("<head>"):
            html_string = html_string[6:]
        if html_string.endswith("</head>"):
            html_string = html_string[:-7]
        return html_string

    def download(self, instance_connection):
        instance_assets_path = self.scraper.build_dir.joinpath("instance_assets")
        instance_assets_path.mkdir(parents=True, exist_ok=True)

        # get the LMS content for the vertical
        content = instance_connection.get_page(self.xblock_json["lms_web_url"])
        soup = BeautifulSoup(content, "lxml")

        # extract CSS and JS from HTML head
        html_headers = soup.find("head")
        head_css_js = (
            html_headers.find_all("script")
            + html_headers.find_all("link", attrs={"rel": "stylesheet"})
            + html_headers.find_all("style")
        )
        for header_element in head_css_js:
            self.extra_head_content.append(
                self.remove_head_and_html_tags(
                    self.scraper.html_processor.dl_dependencies_and_fix_links(
                        content=str(header_element),
                        output_path=instance_assets_path,
                        path_from_html=f"{self.root_url}instance_assets",
                        root_from_html=self.root_url,
                    )
                )
            )

        # extract scripts at the end of body
        html_body = soup.find("body")
        body_scripts = html_body.find_all("script")
        for script in body_scripts:
            self.body_end_scripts.append(
                self.remove_head_and_html_tags(
                    self.scraper.html_processor.dl_dependencies_and_fix_links(
                        content=str(script),
                        output_path=instance_assets_path,
                        path_from_html=f"{self.root_url}instance_assets",
                        root_from_html=self.root_url,
                    )
                )
            )

        # download content from descendants
        for x in self.descendants:
            x.download(instance_connection)

        # get divs with class vert as those contain extra CSS classes to be applied at render step
        seq_contents = soup.find_all("div", attrs={"class": "seq_contents"})
        for content in seq_contents:
            unescaped_html = html.unescape(content.string)
            new_soup = BeautifulSoup(unescaped_html, "lxml")
            self.verts += new_soup.find_all("div", attrs={"class": "vert"})

    def render(self, prev_vertical, next_vertical, chapter, sequential):
        vertical = []
        for x in self.descendants:
            extra_vert_classes = []
            for vert_div in self.verts:
                if x.xblock_json["id"] == vert_div.attrs["data-id"]:
                    extra_vert_classes = vert_div.attrs["class"]
                    extra_vert_classes.remove("vert")
            start = '<div class="vert ' + " ".join(extra_vert_classes) + '">'
            end = "</div>"
            vertical.append(start + x.render() + end)

        jinja(
            self.output_path.joinpath("index.html"),
            "vertical.html",
            False,
            vertical_content=vertical,
            extra_headers=self.extra_head_content,
            body_scripts=self.body_end_scripts,
            vertical=self,
            mooc=self.scraper,
            chapter=chapter,
            sequential=sequential,
            extracted_id=self.xblock_json["id"].split("@")[-1],
            prev_vertical=prev_vertical,
            next_vertical=next_vertical,
            side_menu=True,
            rooturl=self.root_url,
        )
