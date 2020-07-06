from slugify import slugify


class BaseXblock:
    def __init__(self, xblock_json, output_path, root_url, id, descendants, scraper):
        self.scraper = scraper
        self.xblock_json = xblock_json
        self.relative_path = str(output_path)
        self.root_url = root_url
        self.id = id
        self.descendants = descendants
        self.display_name = xblock_json["display_name"]
        self.folder_name = slugify(self.display_name)
        self.output_path = self.scraper.build_dir.joinpath(output_path)

        # make xblock output directory
        self.output_path.mkdir(parents=True, exist_ok=True)

    def download(self, c):
        return

    def render(self):
        return '<div class="not_available">  <p data-l10n-id="not_available" >  <b> Info : </b> Not available offline. </p></div>'
