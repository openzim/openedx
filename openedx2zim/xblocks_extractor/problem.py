import json
import uuid

from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import jinja, get_back_jumps
from ..constants import getLogger


logger = getLogger()


class Problem(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

        # extra vars
        self.is_video = False
        self.problem_header = ""
        self.html_content = ""
        self.answers = []
        self.explanation = []
        self.problem_id = None

    def get_answers(self, instance_connection):
        # get the answers
        answers_path = self.output_path.joinpath("problem_show")
        answers_content = {"success": None}
        retry = 0
        while "success" in answers_content and retry < 6:
            # query the instance to get answers
            answers_content = instance_connection.get_api_json(
                "/courses/"
                + self.scraper.course_id
                + "/xblock/"
                + self.xblock_json["id"]
                + "/handler/xmodule_handler/problem_show"
            )
            if "success" in answers_content:
                instance_connection.get_api_json(
                    "/courses/"
                    + self.scraper.course_id
                    + "/xblock/"
                    + self.xblock_json["id"]
                    + "/handler/xmodule_handler/problem_check"
                )
                retry += 1
        if "success" in answers_content:
            logger.warning(
                " fail to get answers to this problem : "
                + self.xblock_json["id"]
                + " ("
                + self.xblock_json["lms_web_url"]
                + ")"
            )
            self.answers = None
        else:
            with open(answers_path, "w") as f:
                json.dump(answers_content, f)
            for qid in answers_content["answers"]:
                if "solution" not in qid:
                    for response in answers_content["answers"][qid]:
                        self.answers.append("input_" + qid + "_" + response)
                else:
                    self.explanation.append(
                        {
                            "name": "solution_" + qid,
                            "value": json.dumps(answers_content["answers"][qid]),
                        }
                    )
            self.problem_id = str(uuid.uuid4())

    def download(self, instance_connection):
        content = instance_connection.get_page(self.xblock_json["student_view_url"])
        if not content:
            return
        raw_soup = BeautifulSoup(content, "lxml")
        try:
            html_content_from_div = str(
                raw_soup.find("div", attrs={"class": "problems-wrapper"})[
                    "data-content"
                ]
            )
        except Exception:
            problem_json_url = str(
                raw_soup.find("div", attrs={"class": "problems-wrapper"})["data-url"]
            )
            html_content_from_div = str(
                instance_connection.get_api_json(problem_json_url + "/problem_get")[
                    "html"
                ]
            )
        soup = BeautifulSoup(html_content_from_div, "lxml")

        # remove all notifications
        for div in soup.find_all("div", attrs={"class": "notification"}):
            div.decompose()

        # clear all inputs
        for input_tag in soup.find_all("input"):
            if input_tag.has_attr("value"):
                input_tag["value"] = ""
            if input_tag.has_attr("checked"):
                del input_tag.attrs["checked"]

        # remove action bar (contains the submission button)
        soup.find("div", attrs={"class": "action"}).decompose()
        for span in soup.find_all("span", attrs={"class": "unanswered"}):
            span.decompose()
        for span in soup.find_all("span", attrs={"class": "sr"}):
            span.decompose()

        self.problem_header = str(soup.find("h3", attrs={"class": "problem-header"}))

        # process final HTML content
        html_content = self.scraper.html_processor.dl_dependencies_and_fix_links(
            content=str(soup.find("div", attrs={"class": "problem"})),
            output_path=self.scraper.instance_assets_dir,
            path_from_html=get_back_jumps(5) + "instance_assets",
            root_from_html=get_back_jumps(5),
        )

        # defer scripts in the HTML as they sometimes are inline and tend
        # to access content below them
        html_content = self.scraper.html_processor.defer_scripts(
            content=html_content,
            output_path=self.output_path,
            path_from_html=self.folder_name,
        )

        # save the content
        self.html_content = str(html_content)
        self.get_answers(instance_connection)

    def render(self):
        return jinja(None, "problem.html", False, problem=self)
