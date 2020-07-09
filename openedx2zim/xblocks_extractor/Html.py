from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import dl_dependencies


class Html(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

        self.is_video = False  # check this
        self.html = ""

    def download(self, instance_connection):
        content = instance_connection.get_page(self.xblock_json["student_view_url"])
        soup = BeautifulSoup(content, "lxml")
        html_content = soup.find("div", attrs={"class": "edx-notes-wrapper"})
        if not html_content:
            html_content = str(soup.find("div", attrs={"class": "course-wrapper"}))
        self.html = dl_dependencies(
            html_content,
            self.output_path,
            self.folder_name,
            instance_connection,
            self.scraper,
        )

    def render(self):
        return self.html
