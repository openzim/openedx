from bs4 import BeautifulSoup

from .base_xblock import BaseXblock


class Html(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

        self.is_video = False  # check this
        self.html = ""

    def download(self, instance_connection):
        content = instance_connection.get_page(self.xblock_json["student_view_url"])
        if not content:
            return
        soup = BeautifulSoup(content, "lxml")
        html_content = soup.find("div", attrs={"class": "edx-notes-wrapper"})
        if not html_content:
            html_content = str(soup.find("div", attrs={"class": "course-wrapper"}))
        self.html = self.scraper.dl_dependencies(
            content=html_content,
            output_path=self.output_path,
            path_from_html=self.folder_name,
        )

    def render(self):
        return self.html