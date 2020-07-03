import json
import re
import urllib

from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import (
    jinja,
    download_and_convert_subtitles,
    download,
    download_youtube,
    convert_video_to_webm,
)
from ..constants import getLogger


logger = getLogger()


class Video(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

        # extra vars
        self.subs = []

    def download(self, c):
        subs_lang = {}
        youtube = False
        if "student_view_data" not in self.xblock_json:
            content = c.get_page(self.xblock_json["student_view_url"])
            soup = BeautifulSoup.BeautifulSoup(content, "lxml")
            url = str(soup.find("video").find("source")["src"])
            subs = soup.find("video").find_all("track")
            subs_lang = {}
            if len(subs) != 0:
                for track in subs:
                    if track["src"][0:4] == "http":
                        subs_lang[track["srclang"]] = track["src"]
                    else:
                        subs_lang[track["srclang"]] = (
                            self.scraper.instance_url + track["src"]
                        )
        else:
            if (
                "fallback" in self.xblock_json["student_view_data"]["encoded_videos"]
                and "url"
                in self.xblock_json["student_view_data"]["encoded_videos"]["fallback"]
            ):
                url = urllib.parse.unquote(
                    self.xblock_json["student_view_data"]["encoded_videos"]["fallback"][
                        "url"
                    ]
                )
            elif (
                "mobile_low" in self.xblock_json["student_view_data"]["encoded_videos"]
                and "url"
                in self.xblock_json["student_view_data"]["encoded_videos"]["mobile_low"]
            ):
                url = urllib.parse.unquote(
                    self.xblock_json["student_view_data"]["encoded_videos"][
                        "mobile_low"
                    ]["url"]
                )
            elif (
                "youtube" in self.xblock_json["student_view_data"]["encoded_videos"]
                and "url"
                in self.xblock_json["student_view_data"]["encoded_videos"]["youtube"]
            ):
                url = self.xblock_json["student_view_data"]["encoded_videos"][
                    "youtube"
                ]["url"]
                youtube = True
            else:
                content = c.get_page(self.xblock_json["student_view_url"])
                soup = BeautifulSoup.BeautifulSoup(content, "lxml")
                youtube_json = soup.find("div", attrs={"id": re.compile("^video_")})
                if youtube_json and youtube_json.has_attr("data-metadata"):
                    youtube_json = json.loads(youtube_json["data-metadata"])
                    url = (
                        "https://www.youtube.com/watch?v="
                        + youtube_json["streams"].split(":")[-1]
                    )
                    youtube = True
                    if (
                        "transcriptTranslationUrl" in youtube_json
                        and "transcriptLanguages" in youtube_json
                    ):
                        for lang in youtube_json["transcriptLanguages"]:
                            subs_lang[lang] = c.conf["instance_url"] + youtube_json[
                                "transcriptTranslationUrl"
                            ].replace("__lang__", lang)
                else:
                    self.no_video = True
                    logger.error(
                        "Cannot get video for {}".format(
                            self.xblock_json["lms_web_url"]
                        )
                    )
                    logger.error(self.xblock_json)
                    return
            if subs_lang == {}:
                subs_lang = self.xblock_json["student_view_data"]["transcripts"]

        if self.scraper.convert_in_webm:
            video_path = self.output_path.joinpath("video.webm")
        else:
            video_path = self.output_path.joinpath("video.mp4")
        if not video_path.exists():
            if youtube:
                download_youtube(url, video_path)
            else:
                download(urllib.parse.unquote(url), video_path, c)
            if self.scraper.convert_in_webm:
                convert_video_to_webm(video_path, video_path)
        real_subtitle = download_and_convert_subtitles(self.output_path, subs_lang, c)
        self.subs = [
            {"file": f"{self.folder_name}/{lang}.vtt", "code": lang}
            for lang in real_subtitle
        ]

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
