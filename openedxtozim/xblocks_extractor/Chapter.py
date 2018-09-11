import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja
class Chapter:

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

    def render(self,pred_info,next_info):
        for x in range(0,len(self.descendants)): 
            if x==0: #We search for previous vertical
                pred=pred_info
            else:
                pred=self.descendants[x-1].get_last()

            if x+1==len(self.descendants): #We search for next vertical
                next=next_info
            else:
                next=self.descendants[x+1].get_first()
            self.descendants[x].render(pred,next,self)

    def get_first(self):
        if len(self.descendants) != 0:
            return self.descendants[0].get_first()
        else:
            return None

    def get_last(self):
        if len(self.descendants) != 0:
            return self.descendants[-1].get_last()
        else:
            return None
