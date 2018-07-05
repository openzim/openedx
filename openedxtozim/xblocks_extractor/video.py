import bs4 as BeautifulSoup
from openedxtozim.utils import make_dir, jinja,download_and_convert_subtitles, download, download_youtube, convert_video_to_webm
import os
from slugify import slugify
class Video:
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
        self.subs=[]
        youtube=False
        if "student_view_data" not in self.json:
            content=c.get_page(self.json["student_view_url"]).decode('utf-8')
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            url=str(soup.find('video').find('source')["src"])
            subs=soup.find('video').find_all('track')
            subs_lang = {}
            if len(subs) != 0:
                for track in subs:
                    if track["src"][0:4] == "http":
                        subs_lang[track["srclang"]]=track["src"]
                    else:
                        subs_lang[track["srclang"]]=c.conf["instance_url"] + track["src"]
        else:
            if "fallback" in self.json["student_view_data"]["encoded_videos"] and "url" in self.json["student_view_data"]["encoded_videos"]["fallback"]:
                url = self.json["student_view_data"]["encoded_videos"]["fallback"]["url"]
            elif "mobile_low" in self.json["student_view_data"]["encoded_videos"] and "url" in self.json["student_view_data"]["encoded_videos"]["mobile_low"]:
                url = self.json["student_view_data"]["encoded_videos"]["mobile_low"]["url"]
            elif "youtube" in self.json["student_view_data"]["encoded_videos"] and "url" in self.json["student_view_data"]["encoded_videos"]["youtube"]:
                url = self.json["student_view_data"]["encoded_videos"]["youtube"]["url"]
                youtube=True
            else:
                logging.error("Cannot get video for {}".format(self.json["lms_web_url"]))
            subs_lang = self.json["student_view_data"]["transcripts"]

        if self.mooc.convert_in_webm:
            video_path=os.path.join(self.output_path,"video.webm")
        else:
            video_path=os.path.join(self.output_path,"video.mp4")
        if not os.path.exists(video_path):
                if youtube:
                    download_youtube(url,video_path)
                else:
                    download(url, video_path,c)
                if self.mooc.convert_in_webm:
                    convert_video_to_webm(video_path, video_path)
        download_and_convert_subtitles(self.output_path,self.json["student_view_data"]["transcripts"],c)
        self.subs=[ {"file": os.path.join(self.folder_name, lang + ".vtt"), "code": lang } for lang in subs_lang ]

    def render(self):
            return jinja(
                None,
                "video.html",
                False,
                format="webm" if self.mooc.convert_in_webm else "mp4",
                folder_name=self.folder_name,
                subs=self.subs
            )
