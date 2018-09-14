import bs4 as BeautifulSoup
import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja, download

class Lti:
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
        #IMPROUVEMENT LTI can be lot of content type ? Here pdf
        url = self.json["lms_web_url"].replace("/jump_to/","/xblock/") + "/handler/preview_handler"
        content=c.get_page(url)
        soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
        content_url=soup.find('form')
        download(content_url["action"],os.path.join(self.output_path,"content.pdf"),c)

    def render(self):
            return """<p data-l10n-id='download_lti' data-l10n-args="{ 'url': '{""" + os.path.join(self.folder_name,"content.pdf") + """}' }"> This content can be download <a href='{""" + os.path.join(self.folder_name,"content.pdf") + """}'> here </a>"""
