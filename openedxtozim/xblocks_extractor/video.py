from openedxtozim.utils import make_dir
import os
from slugify import slugify
class Video:
    def __init__(self,json,path,rooturl,id,descendants,mooc):
        self.mooc=mooc
        self.json=json
        self.path=path
        self.rooturl=rooturl
        self.id=id
        self.descendants=descendants
        self.is_video=True
        self.top=self.mooc.top
        self.output_path=self.mooc.output_path
        path = os.path.join(self.output_path,self.path,slugify(json["display_name"]))
        make_dir(path)

    def download(self, c):
        return
        """
        else:
            if data["type"] == "libcast_xblock" or ( data["type"] == "video" and "student_view_data" not in data):
                data["type"] = "video"
                data["student_view_data"]={}
                data["student_view_data"]["encoded_videos"]={}
                try:
                    content=c.get_page(data["student_view_url"]).decode('utf-8')
                    soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
                    url=str(soup.find('video').find('source')["src"])
                    data["student_view_data"]["encoded_videos"]["fallback"]={}
                    data["student_view_data"]["encoded_videos"]["fallback"]["url"]=url
                    data["student_view_data"]["transcripts"]={}
                    data["student_view_data"]["transcripts_vtt"]=True
                    subs=soup.find('video').find_all('track')
                    for track in subs:
                        if track["src"][0:4] == "http":
                            data["student_view_data"]["transcripts"][track["srclang"]]=track["src"]
                        else:
                            data["student_view_data"]["transcripts"][track["srclang"]]=instance_url + track["src"]
                except:
                    try:
                        print("TODO youtube")
                    except:
                        logging.warning("Sorry we can't get video from" +data["student_view_url"])
            elif data["type"] == "video":
                data["student_view_data"]["transcripts_vtt"]=False
        return data
        video_path=os.path.join(path,"video.mp4")
        video_final_path=os.path.join(path,"video.webm")
        if not os.path.exists(video_final_path):
            try:
                download(data["student_view_data"]["encoded_videos"]["fallback"]["url"], video_path,instance_url)
                convert_video_to_webm(video_path, video_final_path)
            except Exception as e:
                try:
                    download(data["student_view_data"]["encoded_videos"]["mobile_low"]["url"], video_path,instance_url)
                    convert_video_to_webm(video_path, video_final_path)
                except Exception as e:
                    try:
                        download_youtube(data["student_view_data"]["encoded_videos"]["youtube"]["url"], video_path)
                    except Exception as e:
                        data["html_content"]="<h3> Sorry, this video is not available </h3>"
                        return data
        download_and_convert_subtitles(path,data["student_view_data"]["transcripts"],data["student_view_data"]["transcripts_vtt"],headers)
        data["video_path"]=os.path.join(data[block_id_id], "video.webm")
        data["transcripts_file"]=[ {"file": os.path.join(data[block_id_id], lang + ".vtt"), "code": lang } for lang in data["student_view_data"]["transcripts"] ]
        """

    def render(self):
            return "TODO"

