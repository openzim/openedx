import re
import html
import uuid
import json
import pathlib
import collections

from bs4 import BeautifulSoup

from .constants import getLogger
from .utils import jinja, markdown, get_back_jumps

logger = getLogger()


class MoocForum:
    def __init__(self, scraper):
        self.scraper = scraper
        self.threads = []
        self.categories = collections.OrderedDict()
        self.staff_user = []
        self.output_path = self.scraper.build_dir.joinpath("forum")
        self.output_path.mkdir(parents=True, exist_ok=True)

    def add_categories(self, categories):
        for category in categories:
            if (category.get("id") in ["all_discussions", "posts_following"]) or (
                category.has_attr("class")
                and (
                    "forum-nav-browse-menu-all" in category["class"]
                    or "forum-nav-browse-menu-following" in category["class"]
                )
            ):
                continue
            if not category.has_attr(
                "data-discussion-id"
            ):  # and cat.find("a") != None:
                self.categories[str(uuid.uuid4())] = {
                    "title": category.find(
                        ["a", "span"], attrs={"class": "forum-nav-browse-title"}
                    ).text,
                    "catego_with_sub_catego": True,
                }
            elif category.has_attr("data-discussion-id"):
                self.categories[category["data-discussion-id"]] = {
                    "title": str(category.text).replace("\n", "")
                }

    def prepare_forum_categories(self, forum_content):
        soup = BeautifulSoup(forum_content, "lxml")
        good_content = soup.find("script", attrs={"id": "thread-list-template"})
        if good_content:
            categories = soup.find_all(
                "li", attrs={"class": "forum-nav-browse-menu-item"}
            )
            if len(categories) == 0:
                soup = BeautifulSoup(
                    good_content.text, "lxml"
                )  # On Fun plateform, categorie list is in script with id thread-list-template
                categories = soup.find_all(
                    "li", attrs={"class": "forum-nav-browse-menu-item"}
                )
            self.add_categories(categories)
        else:
            logger.error("No forum category found")

    def populate_staff_users(self, forum_content):
        user_json = {}
        user_section = BeautifulSoup(forum_content, "lxml").find(
            "section", attrs={"id": "discussion-container"}
        )
        if user_section and user_section.has_attr("data-roles"):
            if "&#34;" in user_section["data-roles"]:
                user_json = json.loads(html.unescape(user_section["data-roles"]))
            else:
                user_json = json.loads(user_section["data-roles"])
        else:
            user_section = re.search("roles: [^\n]*", forum_content)
            if user_section:  # TODO check ok in this case
                user_json = json.loads(
                    re.sub(r"roles: (.*),", r"\1", user_section.group())
                )
        for user in user_json:
            self.staff_user += [str(y) for y in user_json[user]]

    def prepare_thread_list(self):
        for category in self.categories:
            self.output_path.joinpath(category).mkdir(parents=True, exist_ok=True)
            data = self.scraper.instance_connection.get_api_json(
                "/courses/"
                + self.scraper.course_id
                + "/discussion/forum/"
                + category
                + "/inline?ajax=1&page=1&sort_key=activity&sort_order=desc"
            )
            self.threads += data["discussion_data"]
            for i in range(1, data["num_pages"]):
                data = self.scraper.instance_connection.get_api_json(
                    "/courses/"
                    + self.scraper.course_id
                    + "/discussion/forum/"
                    + category
                    + "/inline?ajax=1&page="
                    + str(i + 1)
                    + "&sort_key=activity&sort_order=desc"
                )
                self.threads += data["discussion_data"]

    def fetch_thread_data(self, thread):
        url = (
            "/courses/"
            + self.scraper.course_id
            + "/discussion/forum/"
            + thread["commentable_id"]
            + "/threads/"
            + thread["id"]
            + "?ajax=1&resp_skip=0&resp_limit=100"
        )
        self.output_path.joinpath(thread["id"]).mkdir(parents=True, exist_ok=True)
        try:
            thread["data_thread"] = self.scraper.instance_connection.get_api_json(
                url, referer=self.scraper.instance_url + url.split("?")[0]
            )
            total_answers = 100
            while total_answers < thread["data_thread"]["content"]["resp_total"]:
                url = (
                    "/courses/"
                    + self.scraper.course_id
                    + "/discussion/forum/"
                    + thread["commentable_id"]
                    + "/threads/"
                    + thread["id"]
                    + "?ajax=1&resp_skip="
                    + str(total_answers)
                    + "&resp_limit=100"
                )
                new_answers = self.scraper.instance_connection.get_api_json(
                    url, referer=self.scraper.instance_url + url.split("?")[0]
                )["content"]["children"]
                thread["data_thread"]["content"]["children"] += new_answers
                total_answers += 100
        except Exception:
            try:
                thread["data_thread"] = self.scraper.instance_connection.get_api_json(
                    url
                )
            except Exception:
                logger.debug(
                    "Can not get " + self.scraper.instance_url + url + "discussion"
                )

    def update_thread_children(self, thread):
        for children in thread["data_thread"]["content"]["children"]:
            children[
                "body"
            ] = self.scraper.html_processor.dl_dependencies_and_fix_links(
                content=markdown(children["body"]),
                output_path=self.output_path.joinpath(thread["id"]),
                path_from_html="",
                root_from_html=get_back_jumps(
                    len(self.output_path.relative_to(self.scraper.build_dir).parts)
                ),
            )
            if "children" in children:
                for children_children in children["children"]:
                    children_children[
                        "body"
                    ] = self.scraper.html_processor.dl_dependencies_and_fix_links(
                        content=markdown(children_children["body"]),
                        output_path=self.output_path.joinpath(thread["id"]),
                        path_from_html="",
                        root_from_html=get_back_jumps(
                            len(
                                self.output_path.relative_to(
                                    self.scraper.build_dir
                                ).parts
                            )
                        ),
                    )

    def annex_forum(self):
        forum_content = self.scraper.instance_connection.get_page(
            self.scraper.instance_url
            + "/courses/"
            + self.scraper.course_id
            + "/discussion/forum"
        )
        self.prepare_forum_categories(forum_content)
        self.populate_staff_users(forum_content)
        self.prepare_thread_list()

        for thread in self.threads:
            self.fetch_thread_data(thread)
            if (
                "endorsed_responses" in thread["data_thread"]["content"]
                or "non_endorsed_responses" in thread["data_thread"]["content"]
            ) and "children" in thread["data_thread"]["content"]:
                logger.warning("pb endorsed VS children" + thread["id"])
            if "children" not in thread["data_thread"]["content"]:
                thread["data_thread"]["content"]["children"] = []
            if "endorsed_responses" in thread["data_thread"]["content"]:
                thread["data_thread"]["content"]["children"] += thread["data_thread"][
                    "content"
                ]["endorsed_responses"]
            if "non_endorsed_responses" in thread["data_thread"]["content"]:
                thread["data_thread"]["content"]["children"] += thread["data_thread"][
                    "content"
                ]["non_endorsed_responses"]
            thread["data_thread"]["content"][
                "body"
            ] = self.scraper.html_processor.dl_dependencies_and_fix_links(
                content=markdown(thread["data_thread"]["content"]["body"]),
                output_path=self.output_path.joinpath(thread["id"]),
                path_from_html="",
                root_from_html=get_back_jumps(
                    len(self.output_path.relative_to(self.scraper.build_dir).parts)
                ),
            )
            self.update_thread_children(thread)

    def render_forum(self):
        thread_by_category = collections.defaultdict(list)
        for thread in self.threads:
            thread_by_category[thread["commentable_id"]].append(thread)
        jinja(
            self.output_path.joinpath("index.html"),
            "forum.html",
            False,
            category=self.categories,
            thread_by_category=thread_by_category,
            staff_user=self.staff_user,
            mooc=self.scraper,
            rooturl="../",
            display_on_mobile=True,
        )
        for thread in self.threads:
            jinja(
                self.output_path.joinpath(thread["id"]).joinpath("index.html"),
                "forum.html",
                False,
                thread=thread["data_thread"]["content"],
                category=self.categories,
                thread_by_category=thread_by_category,
                staff_user=self.staff_user,
                mooc=self.scraper,
                rooturl="../../",
                forum_menu=True,
            )


