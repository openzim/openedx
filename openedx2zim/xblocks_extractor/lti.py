from bs4 import BeautifulSoup

from .base_xblock import BaseXblock

from ..utils import prepare_url


class Lti(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

    def download(self, instance_connection):
        # IMPROUVEMENT LTI can be lot of content type ? Here pdf
        url = (
            self.xblock_json["lms_web_url"].replace("/jump_to/", "/xblock/")
            + "/handler/preview_handler"
        )
        content = instance_connection.get_page(url)
        if not content:
            return
        soup = BeautifulSoup(content, "lxml")
        content_url = soup.find("form")
        self.scraper.download_file(
            prepare_url(content_url["action"], self.scraper.instance_url),
            self.output_path.joinpath("content.pdf"),
        )

    def render(self):
        return (
            """<p data-l10n-id='download_lti' data-l10n-args="{ 'url': '{"""
            + f"{self.folder_name}/content.pdf"
            + """}' }"> This content can be download <a href='{"""
            + f"{self.folder_name}/content.pdf"
            + """}'> here </a>"""
        )
