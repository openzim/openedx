from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import download


class Lti(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

    def download(self, c):
        # IMPROUVEMENT LTI can be lot of content type ? Here pdf
        url = (
            self.xblock_json["lms_web_url"].replace("/jump_to/", "/xblock/")
            + "/handler/preview_handler"
        )
        content = c.get_page(url)
        soup = BeautifulSoup(content, "lxml")
        content_url = soup.find("form")
        download(
            content_url["action"], self.output_path.joinpath("content.pdf"), c
        )

    def render(self):
        return (
            """<p data-l10n-id='download_lti' data-l10n-args="{ 'url': '{"""
            + f"{self.folder_name}/content.pdf"
            + """}' }"> This content can be download <a href='{"""
            + f"{self.folder_name}/content.pdf"
            + """}'> here </a>"""
        )
