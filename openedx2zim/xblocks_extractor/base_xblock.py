from slugify import slugify

from ..constants import getLogger


class ExtractionWatcher:
    total_count = 0
    dl_count = 0
    success_count = 0
    failed_xblocks = []


logger = getLogger()


class BaseXblock:

    watcher = ExtractionWatcher()
    watcher_min_dl_count = 0
    watcher_min_ratio = 0

    def __init__(
        self, xblock_json, output_path, root_url, xblock_id, descendants, scraper
    ):
        self.scraper = scraper
        self.xblock_json = xblock_json
        self.relative_path = str(output_path)
        self.root_url = root_url
        self.xblock_id = xblock_id
        self.descendants = descendants
        self.display_name = xblock_json["display_name"]
        self.folder_name = slugify(self.display_name)
        self.output_path = self.scraper.build_dir.joinpath(output_path)

        # make xblock output directory
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.watcher.total_count += 1

    @classmethod
    def too_many_failures(cls):
        return cls.watcher.dl_count > cls.watcher_min_dl_count and (cls.watcher.success_count / cls.watcher.dl_count) < cls.watcher_min_ratio
    
    def download(self, instance_connection, lock):
        if BaseXblock.too_many_failures():
            return
        self.lock = lock
        with self.lock:
            self.watcher.dl_count += 1
        logger.debug(f"Downloading resource {self.watcher.dl_count} of {self.watcher.total_count} ({self.watcher.success_count} success so far)")
        try:
            self.download_inner(instance_connection=instance_connection)
        except Exception:
            self.add_failed({})
            return
        with self.lock:
            self.watcher.success_count += 1

    def add_failed(self, description):
        with self.lock:
            description["xblock_id"] = self.xblock_id
            description["class"] = type(self).__name__
            self.watcher.failed_xblocks.append(description)

    def download_inner(self, instance_connection):
        return

    def render(self):
        return
