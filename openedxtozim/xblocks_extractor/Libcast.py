import bs4 as BeautifulSoup
import os
from slugify import slugify
from openedxtozim.utils import make_dir, jinja,download_and_convert_subtitles, download,convert_video_to_webm

class Libcast:
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.path=path
        self.rooturl=rooturl
        self.json=json
        self.id=id
        self.folder_name=slugify(json["display_name"])
        self.output_path = os.path.join(self.mooc.output_path,self.path)
        make_dir(self.output_path)

    def download(self,c):
        self.subs=[]
        content=c.get_page(self.json["student_view_url"])
        soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
        url=str(soup.find('video').find('source')["src"])
        subs=soup.find('video').find_all('track')
        if len(subs) != 0:
            subs_lang = {}
            for track in subs:
                if track["src"][0:4] == "http":
                    subs_lang[track["srclang"]]=track["src"]
                else:
                    subs_lang[track["srclang"]]=self.mooc.instance_url + track["src"]
            download_and_convert_subtitles(self.output_path, subs_lang,c)
            self.subs=[ {"file": os.path.join(self.folder_name, lang + ".vtt"), "code": lang } for lang in subs_lang]

        if self.mooc.convert_in_webm:
            video_path=os.path.join(self.output_path,"video.webm")
        else:
            video_path=os.path.join(self.output_path,"video.mp4")
        if not os.path.exists(video_path):
                download(url, video_path,c)
                if self.mooc.convert_in_webm:
                    convert_video_to_webm(video_path, video_path)

    def render(self):
            return jinja(
                None,
                "video.html",
                False,
                format="webm" if self.mooc.convert_in_webm else "mp4",
                folder_name=self.folder_name,
                title=self.json["display_name"],
                subs=self.subs
            )
