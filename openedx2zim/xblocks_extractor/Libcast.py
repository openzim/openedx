from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import (
    jinja,
    download_and_convert_subtitles,
    download,
    convert_video_to_webm,
)


class Libcast(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

        # extra vars
        self.subs = []

    def download(self, c):
        content = c.get_page(self.xblock_json["student_view_url"])
        soup = BeautifulSoup(content, "lxml")
        url = str(soup.find("video").find("source")["src"])
        subs = soup.find("video").find_all("track")
        if len(subs) != 0:
            subs_lang = {}
            for track in subs:
                if track["src"][0:4] == "http":
                    subs_lang[track["srclang"]] = track["src"]
                else:
                    subs_lang[track["srclang"]] = (
                        self.scraper.instance_url + track["src"]
                    )
            download_and_convert_subtitles(self.output_path, subs_lang, c)
            self.subs = [
                {"file": f"{self.folder_name}/{lang}.vtt", "code": lang}
                for lang in subs_lang
            ]

        if self.scraper.convert_in_webm:
            video_path = self.output_path.joinpath("video.webm")
        else:
            video_path = self.output_path.joinpath("video.mp4")
        if not video_path.exists():
            download(url, video_path, c)
            if self.scraper.convert_in_webm:
                convert_video_to_webm(video_path, video_path)

    def render(self):
        return jinja(
            None,
            "video.html",
            False,
            format="webm" if self.scraper.convert_in_webm else "mp4",
            folder_name=self.folder_name,
            title=self.xblock_json["display_name"],
            subs=self.subs,
        )
