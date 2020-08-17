import html

from bs4 import BeautifulSoup

from ..utils import jinja
from .base_xblock import BaseXblock


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

    def download(self, instance_connection):
        # get the LMS content for the vertical
        content = instance_connection.get_page(self.xblock_json["lms_web_url"])
        soup = BeautifulSoup(content, "lxml")

        # extract CSS and JS from HTML head
        self.extra_head_content = self.scraper.html_processor.extract_head_css_js(
            soup=soup,
            output_path=self.scraper.instance_assets_dir,
            path_from_html=f"{self.root_url}instance_assets",
            root_from_html=self.root_url,
        )

        # extract scripts at the end of body
        self.body_end_scripts = self.scraper.html_processor.extract_body_end_scripts(
            soup=soup,
            output_path=self.scraper.instance_assets_dir,
            path_from_html=f"{self.root_url}instance_assets",
            root_from_html=self.root_url,
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
