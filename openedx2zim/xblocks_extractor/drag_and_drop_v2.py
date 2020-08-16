import pathlib
import json

from bs4 import BeautifulSoup

from .base_xblock import BaseXblock
from ..utils import jinja, prepare_url, get_back_jumps


class DragAndDropV2(
    BaseXblock
):  # IMPROVEMENT We can only see it, not interracting with it
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

        # extra vars
        self.content = None

    def download(self, instance_connection):
        content = instance_connection.get_page(self.xblock_json["student_view_url"])
        if not content:
            return
        soup = BeautifulSoup(content, "lxml")
        self.content = json.loads(
            soup.find("script", attrs={"class": "xblock-json-init-args"}).string.strip()
        )
        # item
        for item in self.content["items"]:
            name = pathlib.Path(item["expandedImageURL"]).name
            if self.scraper.download_file(
                prepare_url(item["expandedImageURL"], self.scraper.instance_url),
                self.scraper.instance_assets_dir.joinpath(name),
            ):
                item["expandedImageURL"] = get_back_jumps(5) + f"instance_assets/{name}"
            else:
                item["expandedImageURL"] = ""
        # Grid
        name = pathlib.Path(self.content["target_img_expanded_url"]).name
        if self.scraper.download_file(
            prepare_url(
                self.content["target_img_expanded_url"], self.scraper.instance_url
            ),
            self.scraper.instance_assets_dir.joinpath(name),
        ):
            self.content["target_img_expanded_url"] = (
                get_back_jumps(5) + f"instance_assets/{name}"
            )
        else:
            self.content["target_img_expanded_url"] = ""

    def render(self):
        return jinja(None, "DragAndDropV2.html", False, dragdrop_content=self.content)