class MoocWiki:
    def __init__(self, scraper):
        self.scraper = scraper
        self.wiki_data = {}
        self.wiki_name = ""
        self.wiki_path = None
        self.first_page = None

    def get_first_page(self):
        # get redirection to first wiki page
        first_page = self.scraper.instance_connection.get_redirection(
            self.scraper.instance_url
            + "/courses/"
            + self.scraper.course_id
            + "/course_wiki"
        )
        # Data from page already visit
        # "[url]" : { "rooturl": , "path": , "text": , "title": , "dir" : , "children": [] }

        # Extract wiki name
        self.wiki_name = first_page.replace(self.scraper.instance_url + "/wiki/", "")[
            :-1
        ]
        self.wiki_path = pathlib.Path("wiki", self.wiki_name)

    def add_to_wiki_data(self, url):
        self.wiki_data[url] = {}
        web_path = pathlib.Path("wiki").joinpath(
            url.replace(self.scraper.instance_url + "/wiki/", "")
        )
        output_path = self.scraper.build_dir.joinpath(web_path)
        output_path.mkdir(parents=True, exist_ok=True)
        self.wiki_data[url]["path"] = output_path
        rooturl = "../"
        for x in range(0, len(web_path.parts)):
            rooturl += "../"
        self.wiki_data[url]["rooturl"] = rooturl
        self.wiki_data[url]["children"] = []

    def update_wiki_page(self, soup, text, url, page_to_visit):
        for link in text.find_all("a"):
            if link.has_attr("href") and "/wiki/" in link["href"]:
                if link not in self.wiki_data and link not in page_to_visit:
                    if not link["href"][0:4] == "http":
                        page_to_visit.append(self.scraper.instance_url + link["href"])
                    else:
                        page_to_visit.append(link["href"])

                if not link["href"][0:4] == "http":  # Update path in wiki page
                    link["href"] = (
                        self.wiki_data[url]["rooturl"][:-1]
                        + link["href"].replace(self.scraper.instance_url, "")
                        + "/index.html"
                    )

        self.wiki_data[url][
            "text"
        ] = self.scraper.html_processor.dl_dependencies_and_fix_links(
            content=str(text),
            output_path=self.wiki_data[url]["path"],
            path_from_html="",
            root_from_html=get_back_jumps(
                len(
                    self.wiki_data[url]["path"]
                    .relative_to(self.scraper.build_dir)
                    .parts
                )
            ),
        )
        self.wiki_data[url]["title"] = soup.find("title").text
        self.wiki_data[url]["last-modif"] = soup.find(
            "span", attrs={"class": "date"}
        ).text
        self.wiki_data[url]["children"] = []

    def get_wiki_children(self, soup, url, page_to_visit):
        see_children = soup.find("div", attrs={"class": "see-children"})
        if see_children:
            allpage_url = str(see_children.find("a")["href"])
            self.wiki_data[url]["dir"] = allpage_url
            content = self.scraper.instance_connection.get_page(
                self.scraper.instance_url + allpage_url
            )
            soup = BeautifulSoup(content, "lxml")
            table = soup.find("table")
            if table:
                for link in table.find_all("a"):
                    if not (
                        link.has_attr("class") and "list-children" in link["class"]
                    ):
                        if (
                            link["href"] not in self.wiki_data
                            and link["href"] not in page_to_visit
                        ):
                            page_to_visit.append(
                                self.scraper.instance_url + link["href"]
                            )
                        self.wiki_data[url]["children"].append(
                            self.scraper.instance_url + link["href"]
                        )

    def annex_wiki(self):
        self.get_first_page()
        page_to_visit = [self.first_page]
        while page_to_visit:
            url = page_to_visit.pop()
            self.add_to_wiki_data(url)
            content = self.scraper.instance_connection.get_page(url)
            # Parse content page
            if content:
                soup = BeautifulSoup(content, "lxml")
                text = soup.find("div", attrs={"class": "wiki-article"})
                if text:  # If it's a page (and not a list of page)
                    self.update_wiki_page(soup, text, url, page_to_visit)
            else:
                self.wiki_data[url][
                    "text"
                ] = """<div><h1 class="page-header">Permission Denied</h1><p class="alert denied">Sorry, you don't have permission to view this page.</p></div>"""
                self.wiki_data[url]["title"] = "Permission Denied | Wiki"
                self.wiki_data[url]["last-modif"] = "Unknow"
                self.wiki_data[url]["children"] = []

            # find new url of wiki in the list children page
            self.get_wiki_children(soup, url, page_to_visit)

    def render_wiki(self):
        for page in self.wiki_data:
            if "text" in self.wiki_data[page]:  # this is a page
                jinja(
                    self.wiki_data[page]["path"].joinpath("index.html"),
                    "wiki_page.html",
                    False,
                    content=self.wiki_data[page],
                    dir=self.wiki_data[page]["dir"].replace(
                        self.scraper.instance_url + "/wiki/", ""
                    )
                    + "index.html",
                    mooc=self.scraper,
                    rooturl=self.wiki_data[page]["rooturl"],
                )

            self.wiki_data[page]["path"].joinpath("_dir").mkdir(
                parents=True, exist_ok=True
            )
            if len(self.wiki_data[page]["children"]) != 0:  # this is a list page
                page_to_list = []
                for child_page in self.wiki_data[page]["children"]:
                    if "title" in self.wiki_data[child_page]:
                        page_to_list.append(
                            {
                                "url": self.wiki_data[page]["rooturl"]
                                + "/.."
                                + child_page.replace(self.scraper.instance_url, ""),
                                "title": self.wiki_data[child_page]["title"],
                                "last-modif": self.wiki_data[child_page]["last-modif"],
                            }
                        )
                jinja(
                    self.wiki_data[page]["path"]
                    .joinpath("_dir")
                    .joinpath("index.html"),
                    "wiki_list.html",
                    False,
                    pages=page_to_list,
                    wiki_name=self.wiki_name,
                    mooc=self.scraper,
                    rooturl=self.wiki_data[page]["rooturl"] + "../",
                )
