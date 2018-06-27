from openedxtozim.utils import create_zims, make_dir
#from openedxtozim.utils import exec_cmd #TODO temporaire
import re
from urllib.parse import (
    urlencode,
    quote_plus,
    unquote,
)
import json
import logging
import os
from slugify import slugify
from uuid import uuid4
from distutils.dir_util import copy_tree

from openedxtozim.xblocks_extractor.course import Course
from openedxtozim.xblocks_extractor.chapter import Chapter
from openedxtozim.xblocks_extractor.sequential import Sequential
from openedxtozim.xblocks_extractor.vertical import Vertical
from openedxtozim.xblocks_extractor.video import Video
from openedxtozim.xblocks_extractor.libcast_xblock import Libcast_xblock
from openedxtozim.xblocks_extractor.html import Html
from openedxtozim.xblocks_extractor.problem import Problem
from openedxtozim.xblocks_extractor.discussion import Discussion

BLOCKS_TYPE = { "course": Course, "chapter": Chapter, "sequential": Sequential, "vertical" : Vertical, "video": Video, "libcast_xblock": Libcast_xblock, "html": Html,"problem": Problem, "discussion": Discussion }

def get_course_id(url, course_page_name, course_prefix, instance_url):
    clean_url=re.match(instance_url+course_prefix+".*"+course_page_name,url)
    return quote_plus(clean_url.group(0)[len(instance_url+course_prefix):-len(course_page_name)])

class Mooc:
    json=None
    course_url=None
    course_id=None
    block_id_id=None
    json_tree=None

    def __init__(self,c,course_url):
        self.course_url=course_url
        self.course_id=get_course_id(self.course_url, c.conf["course_page_name"], c.conf["course_prefix"], c.conf["instance_url"])
        logging.info("Get info about course")
        self.info=c.get_api_json("/api/courses/v1/courses/" + self.course_id + "?username="+ c.user)
        self.output_path=os.path.join("output",slugify(self.info["name"]))
        make_dir(self.output_path)
        logging.info("Get course blocks")
        self.json=c.get_api_json("/api/courses/v1/blocks/?course_id=" + self.course_id + "&username="+c.user +"&depth=all&requested_fields=graded,format,student_view_multi_device&student_view_data=video,discussion&block_counts=video,discussion,problem&nav_depth=3")["blocks"]

        with open("json_to_see","w") as f:
            json.dump(self.json,f)
        self.course_root=None
        self.path="course/" # TODO Non ?
        self.rooturl="../"
        self.top={}
        self.object=[]

    def parser_json(self):
        def make_objects(current_path,current_id, rooturl):
            current_json=self.json[current_id]
            path=os.path.join(current_path,slugify(current_json["display_name"]))
            rooturl= rooturl + "../"
            random_id=current_json["localid"]
            descendants = None
            if "descendants" in current_json:
                descendants = []
                for next_id in current_json["descendants"]:
                    descendants.append(make_objects(path,next_id,rooturl))
            obj = BLOCKS_TYPE[current_json["type"]](current_json,path,rooturl,random_id,descendants,self)
            if current_json["type"] == "course":
                self.head=obj
            self.object.append(obj)
            return obj

        logging.info("Parse json and make folder tree")
        for x in self.json:
            self.json[x]["localid"]=str(uuid4())

        root_id=[i for i in self.json if self.json[i]["type"] == "course"]
        if len(root_id) != 0:
            make_objects(self.path,root_id[0],self.rooturl)
        self.top["course"] = "course/" + self.head.folder_name + "/index.html"

    def download(self,c):
        logging.info("Get content")
        for x in self.object:
            x.download(c)

    def annexe(self,c):
        """
        logging.info("Try to get specific page of mooc")
        if len(vertical_path_list) != 0:
            self.link_on_top=get_and_save_specific_pages(c,self.course_id,output,vertical_path_list[0]["url"])
        else:
            self.link_on_top=get_and_save_specific_pages(c,self.course_id,output,False)

        if "forum" in link_on_top:
            logging.info("Get discussion")
            threads, threads_category =get_forum(c,self.course_id,output)
            render_forum(threads,threads_category,output,link_on_top)

        if "wiki" in link_on_top:
            logging.info("Get wiki")
            wiki_page=get_wiki(c,self.course_id,output)
            render_wiki(wiki_page,c,self.course_id,output,link_on_top)
        """

    def render(self):
        self.head.render()
        #TODO
        #exec_cmd("touch {}".format(os.path.join(self.output_path,"index.html")))
        #        exec_cmd("touch {}".format(os.path.join(self.output_path,"favicon.png")))
        #make_welcome_page(output,arguments["<course_url>"],headers,info["name"],instance,conf["instance_url"],link_on_top)
        copy_tree(os.path.join(os.path.abspath(os.path.dirname(__file__)) ,'static'), os.path.join(self.output_path, 'static'))

    def zim(self,lang,publisher,zimpath,nofulltextindex):
        logging.info("Create zim")
        done=create_zims(self.info["name"],lang,publisher,self.info["short_description"], self.info["org"],self.output_path,zimpath,nofulltextindex)


"""
def make_welcome_page(output,course_url,headers,mooc_name,instance,instance_url,link_on_top):
    content=get_page(course_url,headers).decode('utf-8')
    if not os.path.exists(os.path.join(output,"home")):
        os.makedirs(os.path.join(output,"home"))
    html_content_offline=[]
    soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
    #html_content=soup.find_all('div', attrs={"id": re.compile("msg-content-[0-9]*")})
    html_content=soup.find('div', attrs={"class": "welcome-message" })
    if html_content is None:
        html_content=soup.find_all('div', attrs={"class": re.compile("info-wrapper")})
        for x in range(0,len(html_content)):
            article=html_content[x]
            article['class']="toggle-visibility-element article-content"
            html_content_offline.append(dl_dependencies(article.prettify(),os.path.join(output, "home"),"home",instance_url))
    else:
            html_content_offline.append(dl_dependencies(html_content.prettify(),os.path.join(output, "home"),"home",instance_url))
    jinja(
        os.path.join(output,"index.html"),
        "home.html",
        False,
        messages=html_content_offline,
        top=link_on_top,
        mooc_name=mooc_name
    )
    download("https://www.google.com/s2/favicons?domain=" + instance,os.path.join(output,"favicon.png"),instance_url)
"""
