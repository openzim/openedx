from .base_xblock import BaseXblock


class Unavailable(BaseXblock):
    def __init__(self, xblock_json, relative_path, root_url, id, descendants, scraper):
        super().__init__(xblock_json, relative_path, root_url, id, descendants, scraper)

    def download(self, c):
        return

    def render(self):
        return '<div class="not_available">  <p data-l10n-id="not_available" >  <b> Info : </b> Not available offline. </p></div>'