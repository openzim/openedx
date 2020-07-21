import json
import uuid

from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import jinja
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
        self.html_content = ""
        self.answers = []
        self.explanation = []
        self.problem_id = None

    def download(self, instance_connection):
        content = instance_connection.get_page(self.xblock_json["student_view_url"])
        if not content:
            return
        soup = BeautifulSoup(content, "lxml")
        try:
            html_content_from_div = str(
                soup.find("div", attrs={"class": "problems-wrapper"})["data-content"]
            )
        except Exception:
            problem_json_url = str(
                soup.find("div", attrs={"class": "problems-wrapper"})["data-url"]
            )
            html_content_from_div = str(
                instance_connection.get_api_json(problem_json_url + "/problem_get")[
                    "html"
                ]
            )
        soup = BeautifulSoup(html_content_from_div, "lxml")
        # self.has_hint=soup.find("button", attrs={"class" : "hint-button"}) #Remove comment when  hint ok
        for div in soup.find_all("div", attrs={"class": "notification"}):
            div.decompose()
        for input_tag in soup.find_all("input"):
            if input_tag.has_attr("value"):
                input_tag["value"] = ""
            if input_tag.has_attr("checked"):
                del input_tag.attrs["checked"]
        soup.find("div", attrs={"class": "action"}).decompose()
        for span in soup.find_all("span", attrs={"class": "unanswered"}):
            span.decompose()
        for span in soup.find_all("span", attrs={"class": "sr"}):
            span.decompose()
        html_content = str(soup)
        html_content = self.scraper.html_processor.dl_dependencies_and_fix_links(
            content=html_content,
            output_path=self.output_path,
            path_from_html=self.folder_name,
        )
        self.html_content = str(html_content)

        # Save json answers
        answers_path = self.output_path.joinpath("problem_show")
        answers_content = {"success": None}
        retry = 0
        while (
            "success" in answers_content and retry < 6
        ):  # We use our check to finally get anwers
            answers_content = instance_connection.get_api_json(
                "/courses/"
                + self.scraper.course_id
                + "/xblock/"
                + self.xblock_json["id"]
                + "/handler/xmodule_handler/problem_show"
            )
            if "success" in answers_content:
                """
                    #IMPROVEMENT instance_connection , same as hint ?
                    post_data=urlencode({'event_type': "problem_show", "event": { "problem": self.json["id"] }, "page" : self.json["lms_web_url"]}).encode('utf-8')
                    instance_connection.get_api_json("/event", post_data) """
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

        """
            #HINT fix it !
            if self.has_hint:
                self.hint = []
                hint_index=0
                referer=self.mooc.instance_url + "/courses/" + self.mooc.course_id + "/?activate_block_id=" + self.json["id"]
                referer=self.json["lms_web_url"] + "/?activate_block_id=" + self.json["id"]
                post_data=urlencode({'hint_index': hint_index, 'input_id': self.json["id"]}).encode('utf-8')
                url_hint = "/courses/" + self.mooc.course_id + "/xblock/" + self.json["id"] + "/handler/xmodule_handler/hint_button"
                get_info=instance_connection.get_api_json(url_hint, post_data, referer)
                if "success" in get_info:
                    self.hint.append(get_info)
                    hint_index+=1
                    while hint_index < get_info["total_possible"]:
                        post_data=urlencode({'hint_index': hint_index,'input_id': self.json["id"]}).encode('utf-8')
                        get_info=instance_connection.get_api_json("/courses/" + self.mooc.course_id + "/xblock/" + self.json["id"] + "/handler/xmodule_handler/hint_button", post_data, referer)
                        if "success" in get_info:
                            self.hint.append(get_info)
                        hint_index+=1
            """

    def render(self):
        return jinja(None, "problem.html", False, problem=self)
