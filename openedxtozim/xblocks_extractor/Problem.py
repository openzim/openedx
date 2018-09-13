import bs4 as BeautifulSoup
import os
from slugify import slugify
import logging
import json
from uuid import uuid4
from urllib.parse import urlencode
from openedxtozim.utils import make_dir, jinja, dl_dependencies

class Problem:
    is_video = False
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.folder_name = slugify(json["display_name"])
        self.output_path = os.path.join(self.mooc.output_path,self.path)
        make_dir(self.output_path)

    def download(self,c):
            content=c.get_page(self.json["student_view_url"])
            soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
            try:
                html_content_from_div=str(soup.find('div', attrs={"class": "problems-wrapper"})['data-content'])
            except:
                problem_json_url=str(soup.find('div', attrs={"class": "problems-wrapper"})['data-url'])
                html_content_from_div=str(c.get_api_json(problem_json_url+"/problem_get")["html"])
            soup=BeautifulSoup.BeautifulSoup(html_content_from_div, 'lxml')
            #self.has_hint=soup.find("button", attrs={"class" : "hint-button"}) #Remove comment when  hint ok
            for div in soup.find_all('div', attrs={"class": "notification"}):
                div.decompose()
            for input_tag in soup.find_all('input'):
                if input_tag.has_attr("value"):
                    input_tag["value"]=""
                if input_tag.has_attr("checked"):
                        del input_tag.attrs['checked']
            soup.find('div', attrs={"class": "action"}).decompose()
            for span in soup.find_all('span', attrs={"class" : "unanswered"}):
                span.decompose()
            for span in soup.find_all('span', attrs={"class" : "sr"}):
                span.decompose()
            html_content=str(soup)
            html_content=dl_dependencies(html_content,self.output_path,self.folder_name,c)
            self.html_content=str(html_content)

            #Save json answers
            path_answers=os.path.join(self.output_path,"problem_show")
            answers_content={"success": None}
            retry=0
            while "success" in answers_content and retry < 6: #We use our check to finally get anwers
                answers_content=c.get_api_json("/courses/" + self.mooc.course_id + "/xblock/" + self.json["id"] + "/handler/xmodule_handler/problem_show")
                if "success" in answers_content:
                    """
                    #IMPROUVEMENT connection , same as hint ?
                    post_data=urlencode({'event_type': "problem_show", "event": { "problem": self.json["id"] }, "page" : self.json["lms_web_url"]}).encode('utf-8')
                    c.get_api_json("/event", post_data)
                    """
                    c.get_api_json("/courses/" + self.mooc.course_id + "/xblock/" + self.json["id"] + "/handler/xmodule_handler/problem_check")
                    retry+=1
            if "success" in answers_content:
                logging.warning(" fail to get answers to this problem : " + self.json["id"] + " (" + self.json["lms_web_url"]  + ")")
                self.answers=None
            else:
                with open(path_answers,"w") as f:
                    json.dump(answers_content, f)
                self.answers=[]
                self.explanation=[]
                for qid in answers_content["answers"]:
                    if not "solution" in qid:
                        for response in answers_content["answers"][qid]:
                            self.answers.append("input_" + qid + "_" + response)
                    else:
                        self.explanation.append({ "name": "solution_" + qid, "value": json.dumps(answers_content["answers"][qid])})
                self.problem_id=str(uuid4())

            """
            #HINT fix it !
            if self.has_hint:
                self.hint = []
                hint_index=0
                referer=self.mooc.instance_url + "/courses/" + self.mooc.course_id + "/?activate_block_id=" + self.json["id"]
                referer=self.json["lms_web_url"] + "/?activate_block_id=" + self.json["id"]
                post_data=urlencode({'hint_index': hint_index, 'input_id': self.json["id"]}).encode('utf-8')
                url_hint = "/courses/" + self.mooc.course_id + "/xblock/" + self.json["id"] + "/handler/xmodule_handler/hint_button"
                get_info=c.get_api_json(url_hint, post_data, referer)
                if "success" in get_info:
                    self.hint.append(get_info)
                    hint_index+=1
                    while hint_index < get_info["total_possible"]:
                        post_data=urlencode({'hint_index': hint_index,'input_id': self.json["id"]}).encode('utf-8')
                        get_info=c.get_api_json("/courses/" + self.mooc.course_id + "/xblock/" + self.json["id"] + "/handler/xmodule_handler/hint_button", post_data, referer)
                        if "success" in get_info:
                            self.hint.append(get_info)
                        hint_index+=1
            """

    def render(self):
            return jinja(
                None,
                "problem.html",
                False,
                problem=self
            )



