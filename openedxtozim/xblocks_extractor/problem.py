from openedxtozim.utils import make_dir
import os
from slugify import slugify
class Problem:
    is_video = False
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.descendants=descendants
        self.top=self.mooc.top
        self.output_path=self.mooc.output_path
        path = os.path.join(self.output_path,self.path,slugify(json["display_name"]))
        make_dir(path)

    def download(self,c):
        return
        """
            content=get_page(data["student_view_url"],headers).decode('utf-8')
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            try:
                html_content_from_div=str(soup.find('div', attrs={"class": "problems-wrapper"})['data-content'])
            except:
                problem_json_url=str(soup.find('div', attrs={"class": "problems-wrapper"})['data-url'])
                html_content_from_div=str(get_api_json(instance_url,problem_json_url+"/problem_get",headers)["html"])
            soup=BeautifulSoup.BeautifulSoup(html_content_from_div, 'html.parser')
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
            html_content=dl_dependencies(html_content,path,data[block_id_id],instance_url)
            data["html_content"]=str(html_content)

            #Save json answers
            path_answers=os.path.join(path,"problem_show")
            answers_content={"success": None}
            retry=0
            while "success" in answers_content and retry < 6: #We use our check to finally get anwers
                answers_content=get_api_json(instance_url,"/courses/" + course_id + "/xblock/" + data["block_name"] + "/handler/xmodule_handler/problem_show", headers)
                if "success" in answers_content:
                    get_api_json(instance_url,"/courses/" + course_id + "/xblock/" + data["block_name"] + "/handler/xmodule_handler/problem_check", headers)
                    retry+=1
            if "success" in answers_content:
                logging.warning(" fail to get answers to this problem : " + data["block_name"])
                data["answers"]=None
            else:
                with open(path_answers,"w") as f:
                    json.dump(answers_content, f)
                data["answers"]=[]
                data["explanation"]=[]
                for qid in answers_content["answers"]:
                    if not "solution" in qid:
                        for response in answers_content["answers"][qid]:
                            data["answers"].append("input_" + qid + "_" + response)
                    else:
                        data["explanation"].append({ "name": "solution_" + qid, "value": json.dumps(answers_content["answers"][qid])})
                data["problem_id"]=sha256(str(random.random()).encode('utf-8')).hexdigest()
            """

    def render(self):
            return "TODO"



