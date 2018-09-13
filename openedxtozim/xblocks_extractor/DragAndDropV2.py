import bs4 as BeautifulSoup
import os
from slugify import slugify
import json
from openedxtozim.utils import make_dir, jinja, download

class DragAndDropV2: #IMPROVEMENT We can only see it, not interracting with it
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.output_path=self.mooc.output_path
        self.folder_name = slugify(json["display_name"])
        self.output_path = os.path.join(self.mooc.output_path,self.path)
        make_dir(self.output_path)

    def download(self, c):
        content=c.get_page(self.json["student_view_url"])
        soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
        self.content=json.loads(soup.find('script', attrs={"class": "xblock-json-init-args"}).get_text())
        #item
        for item in self.content["items"]:
            name=os.path.basename(item["expandedImageURL"])
            download(item["expandedImageURL"], os.path.join(self.output_path,name),self.mooc.instance_url)
            item["expandedImageURL"]=os.path.join(self.folder_name,name)
        #Grid
        name=os.path.basename(self.content["target_img_expanded_url"])
        download(self.content["target_img_expanded_url"], os.path.join(self.output_path,name),self.mooc.instance_url)
        self.content["target_img_expanded_url"]=os.path.join(self.folder_name,name)

    def render(self):
            return jinja(
                None,
                "DragAndDropV2.html",
                False,
                DragDrop=self
            )

