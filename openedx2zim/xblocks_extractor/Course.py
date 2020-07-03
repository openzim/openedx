from .base_xblock import BaseXblock
from ..utils import jinja
from ..constants import getLogger

logger = getLogger()


class Course(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

    def download(self, c):
        for x in self.descendants:
            x.download(c)

    def render(self):
        for x in range(0, len(self.descendants)):
            if x == 0:
                pred_info = None
            else:
                pred_info = self.descendants[x - 1].get_last()
            if x + 1 == len(self.descendants):
                next_info = None
            else:
                next_info = self.descendants[x + 1].get_first()
            self.descendants[x].render(pred_info, next_info)
        if len(self.descendants) == 0:
            logger.warning("This course has no content")
        else:
            jinja(
                self.output_path.joinpath(self.relative_path).joinpath("index.html"),
                "course_menu.html",
                False,
                course=self,
                rooturl=self.root_url,
                mooc=self.scraper,
                all_side_menu_open=True,
                display_on_mobile=True,
            )
