from .base_xblock import BaseXblock


class GradeMeButton(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

    def download(self, instance_connection):
        return

    def render(self):
        return "Grade Me ! ; Not available offline"
