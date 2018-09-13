import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja

class QualtricsSurvey: #Replace by Html
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
      return

    def render(self):
      return '<div class="not_available">  <p data-l10n-id="not_available" >  <b> Info : </b> Not available offline. </p></div>'
