#!/usr/bin/env python3
# -*-coding:utf8 -*
"""openedx2zim.

Usage:
  openedx2zim <course_url> <publisher> <email> [--password=<pass>] [--nozim] [--zimpath=<zimpath>] [--nofulltextindex]
  openedx2zim (-h | --help)
  openedx2zim --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --password=<pass> you can specify password as arguments or you'll be asked for password
  --nozim       doesn't make zim file, output will be in work/ in normal html
  --zimpath=<zimpath>   Final path of the zim file
  --nofulltextindex        Dont index content

"""
import json
import getpass
import re
from docopt import docopt
from http.cookiejar import LWPCookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import (
    urlencode,
    quote_plus,
    unquote,
)
from urllib.request import (
    urlopen,
    build_opener,
    install_opener,
    HTTPCookieProcessor,
    Request,
    urlretrieve,
)
import ssl
import subprocess
import sys
import os
import bs4 as BeautifulSoup

from lxml.etree import parse as string2xml
from lxml.html import fromstring as string2html
from lxml.html import tostring as html2string
from webvtt import WebVTT
import youtube_dl

from hashlib import sha256
from slugify import slugify
from subprocess import call
import shlex
from jinja2 import Environment
from jinja2 import FileSystemLoader
from distutils.dir_util import copy_tree
import datetime
import logging
import random
import mistune #markdown

DEBUG=False
#########################
# Interact with website #
#########################
def make_headers(instance_url, page):
    cookiejar = LWPCookieJar()
    opener = build_opener(HTTPCookieProcessor(cookiejar))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    install_opener(opener)
    opener.open(instance_url)
    for cookie in cookiejar:
        if cookie.name == 'csrftoken':
            break
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': instance_url + page,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': cookie.value,
    }
    return headers

