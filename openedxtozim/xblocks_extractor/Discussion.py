import os
import re
import bs4 as BeautifulSoup
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
        if self.mooc.forum_thread != None:
            content=c.get_page(self.json["student_view_url"])
            soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
            discussion_block=soup.find(re.compile(r".*") , {"data-discussion-id" : re.compile(r".*")})
            if discussion_block != None:
                discussion_id=discussion_block["data-discussion-id"]
                for thread in self.mooc.forum_thread:
                    if thread["commentable_id"] == discussion_id :
                        self.data.append(thread)
                if len(self.data) != 0:
                    self.category_title=self.mooc.forum_category[discussion_id]

    def render(self):
        if self.category_title != "":
            return jinja(
                None,
                "discussion.html",
                False,
                category_title=self.category_title,
                threads=self.data,
                discussion=self,
                staff_user=self.mooc.staff_user_forum,
                rooturl="/".join(self.rooturl.split("/")[:-1]) #rooturl - 1 folder
            )
        else:
            return "This discussion is not supported, sorry !"

