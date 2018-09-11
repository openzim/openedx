import bs4 as BeautifulSoup
import os
from slugify import slugify
import logging
import json
import re
from openedxtozim.utils import make_dir, jinja,download_and_convert_subtitles, download, download_youtube, convert_video_to_webm
from urllib.parse import unquote

class Video:
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.no_video=False
        self.folder_name = slugify(json["display_name"])
        self.output_path = os.path.join(self.mooc.output_path,self.path)
        make_dir(self.output_path)
        self.subs=[]

    def download(self, c):
        subs_lang={}
        youtube=False
        if "student_view_data" not in self.json:
            content=c.get_page(self.json["student_view_url"])
            soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
            url=str(soup.find('video').find('source')["src"])
            subs=soup.find('video').find_all('track')
            subs_lang = {}
            if len(subs) != 0:
                for track in subs:
                    if track["src"][0:4] == "http":
                        subs_lang[track["srclang"]]=track["src"]
                    else:
                        subs_lang[track["srclang"]]=self.mooc.instance_url + track["src"]
        else:
            if "fallback" in self.json["student_view_data"]["encoded_videos"] and "url" in self.json["student_view_data"]["encoded_videos"]["fallback"]:
                url = unquote(self.json["student_view_data"]["encoded_videos"]["fallback"]["url"])
            elif "mobile_low" in self.json["student_view_data"]["encoded_videos"] and "url" in self.json["student_view_data"]["encoded_videos"]["mobile_low"]:
                url = unquote(self.json["student_view_data"]["encoded_videos"]["mobile_low"]["url"])
            elif "youtube" in self.json["student_view_data"]["encoded_videos"] and "url" in self.json["student_view_data"]["encoded_videos"]["youtube"]:
                url = self.json["student_view_data"]["encoded_videos"]["youtube"]["url"]
                youtube=True
            else:
                content=c.get_page(self.json["student_view_url"])
                soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
                youtube_json=soup.find('div', attrs={ "id" : re.compile("^video_") })
                if youtube_json and youtube_json.has_attr("data-metadata"):
                    youtube_json=json.loads(youtube_json["data-metadata"])
                    url="https://www.youtube.com/watch?v=" + youtube_json["streams"].split(":")[-1]
                    youtube=True
                    if "transcriptTranslationUrl" in youtube_json and "transcriptLanguages" in youtube_json:
                            for lang in youtube_json["transcriptLanguages"]:
                                subs_lang[lang] = c.conf["instance_url"] + youtube_json["transcriptTranslationUrl"].replace("__lang__", lang) 
                else:
                    self.no_video=True
                    logging.error("Cannot get video for {}".format(self.json["lms_web_url"]))
                    logging.error(self.json)
                    return
            if subs_lang=={}:
                subs_lang = self.json["student_view_data"]["transcripts"]

        if self.mooc.convert_in_webm:
            video_path=os.path.join(self.output_path,"video.webm")
        else:
            video_path=os.path.join(self.output_path,"video.mp4")
        if not os.path.exists(video_path):
                if youtube:
                    download_youtube(url,video_path)
                else:
                    download(unquote(url), video_path,c)
                if self.mooc.convert_in_webm:
                    convert_video_to_webm(video_path, video_path)
        real_subtitle=download_and_convert_subtitles(self.output_path,subs_lang,c)
        self.subs=[ {"file": os.path.join(self.folder_name, lang + ".vtt"), "code": lang } for lang in real_subtitle ]

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
