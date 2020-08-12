import json
import uuid
import itertools
import urllib

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

    def check_problem_type_and_get_options(self, problem_tag):
        """ returns whether answers are fetchable for a problem, if yes, also returns whether the problem
            has single correct answers, and a list of options for answers """

        single_answer_correct_options = problem_tag.find_all("input", attrs={"type": "radio"})
        if len(single_answer_correct_options) > 1:
            return True, True, single_answer_correct_options
        multi_answer_correct_options = problem_tag.find_all("input", attrs={"type": "checkbox"})
        if len(multi_answer_correct_options) > 1 and len(multi_answer_correct_options) <= 5:
            return True, False, multi_answer_correct_options
        return False, None, None

    def get_answers(self, instance_connection, problem_tag, xmodule_handler):

        def check_result(answer_candidate):
            post_data = ""
            for candidate in answer_candidate:
                if post_data == "":
                    post_data = f"{candidate.attrs.get('name')}={candidate.attrs.get('value')}"
                else:
                    post_data = post_data + f"&{candidate.attrs.get('name')}={candidate.attrs.get('value')}"
            post_data = urllib.parse.urlencode(post_data).encode('utf-8')
            instance_connection.get_api_json(f"{xmodule_handler}/problem_check", post_data, referrer="")

        answers_fetchable, single_correct, options_list = self.check_problem_type_and_get_options(problem_tag)
        if answers_fetchable:
            if single_correct:
                # fetch answer for single correct question
                answer_found = False
                for answer_candidate in options_list:
                    if answer_found:
                        # mark this wrong
                        continue
                    correct = check_result([answer_candidate])
                    if correct:
                        answer_found = True
                        # mark this correct

            else:
                # fetch answer for multiple correct question
                answer_found = False
                for r in range(1, len(options_list) + 1):
                    for answer_candidate in itertools.combinations(options_list, r):
                        if answer_found:
                            # mark this wrong
                            continue                       
                        correct = check_result(answer_candidate)
                        if correct:
                            answer_found = True
                            # mark this correct

        else:
            logger.warning("Answer fetching for this type of problem is not supported")

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
        xmodule_handler = str(
                raw_soup.find("div", attrs={"class": "problems-wrapper"})["data-url"]
            )
        try:
            html_content_from_div = str(
                raw_soup.find("div", attrs={"class": "problems-wrapper"})[
                    "data-content"
                ]
            )
        except Exception:
            html_content_from_div = str(
                instance_connection.get_api_json(xmodule_handler + "/problem_get")[
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

        problem_tag = soup.find("div", attrs={"class": "problem"})
        self.get_answers(instance_connection, problem_tag, xmodule_handler)

        # process final HTML content
        html_content = self.scraper.html_processor.dl_dependencies_and_fix_links(
            content=str(),
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

    def render(self):
        return jinja(None, "problem.html", False, problem=self)
