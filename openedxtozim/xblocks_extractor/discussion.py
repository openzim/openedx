import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja
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
        self.data=[]
        self.category_title=""

    def download(self,c):
        if self.mooc.forum_thread != None and "topic_id" in self.json["student_view_data"] :
            for thread in self.mooc.forum_thread:
                if thread["category_id"] == self.json["student_view_data"]["topic_id"]:
                    self.data.append(thread)
            self.category_title=self.mooc.forum_category[self.json["student_view_data"]["topic_id"]]

    def render(self):
        if self.category_title != "":
            return jinja(
                None,
                "discussion.html",
                False,
                category_title=self.category_title,
                threads=self.data,
                discussion=self
            )
        else:
            return "This discussion is not supported, sorry !"

