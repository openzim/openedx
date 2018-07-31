import bs4 as BeautifulSoup
import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja, dl_dependencies

class FreeTextResponse:
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.is_video=True
        self.folder_name = slugify(json["display_name"])
        self.output_path = os.path.join(self.mooc.output_path,self.path)
        make_dir(self.output_path)

    def download(self, c):
        content=c.get_page(self.json["student_view_url"])
        soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
        html_content=soup.find('div', attrs={"class": "edx-notes-wrapper"})
        if html_content== None:
            html_content=str(soup.find('div', attrs={"class": "course-wrapper"}))
        soup=BeautifulSoup.BeautifulSoup(html_content, "html.parser")
        text_area=soup.find("textarea", attrs={"class": "student_answer"})
        check=soup.find("button", attrs={"class": "check"})
        save=soup.find("button", attrs={"class": "save"})
        text_area["id"] = self.id
        check["onclick"] = 'check_freetext("{}")'.format(self.id)
        save["onclick"] = 'save_freetext("{}")'.format(self.id)
        self.html=dl_dependencies(str(soup),self.output_path, self.folder_name, c)

    def render(self):
            return jinja(
                None,
                "freetextresponse.html",
                False,
                freetextresponse=self,
                mooc=self.mooc
            )
