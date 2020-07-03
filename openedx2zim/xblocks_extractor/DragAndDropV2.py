import pathlib
import json

from bs4 import BeautifulSoup
from slugify import slugify

from .base_xblock import BaseXblock
from ..utils import jinja, download


class DragAndDropV2(BaseXblock):  # IMPROVEMENT We can only see it, not interracting with it
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

        # extra vars
        self.content = None

    def download(self, c):
        content = c.get_page(self.xblock_json["student_view_url"])
        soup = BeautifulSoup(content, "lxml")
        self.content = json.loads(
            soup.find("script", attrs={"class": "xblock-json-init-args"}).get_text()
        )
        # item
        for item in self.content["items"]:
            name = pathlib.Path(item["expandedImageURL"]).name
            download(
                item["expandedImageURL"],
                self.output_path.joinpath(name),
                self.scraper.instance_url,
            )
            item["expandedImageURL"] = f"{slugify(self.display_name)}/{name}"
        # Grid
        name = pathlib.Path(self.content["target_img_expanded_url"]).name
        download(
            self.content["target_img_expanded_url"],
            self.output_path.joinpath(name),
            self.scraper.instance_url,
        )
        self.content["target_img_expanded_url"] = f"{slugify(self.display_name)}/{name}"

    def render(self):
        return jinja(None, "DragAndDropV2.html", False, dragdrop_content=self.content)
