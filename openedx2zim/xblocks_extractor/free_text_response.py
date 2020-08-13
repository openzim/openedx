from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import jinja, get_back_jumps


class FreeTextResponse(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

        # extra vars
        self.html = ""

    def download(self, instance_connection):
        content = instance_connection.get_page(self.xblock_json["student_view_url"])
        if not content:
            return
        soup = BeautifulSoup(content, "lxml")
        html_content = soup.find("div", attrs={"class": "edx-notes-wrapper"})
        if not html_content:
            html_content = str(soup.find("div", attrs={"class": "course-wrapper"}))
        soup = BeautifulSoup(html_content, "lxml")
        text_area = soup.find("textarea", attrs={"class": "student_answer"})
        # check = soup.find("button", attrs={"class": "check"}).decompose()
        save = soup.find("button", attrs={"class": "save"})
        text_area["id"] = self.xblock_id
        # check["onclick"] = 'check_freetext("{}")'.format(self.id)
        save["onclick"] = 'save_freetext("{}")'.format(self.xblock_id)
        html_no_answers = '<div class="noanswers"><p data-l10n-id="no_answers_for_freetext" >  <b> Warning : </b> There is not correction for Freetext block. </p> </div>'
        self.html = (
            html_no_answers
            + self.scraper.html_processor.dl_dependencies_and_fix_links(
                content=str(soup),
                output_path=self.scraper.instance_assets_dir,
                path_from_html=get_back_jumps(5) + "instance_assets",
                root_from_html=get_back_jumps(5),
            )
        )

    def render(self):
        return jinja(
            None,
            "freetextresponse.html",
            False,
            freetextresponse_html=self.html,
            freetextresponse_id=self.xblock_id,
            mooc=self.scraper,
        )
