from .base_xblock import BaseXblock
from ..utils import jinja


class Vertical(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

        # set icon
        if self.xblock_json["block_counts"]["video"] != 0:
            self.icon_type = "fa-video-camera"
        elif self.xblock_json["block_counts"]["problem"] != 0:
            self.icon_type = "fa-question-circle"
        elif self.xblock_json["block_counts"]["discussion"] != 0:
            self.icon_type = "fa-comment"
        else:
            self.icon_type = "fa-book"

    def download(self, instance_connection):
        for x in self.descendants:
            x.download(instance_connection)

    def render(self, prev_vertical, next_vertical, chapter, sequential):
        vertical = []
        for x in self.descendants:
            vertical.append(x.render())
        jinja(
            self.output_path.joinpath("index.html"),
            "vertical.html",
            False,
            rooturl=self.root_url,
            mooc=self.scraper,
            chapter=chapter,
            sequential=sequential,
            vertical=self,
            extracted_id=self.xblock_json["id"].split("@")[-1],
            vertical_content=vertical,
            prev_vertical=prev_vertical,
            next_vertical=next_vertical,
            side_menu=True,
        )
