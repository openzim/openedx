from openedxtozim.utils import make_dir
import os
from slugify import slugify
class Html:
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
            html_content=str(soup.find('div', attrs={"class": "edx-notes-wrapper"}))
            if html_content=="None":
                html_content=str(soup.find('div', attrs={"class": "course-wrapper"}))
            html_content=dl_dependencies(html_content,path,data[block_id_id],instance_url)
            data["html_content"]=str(html_content)
        """
    def render(self):
            return "TODO"

