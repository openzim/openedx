import re

from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import jinja


class Discussion(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

        # extra vars
        self.data = []
        self.category_title = ""
        self.is_video = False

    def download(self, c):
        if self.scraper.forum_thread:
            content = c.get_page(self.xblock_json["student_view_url"])
            soup = BeautifulSoup(content, "lxml")
            discussion_block = soup.find(
                re.compile(r".*"), {"data-discussion-id": re.compile(r".*")}
            )
            if discussion_block:
                discussion_id = discussion_block["data-discussion-id"]
                for thread in self.scraper.forum_thread:
                    if thread["commentable_id"] == discussion_id:
                        self.data.append(thread)
                if len(self.data) != 0:
                    self.category_title = self.scraper.forum_category[discussion_id]

    def render(self):
        if self.category_title != "":
            return jinja(
                None,
                "discussion.html",
                False,
                category_title=self.category_title,
                threads=self.data,
                discussion=self,
                staff_user=self.scraper.staff_user_forum,
                rooturl="/".join(self.root_url.split("/")[:-1]),  # rooturl - 1 folder
            )
        else:
            return "This discussion is not supported, sorry !"