import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja

class Vertical:
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.descendants=descendants
        self.top=self.mooc.top
        self.output_path=self.mooc.output_path
        if self.json["block_counts"]["video"] != 0:
            self.icon_type="fa-video-camera"
        elif self.json["block_counts"]["problem"] != 0:
            self.icon_type="fa-question-circle"
        elif self.json["block_counts"]["discussion"] != 0:
            self.icon_type="fa-comment"
        else:
            self.icon_type="fa-book"

        self.display_name=json["display_name"]
        self.folder_name=slugify(self.display_name)
        path = os.path.join(self.output_path,self.path,self.folder_name)
        make_dir(path)

    def download(self,c):
        for x in self.descendants:
            x.download(c)

    def render(self,pred_vertical,next_vertical,chapter,sequential):
        vertical=[]
        video=False
        for x in self.descendants:
            vertical.append(x.render())
        jinja(
            os.path.join(self.output_path,self.path,"index.html"),
            "vertical.html",
            False,
            rooturl=self.rooturl,
            mooc=self.mooc,
            chapter=chapter,
            sequential=sequential,
            vertical=self,
            extracted_id=self.json["id"].split("@")[-1],
            vertical_content=vertical,
            pred_vertical=pred_vertical,
            next_vertical=next_vertical,
            side_menu=True
        )

