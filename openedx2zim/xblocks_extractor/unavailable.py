from .base_xblock import BaseXblock
from ..constants import UNSUPPORTED_XBLOCKS


class Unavailable(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

    def render(self):
        error_message = UNSUPPORTED_XBLOCKS.get(
            self.xblock_json["type"], "Not available offline"
        )
        return f'<div class="not_available">  <p data-l10n-id="not_available" >  <b> Info : </b> {error_message} </p></div>'
