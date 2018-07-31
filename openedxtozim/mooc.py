import re
from urllib.parse import (
    urlencode,
    quote_plus,
    unquote,
    urlparse,
)
import json
import logging
import os
from slugify import slugify
from uuid import uuid4
from distutils.dir_util import copy_tree
import bs4 as BeautifulSoup
from openedxtozim.utils import create_zims, make_dir, download, dl_dependencies, jinja

import openedxtozim.annexe as annexe

from openedxtozim.xblocks_extractor.course import Course
from openedxtozim.xblocks_extractor.chapter import Chapter
from openedxtozim.xblocks_extractor.sequential import Sequential
from openedxtozim.xblocks_extractor.vertical import Vertical
from openedxtozim.xblocks_extractor.video import Video
from openedxtozim.xblocks_extractor.libcast_xblock import Libcast_xblock
from openedxtozim.xblocks_extractor.html import Html
from openedxtozim.xblocks_extractor.problem import Problem
from openedxtozim.xblocks_extractor.discussion import Discussion
from openedxtozim.xblocks_extractor.FreeTextResponse import FreeTextResponse
from openedxtozim.xblocks_extractor.Unavailable import Unavailable
from openedxtozim.xblocks_extractor.Lti import Lti
from openedxtozim.xblocks_extractor.DragAndDropV2 import DragAndDropV2

BLOCKS_TYPE = { "course": Course, "chapter": Chapter, "sequential": Sequential, "vertical" : Vertical, "video": Video, "libcast_xblock": Libcast_xblock, "html": Html,"problem": Problem, "discussion": Discussion, "qualtricssurvey" : Html , "freetextresponse": FreeTextResponse , "grademebutton": Unavailable, "drag-and-drop-v2" : DragAndDropV2, "lti": Lti, "unavailable": Unavailable}

def get_course_id(url, course_page_name, course_prefix, instance_url):
    clean_url=re.match(instance_url+course_prefix+".*"+course_page_name,url)
    clean_id=clean_url.group(0)[len(instance_url+course_prefix):-len(course_page_name)]
    if "%3" in clean_id: #course_id seems already encode
        return clean_id
    else:
        return quote_plus(clean_id)