def login(instance_url, page,headers,username,password):
    post_data = urlencode({'email': username,
                           'password': password,
                           'remember': False}).encode('utf-8')

    request = Request(instance_url + page, post_data, headers=headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    return resp

def get_api_json(instance_url,page, headers):
    if DEBUG:
        print(instance_url+page)
    request = Request(instance_url + page, None, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    return resp

def get_page(url,headers):
    if DEBUG:
        print(url)
    request = Request(url, None, headers)
    try:
        response = urlopen(request)
    except:
        response = urlopen(request)
    return response.read()

def get_course_id(url, course_page_name, course_prefix, instance_url):
    clean_url=re.match(instance_url+course_prefix+".*"+course_page_name,url)
    return clean_url.group(0)[len(instance_url+course_prefix):-len(course_page_name)]


def get_username(url, headers):
    content=get_page(url, headers)
    return re.search('"/u/[^"]*"', str(content)).group(0).split("/")[-1][:-1]

def get_config(instance):
    configuration = { "courses.edx.org" : { "login_page" : "/login_ajax", "account_page": "/account/settings", "course_page_name": "/course", "course_prefix": "/courses/", "instance_url": "https://courses.edx.org" } }
    if instance not in configuration:
        return { "login_page" : "/login_ajax", "account_page": "/account/settings", "course_page_name": "/info", "course_prefix": "/courses/", "instance_url": "https://" + instance }
    else:
        return configuration[instance]

#########################
#   Prepare content     #
#########################
def make_json_tree_and_folder_tree(id,source_json, headers,parent_path,block_id_id,instance_url):
    data=source_json[id]
    data["block_name"]=id
    path=os.path.join(parent_path, data[block_id_id])
    if not os.path.exists(path):
        os.makedirs(path)
    if "descendants" in data:
        new=[]
        for des in data["descendants"]:
            new.append(make_json_tree_and_folder_tree(des,source_json, headers,path,block_id_id,instance_url))
        data["descendants"]=new
    else:
        if data["type"] == "libcast_xblock" or ( data["type"] == "video" and "student_view_data" not in data):
            data["type"] = "video"
            data["student_view_data"]={}
            data["student_view_data"]["encoded_videos"]={}
            try:
                content=get_page(data["student_view_url"],headers).decode('utf-8')
                soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
                url=str(soup.find('video').find('source')["src"])
                data["student_view_data"]["encoded_videos"]["fallback"]={}
                data["student_view_data"]["encoded_videos"]["fallback"]["url"]=url
                data["student_view_data"]["transcripts"]={}
                data["student_view_data"]["transcripts_vtt"]=True
                subs=soup.find('video').find_all('track')
                for track in subs:
                    if track["src"][0:4] == "http":
                        data["student_view_data"]["transcripts"][track["srclang"]]=track["src"]
                    else:
                        data["student_view_data"]["transcripts"][track["srclang"]]=instance_url + track["src"]
            except:
                try:
                    print("TODO youtube")
                except:
                    logging.warning("Sorry we can't get video from" +data["student_view_url"])
        elif data["type"] == "video":
            data["student_view_data"]["transcripts_vtt"]=False
    return data

#########################
#   Content Extractor   #
########################

def get_forum(headers,instance_url,course_id,output):
    url="/courses/" + course_id + "/discussion/forum/?ajax=1&page=1&sort_key=activity&sort_order=desc"
    data=get_api_json(instance_url,url, headers)
    threads=data["discussion_data"]
    for i in range(1,data["num_pages"]):
        url="/courses/" + course_id + "/discussion/forum/?ajax=1&page=" + str(i+1) + "&sort_key=activity&sort_order=desc"
        data=get_api_json(instance_url,url, headers)
        threads+=data["discussion_data"]

    for thread in threads:
        url = "/courses/" + course_id + "/discussion/forum/" + thread["commentable_id"] + "/threads/" + thread["id"] + "?ajax=1&resp_skip=0&resp_limit=100"
        if not os.path.exists(os.path.join(output,"forum",thread["commentable_id"])):
            os.makedirs(os.path.join(output,"forum",thread["commentable_id"]))
        try:
            thread["data_thread"]=get_api_json(instance_url,url,headers)
        except:
            try:
                thread["data_thread"]=get_api_json(instance_url,url,headers)
            except:
                logging.log("Can not get " + instance_url + url + "discussion")

    headers["X-Requested-With"] = ""
    content=get_page(instance_url + "/courses/" +  course_id + "/discussion/forum",headers).decode('utf-8')
    good_content=BeautifulSoup.BeautifulSoup(content, 'html.parser').find("script", attrs={"id": "thread-list-template"}).text
    soup=BeautifulSoup.BeautifulSoup(good_content, 'html.parser')
    all_category=soup.find_all('li', attrs={"class": "forum-nav-browse-menu-item"})
    if len(all_category) == 0:
        soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
        all_category=soup.find_all('li', attrs={"class": "forum-nav-browse-menu-item"})
        
    see=[]
    category={}
    for cat in all_category:
        if not cat.has_attr("data-discussion-id") and cat.find("a") != None:
            random_id=sha256(str(random.random()).encode('utf-8')).hexdigest()
            category[random_id]={"name" : cat.find("a").text.replace("\n",""), "sub_cat":[]}
            bs_sub_cat=cat.find_all("li", attrs={"class": "forum-nav-browse-menu-item"});
            for sub_cat in cat.find_all("li", attrs={"class": "forum-nav-browse-menu-item"}):
                if sub_cat.has_attr("data-discussion-id"):
                    category[random_id]["sub_cat"].append({"data-discussion-id": sub_cat["data-discussion-id"], "title" :str(sub_cat.text).replace("\n","")})
                    see.append(sub_cat["data-discussion-id"])
    for cat in all_category:
        if cat.has_attr("data-discussion-id"):
            if cat["data-discussion-id"] not in see:
                category[cat["data-discussion-id"]] = {"title": str(cat.text).replace("\n","")}

    return [threads, category]

def get_wiki(headers,instance_url,course_id, output):
    page_to_visit=[instance_url + "/courses/" +  course_id + "/course_wiki"]
    page_already_visit={}

    while page_to_visit:
        url = page_to_visit.pop()
        try:
            content=get_page(url,headers).decode('utf-8')
        except HTTPError as e:
            if e.code == 404 or e.code == 403:
                pass

        soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
        text=soup.find("div", attrs={"class": "wiki-article"})
        page_already_visit[url]={}
        if "/course_wiki" in url:
            web_path="wiki"
        else:
            web_path=os.path.join("wiki", url.replace(instance_url + "/wiki/",""))
        path=os.path.join(output, web_path)
        if not os.path.exists(path):
            os.makedirs(path)
        page_already_visit[url]["path"] = path
        rooturl=""
        for x in range(0,len(web_path.split("/"))):
            rooturl+="../"
        page_already_visit[url]["rooturl"]= rooturl

        if text != None : #If it's a page (and not a list of page)

            #Find new wiki page in page content
            for link in text.find_all("a"):
                if link.has_attr("href") and "/wiki/" in link["href"]:
                    if link not in page_already_visit and link not in page_to_visit:
                        if not link["href"][0:4] == "http":
                            page_to_visit.append(instance_url + link["href"])
                        else:
                            page_to_visit.append(link["href"])

                    if not link["href"][0:4] == "http":
                        link["href"] = rooturl[:-1] + link["href"].replace(instance_url,"") + "/index.html"

            page_already_visit[url]["path"] = path
            page_already_visit[url]["text"] = dl_dependencies(str(text),path,"",instance_url)
            page_already_visit[url]["title"] = soup.find("title").text
            page_already_visit[url]["sub_page"] = False

        #find new url of wiki in the page
        see_children=soup.find('div', attrs={"class": "see-children"})
        if see_children:
            allpage_url=str(see_children.find("a")["href"])
            page_already_visit[url]["dir"] = allpage_url 
            content=get_page(instance_url + allpage_url,headers)
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            table=soup.find("table")
            if table != None:
                for link in table.find_all("a"):
                    if link.has_attr("class") and "list-children" in link["class"]:
                        pass
                    else:
                        page_already_visit[url]["sub_page"]=True
                        if link["href"] not in page_already_visit and link["href"] not in page_to_visit:
                            page_to_visit.append(instance_url + link["href"])
                            if "decoule" in page_already_visit[url]:
                                page_already_visit[url]["decoule"].append(instance_url + link["href"])
                            else:
                                page_already_visit[url]["decoule"]= [ instance_url + link["href"] ]
    return page_already_visit

def get_and_save_specific_pages(headers,instance_url,course_id, output,first_page):
    content=get_page(instance_url + "/courses/" +  course_id,headers).decode('utf-8')
    soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
    specific_pages=soup.find('ol', attrs={"class": "course-tabs"}).find_all('li')
    if first_page:
        link_on_top={ first_page : "Course"}
    else:
        link_on_top={}
    page_to_save={}
    for page in specific_pages:
        link=page.find("a")["href"]
        sub_dir=link.replace("/courses/" + unquote(course_id) + "/","")
        if "course_wiki" in sub_dir:
            link_on_top["wiki"]="Wiki"
        elif "discussion/forum" in sub_dir:
            link_on_top["forum"]="Discussion"
        elif "course" not in sub_dir and "edxnotes" not in sub_dir and "progress" not in sub_dir :
            if page.span:
                page.span.clear()
            link_on_top[sub_dir] = page.text.strip()
            if not os.path.exists(os.path.join(output,sub_dir)):
                os.makedirs(os.path.join(output,sub_dir))
            page_content=get_page(instance_url + link,headers).decode('utf-8')
            soup_page=BeautifulSoup.BeautifulSoup(page_content, 'html.parser')
            good_part_of_page_content=str(soup_page.find('section', attrs={"class": "container"}))
            html_content=dl_dependencies(good_part_of_page_content,os.path.join(output,sub_dir),sub_dir,instance_url)
            page_to_save[sub_dir]={}
            page_to_save[sub_dir]["content"]=html_content
            page_to_save[sub_dir]["title"]=soup_page.find('title').text
    #Now we have all link on top
    for sub_dir in page_to_save:
            jinja(
                os.path.join(output,sub_dir,"index.html"),
                "specific_page.html",
                False,
                title=page_to_save[sub_dir]["title"],
                top=link_on_top,
                content=page_to_save[sub_dir]["content"],
                rooturl="../.."
            )
    return link_on_top


def get_content(data, headers,parent_path,block_id_id,instance_url, course_id):
    path=os.path.join(parent_path, data[block_id_id])
    if "descendants" in data:
        for des in data["descendants"]:
            get_content(des, headers, path,block_id_id,instance_url,course_id)
    else:
        if data["type"] == "html":
            content=get_page(data["student_view_url"],headers).decode('utf-8')
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            html_content=str(soup.find('div', attrs={"class": "edx-notes-wrapper"}))
            if html_content=="None":
                html_content=str(soup.find('div', attrs={"class": "course-wrapper"}))
            html_content=dl_dependencies(html_content,path,data[block_id_id],instance_url)
            data["html_content"]=str(html_content)
        elif data["type"] == "problem":
            content=get_page(data["student_view_url"],headers).decode('utf-8')
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            try:
                html_content_from_div=str(soup.find('div', attrs={"class": "problems-wrapper"})['data-content'])
            except:
                problem_json_url=str(soup.find('div', attrs={"class": "problems-wrapper"})['data-url'])
                html_content_from_div=str(get_api_json(instance_url,problem_json_url+"/problem_get",headers)["html"])
            soup=BeautifulSoup.BeautifulSoup(html_content_from_div, 'html.parser')
            for div in soup.find_all('div', attrs={"class": "notification"}):
                div.decompose()
            for input_tag in soup.find_all('input'):
                if input_tag.has_attr("value"):
                    input_tag["value"]=""
                if input_tag.has_attr("checked"):
                        del input_tag.attrs['checked']
            soup.find('div', attrs={"class": "action"}).decompose()
            for span in soup.find_all('span', attrs={"class" : "unanswered"}):
                span.decompose()
            for span in soup.find_all('span', attrs={"class" : "sr"}):
                span.decompose()
            html_content=str(soup)
            html_content=dl_dependencies(html_content,path,data[block_id_id],instance_url)
            data["html_content"]=str(html_content)

            #Save json answers
            path_answers=os.path.join(path,"problem_show")
            answers_content={"success": None}
            retry=0
            while "success" in answers_content and retry < 6: #We use our check to finally get anwers
                answers_content=get_api_json(instance_url,"/courses/" + course_id + "/xblock/" + data["block_name"] + "/handler/xmodule_handler/problem_show", headers)
                if "success" in answers_content:
                    get_api_json(instance_url,"/courses/" + course_id + "/xblock/" + data["block_name"] + "/handler/xmodule_handler/problem_check", headers)
                    retry+=1
            if "success" in answers_content:
                logging.warning(" fail to get answers to this problem : " + data["block_name"])
                data["answers"]=None
            else:
                with open(path_answers,"w") as f:
                    json.dump(answers_content, f)
                data["answers"]=[]
                data["explanation"]=[]
                for qid in answers_content["answers"]:
                    if not "solution" in qid:
                        for response in answers_content["answers"][qid]:
                            data["answers"].append("input_" + qid + "_" + response)
                    else:
                        data["explanation"].append({ "name": "solution_" + qid, "value": json.dumps(answers_content["answers"][qid])})
                data["problem_id"]=sha256(str(random.random()).encode('utf-8')).hexdigest()



        elif data["type"] == "discussion":
            content=get_page(data["student_view_url"],headers).decode('utf-8')
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            discussion_id=str(soup.find('div', attrs={"class": "discussion-module"})['data-discussion-id'])
            minimal_discussion=get_api_json(instance_url,"/courses/" + course_id + "/discussion/forum/" + discussion_id + "/inline?page=1&ajax=1", headers)
            data["discussion"]={}
            data["discussion"]["discussion_data"]=minimal_discussion["discussion_data"]
            if minimal_discussion["num_pages"] != 1:
                for i in range(2,minimal_discussion["num_pages"]+1):
                    data["discussion"]["discussion_data"]+=get_api_json(instance_url,"/courses/" + course_id + "/discussion/forum/" + discussion_id + "/inline?page=" + str(i) + "&ajax=1", headers)["discussion_data"]



        elif data["type"] == "video":
            video_path=os.path.join(path,"video.mp4")
            video_final_path=os.path.join(path,"video.webm")
            if not os.path.exists(video_final_path):
                try:
                    download(data["student_view_data"]["encoded_videos"]["fallback"]["url"], video_path,instance_url)
                    convert_video_to_webm(video_path, video_final_path)
                except Exception as e:
                    try:
                        download(data["student_view_data"]["encoded_videos"]["mobile_low"]["url"], video_path,instance_url)
                        convert_video_to_webm(video_path, video_final_path)
                    except Exception as e:
                        try:
                            download_youtube(data["student_view_data"]["encoded_videos"]["youtube"]["url"], video_path)
                        except Exception as e:
                            data["html_content"]="<h3> Sorry, this video is not available </h3>"
                            return data
            download_and_convert_subtitles(path,data["student_view_data"]["transcripts"],data["student_view_data"]["transcripts_vtt"],headers)
            data["video_path"]=os.path.join(data[block_id_id], "video.webm")
            data["transcripts_file"]=[ {"file": os.path.join(data[block_id_id], lang + ".vtt"), "code": lang } for lang in data["student_view_data"]["transcripts"] ]

    return data

#########################
# Tools                 #
#########################

def markdown(text):
    return MARKDOWN(text)[3:-5]

def remove_newline(text):
    return text.replace("\n", "")

def download(url, output, instance_url,timeout=None,):
    if url[0:2] == "//":
            url="http:"+url
    elif url[0] == "/":
            url= instance_url + url
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    request_headers={'User-Agent': 'Mozilla/5.0'}
    request = Request(url, headers=request_headers)
    response = urlopen(request, timeout=timeout, context=ctx)
    output_content = response.read()
    with open(output, 'wb') as f:
        f.write(output_content)
    return response.headers

def download_and_convert_subtitles(path,transcripts_data,already_in_vtt,headers):
    for lang in transcripts_data:
        path_lang=os.path.join(path,lang + ".vtt")
        if not os.path.exists(path_lang):
            try:
                subtitle=get_page(transcripts_data[lang],headers).decode('utf-8')
                subtitle=re.sub(r'^0$', '1', str(subtitle), flags=re.M)
                with open(path_lang, 'w') as f:
                    f.write(subtitle)
                if not already_in_vtt:
                    webvtt = WebVTT().from_srt(path_lang)
                    webvtt.save()
            except HTTPError as e:
                if e.code == 404 or e.code == 403:
                    pass

def download_youtube(youtube_url, video_path):
    parametre={"outtmpl" : video_path, 'progress_hooks': [hook_youtube_dl], 'preferredcodec': 'mp4', 'format' : 'mp4'}
    with youtube_dl.YoutubeDL(parametre)  as ydl:
        ydl.download([youtube_url])

def hook_youtube_dl(data):
    if data["status"] == "finished":
        video_final_path=re.sub(r'\.mp4$', '.webm', data["filename"])
        convert_video_to_webm(data["filename"], video_final_path)

def convert_video_to_webm(video_path, video_final_path):
    logging.info("convert " + video_path + "to webm")
    if bin_is_present("avconv"):
        cmd="avconv -y -i file:" + video_path + " -codec:v libvpx -qscale 1 -cpu-used 0 -b:v 300k -qmin 30 -qmax 42 -maxrate 300k -bufsize 1000k -threads 8 -vf scale=480:-1 -codec:a libvorbis -b:a 128k file:" +  video_final_path
        if exec_cmd(cmd) == 0:
            os.remove(video_path)
        else:
            logging.warning("Error when convert " + video_path + " to webm")
    else:
        cmd="ffmpeg -y -i file:" + video_path + " -codec:v libvpx -quality best -cpu-used 0 -b:v 300k -qmin 30 -qmax 42 -maxrate 300k -bufsize 1000k -threads 8 -vf scale=480:-1 -codec:a libvorbis -b:a 128k file:" + video_final_path
        if exec_cmd(cmd) == 0:
            os.remove(video_path)
        else:
            logging.warning("Error when convert " + video_path + " to webm")

def get_filetype(headers,path):
    file_type=headers.get_content_type()
    type="none"
    if ("png" in file_type) or ("PNG" in file_type):
        type="png"
    elif ("jpg" in file_type) or ("jpeg" in file_type) or ("JPG" in file_type) or ("JPEG" in file_type):
        type="jpeg"
    elif ("gif" in file_type) or ("GIF" in file_type):
        type="gif"
    return type

def dl_dependencies(content,path, folder_name,instance_url):
    body = string2html(content)
    imgs = body.xpath('//img')
    for img in imgs:
        if "src" in img.attrib:
            src = img.attrib['src']
            ext = os.path.splitext(src.split("?")[0])[1]
            filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
            out = os.path.join(path, filename)
            # download the image only if it's not already downloaded
            if not os.path.exists(out): 
                try:
                    headers=download(src, out,instance_url, timeout=180)
                    type_of_file=get_filetype(headers,out)
                    # update post's html
                    resize_one(out,type_of_file,"540")
                    optimize_one(out,type_of_file)
                except :
                    logging.warning("error with " + src)
                    pass
            src = os.path.join(folder_name,filename)
            img.attrib['src'] = src
            img.attrib['style']= "max-width:100%"
    docs = body.xpath('//a')
    for a in docs:
        if "href" in a.attrib:
            src = a.attrib['href']
            ext = os.path.splitext(src.split("?")[0])[1]
            filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
            out = os.path.join(path, filename)
            # download the image only if it's not already downloaded
            if ext in [".doc", ".docx", ".pdf", ".DOC", ".DOCX", ".PDF"]: #TODO better solution for extention (black list?)
                if not os.path.exists(out):
                    try:
                        headers=download(src, out,instance_url, timeout=180)
                    except : 
                        logging.warning("error with " + src)
                        pass
                src = os.path.join(folder_name,filename )
                a.attrib['href'] = src
    csss = body.xpath('//link')
    for css in csss:
        if "href" in css.attrib:
            src = css.attrib['href']
            ext = os.path.splitext(src.split("?")[0])[1]
            filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
            out = os.path.join(path, filename)
            if not os.path.exists(out):
                try:
                    headers=download(src, out,instance_url, timeout=180)
                except :
                    logging.warning("error with " + src)
                    pass
            src = os.path.join(folder_name,filename )
            css.attrib['href'] = src 
    jss = body.xpath('//script')
    for js in jss:
        if "src" in js.attrib:
            src = js.attrib['src']
            ext = os.path.splitext(src.split("?")[0])[1]
            filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
            out = os.path.join(path, filename)
            if not os.path.exists(out):
                try:
                    headers=download(src, out,instance_url, timeout=180)
                except :
                    logging.warning("error with " + src)
                    pass
            src = os.path.join(folder_name,filename )
            js.attrib['href'] = src 
    if imgs or docs or csss or jss:
        content = html2string(body, encoding="unicode")
    return content

def optimize_one(path,type):
    if type == "jpeg":
        exec_cmd("jpegoptim --strip-all -m50 " + path, timeout=10)
    elif type == "png" :
        exec_cmd("pngquant --verbose --nofs --force --ext=.png " + path, timeout=10)
        exec_cmd("advdef -q -z -4 -i 5  " + path, timeout=10)
    elif type == "gif":
        exec_cmd("gifsicle --batch -O3 -i " + path, timeout=10)

def resize_one(path,type,nb_pix):
    if type in ["gif", "png", "jpeg"]:
        exec_cmd("mogrify -resize "+nb_pix+"x\> " + path, timeout=10)

#########################
#      Generator        #
#########################
def vertical_list(data,parent_path,block_id_id):
    path=os.path.join(parent_path, data[block_id_id])
    vertical_path_list=[]
    
    if data["type"] != "vertical" and "descendants" in data:
        for des in data["descendants"]:
            vertical_path_list = vertical_path_list + vertical_list(des,path,block_id_id)

    elif data["type"] == "vertical":
        if data["block_counts"]["video"] != 0:
            type_icon="glyphicon glyphicon-facetime-video"
        elif data["block_counts"]["problem"] != 0:
            type_icon="glyphicon glyphicon-question-sign"
        elif data["block_counts"]["discussion"] != 0:
            type_icon="glyphicon glyphicon-comment"
        else:
            type_icon="glyphicon glyphicon-book"
        vertical_path_list.append({ "url" :path, "type_icon": type_icon, "title": data["display_name"], "my_id": data[block_id_id]})
    return vertical_path_list


def render_course(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,block_id_id,link_on_top):
    path=os.path.join(parent_path, data[block_id_id])
    all_data=data
    for des in data["descendants"]:
        vertical_num_start=render_chapter(des,vertical_path_list,output_path,path,vertical_num_start,vertical_num_stop,all_data,block_id_id,link_on_top)
    jinja(
        os.path.join(output_path,path,"index.html"),
        "course_menu.html",
        False,
        course=data,
        sidenav=True,
        all_data=all_data,
        top=link_on_top,
        rooturl=".."
    )

def render_chapter(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,all_data,block_id_id,link_on_top):
    path=os.path.join(parent_path, data[block_id_id])
    jinja(
        os.path.join(output_path,path,"index.html"),
        "chapter_menu.html",
        False,
        chapter=data,
        all_data=all_data,
        sidenav=True,
        sidenav_chapter=data[block_id_id],
        top=link_on_top,
        rooturl="../../.."
    )
    for des in data["descendants"]:
        vertical_num_start=render_sequential(des,vertical_path_list,output_path,path,vertical_num_start,vertical_num_stop,all_data,block_id_id,link_on_top,data[block_id_id])
    return vertical_num_start

def render_sequential(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,all_data,block_id_id,link_on_top,chapter):
    path=os.path.join(parent_path, data[block_id_id])
    vertical_num_stop=vertical_num_start+len(data["descendants"])
    next_in_sequence=1
    for des in data["descendants"]:
        render_vertical(des,vertical_path_list,output_path,path,vertical_num_start,vertical_num_stop,all_data,next_in_sequence,block_id_id,link_on_top,chapter,data[block_id_id])
        next_in_sequence+=1
    return vertical_num_stop

def render_vertical(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,all_data,next_in_sequence,block_id_id,link_on_top,chapter,sequential):
    path=os.path.join(parent_path, data[block_id_id])
    if vertical_num_start == 0:
        pred_seq=None
    else:
        pred_seq=vertical_path_list[vertical_num_start-1]
    if vertical_num_start+next_in_sequence >= len(vertical_path_list):
        next_seq=None
    else:
        next_seq=vertical_path_list[vertical_num_start+next_in_sequence]
    video=False
    for elem in data["descendants"]:
        if elem["type"] == "video":
            video=True
    jinja(
        os.path.join(output_path,path,"index.html"),
        "vertical.html",
        False,
        pred_seq=pred_seq,
        sequential=vertical_path_list[vertical_num_start:vertical_num_stop],
        next_seq=next_seq,
        vertical=data,
        top=link_on_top,
        sidenav=True,
        sidenav_chapter=chapter,
        sidenav_sequential=sequential,
        rooturl="../../../..",
        video=video,
        all_data=all_data
    )
def render_forum(threads,threads_category,output,link_on_top):
    path=os.path.join(output,"forum")
    if not os.path.exists(path):
        os.makedirs(path)
    jinja(
            os.path.join(path,"index.html"),
            "home_category.html",
            False,
            category=threads_category,
            top=link_on_top,
            rooturl=".."
    )
    thread_by_category={}
    for thread in threads: 
        if thread["commentable_id"] not in thread_by_category:
            thread_by_category[thread["commentable_id"]]=[thread]
        else:
            thread_by_category[thread["commentable_id"]].append(thread)
    for category in thread_by_category:
        if not os.path.exists(os.path.join(path, thread["commentable_id"])):
            os.makedirs(os.path.join(path, thread["commentable_id"]))
        jinja(
                os.path.join(path,category,"index.html"),
                "home_discussion.html",
                False,
                threads=thread_by_category[category],
                top=link_on_top,
                rooturl="../.."
        )
    for thread in threads:
        if not os.path.exists(os.path.join(path,thread["commentable_id"],thread["id"])):
            os.makedirs(os.path.join(path,thread["commentable_id"],thread["id"]))
        jinja(
                os.path.join(path,thread["commentable_id"],thread["id"],"index.html"),
                "thread.html",
                False,
                thread=thread,
                top=link_on_top,
                rooturl="../../.."
        )

def render_wiki(wiki_data, instance_url,course_id,output,link_on_top):
    path=os.path.join(output,"wiki")
    if not os.path.exists(path):
        os.makedirs(path)

    for page in wiki_data:
        if "text" in wiki_data[page]: #this is a page
            jinja(
                os.path.join(wiki_data[page]["path"],"index.html"),
                "wiki_page.html",
                False,
                content=wiki_data[page],
                dir=wiki_data[page]["dir"].replace(instance_url + "/wiki/","") + "index.html",
                top=link_on_top,
                rooturl=wiki_data[page]["rooturl"]
            )
    
        if not os.path.exists(os.path.join(wiki_data[page]["path"],"_dir")):
                os.makedirs(os.path.join(wiki_data[page]["path"],"_dir"))
        if "decoule" in wiki_data[page]: #this is a list page
            page_to_list=[]
            for sub_page in wiki_data[page]["decoule"]:
                if "title" in wiki_data[sub_page]:
                    page_to_list.append({ "url": wiki_data[page]["rooturl"]+ "/.." + sub_page.replace(instance_url,""), "title": wiki_data[sub_page]["title"]})
            jinja(
                os.path.join(wiki_data[page]["path"],"_dir","index.html"),
                "wiki_list.html",
                False,
                pages=page_to_list,
                top=link_on_top,
                rooturl=wiki_data[page]["rooturl"] + "/.."
            )
        else: #list page with no sub page
            jinja(
                os.path.join(wiki_data[page]["path"],"_dir","index.html"),
                "wiki_list_none.html",
                False,
                top=link_on_top,
                rooturl=wiki_data[page]["rooturl"] + "/.."
            )

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

def jinja(output, template, deflate, **context):
    template = ENV.get_template(template)
    page = template.render(**context)
    with open(output, 'w') as f:
        if deflate:
            f.write(zlib.compress(page.encode('utf-8')))
        else:
            f.write(page)

def jinja_return(template, **context):
    template = ENV.get_template(template)
    page = template.render(**context)
    return page
 

def jinja_init(templates):
    global ENV
    templates = os.path.abspath(templates)
    ENV = Environment(loader=FileSystemLoader((templates,)))
    filters = dict(
            slugify=slugify,
            markdown=markdown,
            remove_newline=remove_newline,
        )
    ENV.filters.update(filters)

#########################
#     Zim generation    #
#########################
def exec_cmd(cmd, timeout=None):
    try:
        return call(shlex.split(cmd), timeout=timeout)
    except Exception as e:
        logging.error(e)
        pass

def bin_is_present(binary):
    try:
        subprocess.Popen(binary,
                         universal_newlines=True,
                         shell=False,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         bufsize=0)
    except OSError:
        return False
    else:
        return True

def create_zims(title, lang_input, publisher,description, creator,html_dir,zim_path,noindex):
    if zim_path == None:
        zim_path = os.path.join("output/", "{title}_{lang}_all_{date}.zim".format(title=slugify(title),lang=lang_input,date=datetime.datetime.now().strftime('%Y-%m')))
    if description == "":
        description = "Sorry, no description provided"

    logging.info("Writting ZIM for {}".format(title))

    context = {
        'languages': lang_input,
        'title': title,
        'description': description,
        'creator': creator,
        'publisher': publisher,
        'home': 'index.html',
        'favicon': 'favicon.png',
        'static': html_dir,
        'zim': zim_path
    }

    if noindex:
        cmd = ('zimwriterfs --welcome="{home}" --favicon="{favicon}" '
           '--language="{languages}" --title="{title}" '
           '--description="{description}" '
           '--creator="{creator}" --publisher="{publisher}" "{static}" "{zim}"'
           .format(**context))
    else:
        cmd = ('zimwriterfs --withFullTextIndex --welcome="{home}" --favicon="{favicon}" '
           '--language="{languages}" --title="{title}" '
           '--description="{description}" '
           '--creator="{creator}" --publisher="{publisher}" "{static}" "{zim}"'
           .format(**context))
    logging.info(cmd)

    if exec_cmd(cmd) == 0:
        logging.info("Successfuly created ZIM file at {}".format(zim_path))
        return True
    else:
        logging.error("Unable to create ZIM file :(")
        return False


def run():
    arguments = docopt(__doc__, version='0.1')
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    if not arguments['--nozim'] and not bin_is_present("zimwriterfs"):
        sys.exit("zimwriterfs is not available, please install it.")
    for bin in [ "jpegoptim", "pngquant", "advdef", "gifsicle", "mogrify"]:
        if not bin_is_present(bin):
            sys.exit(bin + " is not available, please install it.")
    if not (bin_is_present("ffmpeg") or bin_is_present("avconv")):
        sys.exit("You should install ffmpeg or avconv")
    if arguments["--password"] == None:
        arguments["--password"]=getpass.getpass(stream=sys.stderr)
    
    logging.info("login, get username and parse url")
    instance=arguments["<course_url>"].split("//")[1].split("/")[0]
    try:
        conf=get_config(instance)
    except:
        sys.exit("No configuation found for this instance, please open a issue https://github.com/openzim/openedx/issues")
    jinja_init(os.path.join(os.path.abspath(os.path.dirname(__file__)),"templates/"))

    headers = make_headers(conf["instance_url"],conf["login_page"])
    connection= login(conf["instance_url"],conf["login_page"], headers, arguments["<email>"] , arguments["--password"])
    if not connection.get('success', False):
        sys.exit("error at connection (Email or password is incorrect)")
    else:
        logging.info("Your login is ok!")

    username=get_username(conf["instance_url"] + conf["account_page"], headers)
    course_id=get_course_id(arguments["<course_url>"], conf["course_page_name"], conf["course_prefix"], conf["instance_url"])
    course_id=quote_plus(course_id)

    global MARKDOWN
    MARKDOWN = mistune.Markdown()

    logging.info("Get info about course")
    info=get_api_json(conf["instance_url"], "/api/courses/v1/courses/" + course_id + "?username="+username, headers)
    output=os.path.join("output",slugify(info["name"]))
    if not os.path.exists(output):
        os.makedirs(output)


    logging.info("Get course blocks")
    blocks=get_api_json(conf["instance_url"], "/api/courses/v1/blocks/?course_id=" + course_id + "&username="+username +"&depth=all&requested_fields=graded,format,student_view_multi_device&student_view_data=video,discussion&block_counts=video,discussion,problem&nav_depth=3", headers)

    logging.info("Find root block")
    course_root=None
    for x in blocks["blocks"]:
        if "block_id" not in blocks["blocks"][x]:
            blocks["blocks"][x]["block_id"] =sha256(str(random.random()).encode('utf-8')).hexdigest()
        blocks["blocks"][x]["folder_id"]=slugify(blocks["blocks"][x]["display_name"])
        if blocks["blocks"][x]["type"] == "course":
            blocks["blocks"][x]["folder_id"]="course"
            course_root=x

    block_id_id="folder_id"
    logging.info("Make folder tree")
    json_tree=make_json_tree_and_folder_tree(course_root,blocks["blocks"], headers, output,block_id_id,conf["instance_url"]) 

    logging.info("Get content")
    json_tree_content=get_content(json_tree, headers,output,block_id_id,conf["instance_url"],course_id) 
    vertical_path_list=vertical_list(json_tree_content,"/",block_id_id)

    if len(vertical_path_list) != 0:
        logging.info("Try to get specific page of mooc")
        link_on_top=get_and_save_specific_pages(headers,conf["instance_url"],course_id,output,vertical_path_list[0]["url"])
        logging.info("Render course")
        render_course(json_tree_content,vertical_path_list,output,"",0,0,block_id_id,link_on_top)
    else:
        logging.info("Try to get specific page of mooc")
        link_on_top=get_and_save_specific_pages(headers,conf["instance_url"],course_id,output,False)
        logging.warning("This course has no content")

    if "forum" in link_on_top:
        logging.info("Get discussion")
        threads, threads_category =get_forum(headers,conf["instance_url"],course_id,output)
        render_forum(threads,threads_category,output,link_on_top)

    if "wiki" in link_on_top:
        logging.info("Get wiki")
        wiki_page=get_wiki(headers,conf["instance_url"],course_id,output)
        render_wiki(wiki_page, conf["instance_url"],course_id,output,link_on_top)

    make_welcome_page(output,arguments["<course_url>"],headers,info["name"],instance,conf["instance_url"],link_on_top)

    logging.info("Create zim")
    copy_tree(os.path.join(os.path.abspath(os.path.dirname(__file__)) ,'static'), os.path.join(output, 'static'))
    if not arguments['--nozim']:
        done=create_zims(info["name"],"eng",arguments["<publisher>"],info["short_description"], info["org"],output,arguments["--zimpath"],arguments["--nofulltextindex"])


if __name__ == '__main__':
    run()

