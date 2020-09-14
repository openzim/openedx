from .base_xblock import BaseXblock
from ..utils import jinja
from ..constants import getLogger

logger = getLogger()


class Course(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

    def render(self):
        for x in range(0, len(self.descendants)):
            if x == 0:
                prev_info = None
            else:
                prev_info = self.descendants[x - 1].get_last()
            if x + 1 == len(self.descendants):
                next_info = None
            else:
                next_info = self.descendants[x + 1].get_first()
            self.descendants[x].render(prev_info, next_info)
        if len(self.descendants) == 0:
            logger.warning("This course has no content")
        else:
            jinja(
                self.output_path.joinpath("index.html"),
                "course_menu.html",
                False,
                course=self,
                rooturl=self.root_url,
                mooc=self.scraper,
                all_side_menu_open=True,
                display_on_mobile=True,
            )
