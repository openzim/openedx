from .base_xblock import BaseXblock


class Sequential(BaseXblock):
    def __init__(
        self, xblock_json, relative_path, root_url, xblock_id, descendants, scraper
    ):
        super().__init__(
            xblock_json, relative_path, root_url, xblock_id, descendants, scraper
        )

    def render(self, prev_info, next_info, chapter):
        for x in range(0, len(self.descendants)):
            if x == 0:  # We search for previous vertical
                prev = prev_info
            else:
                prev = self.descendants[x - 1]

            if x + 1 == len(self.descendants):  # We search for next vertical
                next = next_info
            else:
                next = self.descendants[x + 1]
            self.descendants[x].render(prev, next, chapter, self)

    def get_first(self):
        if len(self.descendants) != 0:
            return self.descendants[0]
        else:
            return None

    def get_last(self):
        if len(self.descendants) != 0:
            return self.descendants[-1]
        else:
            return None
