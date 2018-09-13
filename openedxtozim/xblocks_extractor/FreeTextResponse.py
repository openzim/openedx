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
        self.folder_name = slugify(json["display_name"])
        self.output_path = os.path.join(self.mooc.output_path,self.path)
        make_dir(self.output_path)

    def download(self, c):
        content=c.get_page(self.json["student_view_url"])
        soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
        html_content=soup.find('div', attrs={"class": "edx-notes-wrapper"})
        if html_content== None:
            html_content=str(soup.find('div', attrs={"class": "course-wrapper"}))
        soup=BeautifulSoup.BeautifulSoup(html_content, "lxml")
        text_area=soup.find("textarea", attrs={"class": "student_answer"})
        check=soup.find("button", attrs={"class": "check"}).decompose()
        save=soup.find("button", attrs={"class": "save"})
        text_area["id"] = self.id
        #check["onclick"] = 'check_freetext("{}")'.format(self.id)
        save["onclick"] = 'save_freetext("{}")'.format(self.id)
        html_no_answers='<div class="noanswers"><p data-l10n-id="no_answers_for_freetext" >  <b> Warning : </b> There is not correction for Freetext block. </p> </div>'
        self.html=html_no_answers + dl_dependencies(str(soup),self.output_path, self.folder_name, c)

    def render(self):
            return jinja(
                None,
                "freetextresponse.html",
                False,
                freetextresponse=self,
                mooc=self.mooc
            )
