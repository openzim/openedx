import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja

class Course:
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.descendants=descendants
        self.top=self.mooc.top
        self.output_path=self.mooc.output_path
        self.display_name=json["display_name"]
        self.folder_name=slugify(self.display_name)
        path = os.path.join(self.output_path,self.path,self.folder_name)
        make_dir(path)

    def download(self,c):
        for x in self.descendants:
            x.download(c)


    def render(self):
        for x in range(0,len(self.descendants)):
            if x==0:
                pred_info=None
            else:
                pred_info=self.descendants[x-1].get_last()
            if x+1==len(self.descendants):
                next_info=None
            else:
                next_info=self.descendants[x+1].get_first()
            self.descendants[x].render(pred_info,next_info)
        if len(self.descendants) == 0:
            logging.warning("This course has no content")
        else:
            jinja(
                os.path.join(self.output_path,self.path,"index.html"),
                "course_menu.html",
                False,
                course=self,
                rooturl=self.rooturl,
                mooc=self.mooc,
		all_side_menu_open=True,
                display_on_mobile=True
            )