class Mooc:
    json=None
    course_url=None
    course_id=None
    block_id_id=None
    json_tree=None

    def __init__(self,c,course_url,convert_in_webm,ignore_missing_xblock):
        self.course_url=course_url
        self.convert_in_webm=convert_in_webm
        self.ignore_missing_xblock=ignore_missing_xblock
        self.instance_url=c.conf["instance_url"]
        self.course_id=get_course_id(self.course_url, c.conf["course_page_name"], c.conf["course_prefix"], self.instance_url)
        logging.info("Get info about course")
        self.info=c.get_api_json("/api/courses/v1/courses/" + self.course_id + "?username="+ c.user)

        self.output_path=os.path.join("output",slugify(self.info["name"]))
        self.name = slugify(self.info["name"])
        make_dir(self.output_path)
        logging.info("Get course blocks")
        json_from_api=c.get_api_json("/api/courses/v1/blocks/?course_id=" + self.course_id + "&username="+c.user +"&depth=all&requested_fields=graded,format,student_view_multi_device&student_view_data=video,discussion&block_counts=video,discussion,problem&nav_depth=3")
        self.json=json_from_api["blocks"]
        self.root_id=json_from_api["root"]

        self.course_root=None
        self.path=""
        self.rooturl=""
        self.top={}
        self.object=[]
        self.no_homepage=False
        self.wiki=None
        self.forum_thread=None
        self.page_annexe=[]

    def parser_json(self):
        def make_objects(current_path,current_id, rooturl):
            current_json=self.json[current_id]
            path=os.path.join(current_path,slugify(current_json["display_name"]))
            rooturl= rooturl + "../"
            random_id=str(uuid4())
            descendants = None
            if "descendants" in current_json:
                descendants = []
                for next_id in current_json["descendants"]:
                    descendants.append(make_objects(path,next_id,rooturl))
            if current_json["type"] in BLOCKS_TYPE:
                obj = BLOCKS_TYPE[current_json["type"]](current_json,path,rooturl,random_id,descendants,self)
            else:
                if not self.ignore_missing_xblock:
                    logging.error("Some part of your course are not supported by openedx2zim : {} \n You should open an issue at https://github.com/openzim/openedx/issues (with this message and Mooc URL, you can ignore this with --ignore-unsupported-xblocks".format(current_json["type"]))
                else:
                    obj = BLOCKS_TYPE["unavailable"](current_json,path,rooturl,random_id,descendants,self)

            if current_json["type"] == "course":
                self.head=obj
            self.object.append(obj)
            return obj

        logging.info("Parse json and make folder tree")
        make_objects(self.path+"course/",self.root_id,self.rooturl+"../")
        self.top["course"] = "course/" + self.head.folder_name + "/index.html"

    def annexe(self,c):
        logging.info("Try to get specific page of mooc")
        content=c.get_page(self.course_url).decode('utf-8')
        soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
        top_bs=soup.find('ol', attrs={"class": "course-material" }) or soup.find('ul', attrs={"class": "course-material" }) or soup.find('ul', attrs={"class": "navbar-nav" }) or soup.find('ol', attrs={"class": "course-tabs"})
        if top_bs != None:
            for top_elem in top_bs.find_all("li"):
                top_elem=top_elem.find("a")
                path=re.sub("/courses/[^/]*/","",top_elem["href"])
                if path == "course/" or "edxnotes" in path or "progress" in path or "info" in path or "courseware" in path:
                    continue
                self.top[top_elem.get_text()]= path
                if "wiki" in path:
                    self.wiki, self.wiki_name=annexe.wiki(c,self)
                elif "forum" in path:
                    pass #TODO tmp Not working at this time
                    print(path)
                    self.forum_thread, self.forum_category = annexe.forum(c,self)
                else:
                    output_path = os.path.join(self.output_path,path)
                    make_dir(output_path)
                    page_content=c.get_page(self.instance_url + top_elem["href"]).decode('utf-8')
                    soup_page=BeautifulSoup.BeautifulSoup(page_content, 'html.parser')
                    just_content = soup_page.find('section', attrs={"class": "container"})
                    if just_content != None :
                        html_content=dl_dependencies(str(just_content),output_path,"",c)
                    else:
                        book=soup_page.find('section', attrs={"class": "book-sidebar"})
                        if book != None:
                            html_content=annexe.booknav(self,book,url,output_path)
                        else:
                            logging.warning("Oh it's seems we does not support one type of extra content (in top bar) :" + path)
                            continue
                    self.page_annexe.append({ "output_path": output_path, "content": html_content,"title" : soup_page.find('title').get_text()})

    def download(self,c):
        logging.info("Get content")
        for x in self.object:
            x.download(c)

    def render(self):
        self.head.render()
        for data in self.page_annexe:
            jinja(
                os.path.join(data["output_path"],"index.html"),
                "specific_page.html",
                False,
                title=data["title"],
                mooc=self,
                content=data["content"],
                rooturl="../../"
            )

        if self.wiki:
            annexe.render_wiki(self)
        if self.forum_thread:
            annexe.render_forum(self)
        copy_tree(os.path.join(os.path.abspath(os.path.dirname(__file__)) ,'static'), os.path.join(self.output_path, 'static'))

    def make_welcome_page(self,c):
        print("--IMPORTANT--")
        dl_dependencies("","/tmp","bla",c,True) #TODO tmp debug format fichier
        print("-------------")
        download("https://www.google.com/s2/favicons?domain=" + self.instance_url , os.path.join(self.output_path,"favicon.png"),None)

        #IMPROUVEMENT add message sur first page of course, not "homepage" (no more homepage). If homepage, add in top. (if top has info => then info = index.html for zim, else first page of mooc ?
        content=c.get_page(self.course_url).decode('utf-8')
        if not os.path.exists(os.path.join(self.output_path,"home")):
            os.makedirs(os.path.join(self.output_path,"home"))
        html_content_offline=[]
        soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
        html_content=soup.find('div', attrs={"class": "welcome-message" })
        if html_content is None:
            html_content=soup.find_all('div', attrs={"class": re.compile("info-wrapper")})
            if html_content == [] :
                self.no_homepage=True
                return
            else:
                for x in range(0,len(html_content)):
                    article=html_content[x]
                    article['class']="toggle-visibility-element article-content"
                    html_content_offline.append(dl_dependencies(article.prettify(),os.path.join(self.output_path, "home"),"home",c))
        else:
                html_content_offline.append(dl_dependencies(html_content.prettify(),os.path.join(self.output_path, "home"),"home",c))
        jinja(
            os.path.join(self.output_path,"index.html"),
            "home.html",
            False,
            messages=html_content_offline,
            mooc=self
        )

    def zim(self,lang,publisher,zimpath,nofulltextindex):
        logging.info("Create zim")
        if self.no_homepage:
            homepage=os.path.join(self.head.path,self.head.folder_name)
        else:
            homepage="index.html"
        done=create_zims(self.info["name"],lang,publisher,self.info["short_description"], self.info["org"],self.output_path,zimpath,nofulltextindex,homepage)



