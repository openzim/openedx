from openedxtozim.utils import make_dir
import os
from slugify import slugify
class Discussion:
    is_video = False
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.output_path=self.mooc.output_path
        path = os.path.join(self.output_path,self.path,slugify(json["display_name"]))
        make_dir(path)

    def download(self,c):
        return
        """
            content=get_page(data["student_view_url"],headers).decode('utf-8')
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            discussion_id=str(soup.find('div', attrs={"class": "discussion-module"})['data-discussion-id'])
            minimal_discussion=get_api_json(instance_url,"/courses/" + course_id + "/discussion/forum/" + discussion_id + "/inline?page=1&ajax=1", headers)
            data["discussion"]={}
            data["discussion"]["discussion_data"]=minimal_discussion["discussion_data"]
            if minimal_discussion["num_pages"] != 1:
                for i in range(2,minimal_discussion["num_pages"]+1):
                    data["discussion"]["discussion_data"]+=get_api_json(instance_url,"/courses/" + course_id + "/discussion/forum/" + discussion_id + "/inline?page=" + str(i) + "&ajax=1", headers)["discussion_data"]
        """
    def render(self):
            return "TODO when we support annexe content"


