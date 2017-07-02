#!/usr/bin/env python3
# -*-coding:utf8 -*
"""openedx2zim.

Usage:
  openedx2zim <course_url> <publisher> <email> [--password=<pass>] [--nozim] [--zimpath=<zimpath>]
  openedx2zim (-h | --help)
  openedx2zim --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --password=<pass> you can specify password as arguments or you'll be asked for password
  --nozim       doesn't make zim file, output will be in work/ in normal html
  --zimpath=<zimpath>   Final path of the zim file

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
    request = Request(instance_url + page, None, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    return resp

def get_page(url,headers):
    request = Request(url, None, headers)
    response = urlopen(request)
    return response.read()

def get_course_id(url, course_page_name, course_prefix, instance_url):
    clean_url=re.match(instance_url+course_prefix+".*"+course_page_name,url)
    return clean_url.group(0)[len(instance_url+course_prefix):-len(course_page_name)]


def get_username(url, headers):
    content=get_page(url, headers)
    return re.search('"/u/[^"]*"', str(content)).group(0).split("/")[-1][:-1]

def get_config(instance):
    configuration = { "courses.edx.org" : { "login_page" : "/login_ajax", "account_page": "/account/settings", "course_page_name": "/info", "course_prefix": "/courses/", "instance_url": "https://courses.edx.org" } }
    return configuration[instance]
#########################
#   Prepare content     #
#########################
def make_json_tree_and_folder_tree(id,source_json, headers,parent_path,block_id_id):
    data=source_json[id]
    path=os.path.join(parent_path, data[block_id_id])
    if not os.path.exists(path):
        os.makedirs(path)
    if "descendants" in data:
        new=[]
        for des in data["descendants"]:
            new.append(make_json_tree_and_folder_tree(des,source_json, headers,path,block_id_id))
        data["descendants"]=new
    return data

#########################
#   Content Extractor   #
########################

def get_content(data, headers,parent_path,block_id_id):
    path=os.path.join(parent_path, data[block_id_id])
    if "descendants" in data:
        for des in data["descendants"]:
            get_content(des, headers, path,block_id_id)
    else:
        if data["type"] == "html":
            content=get_page(data["student_view_url"],headers).decode('utf-8')
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            html_content=str(soup.find('div', attrs={"class": "edx-notes-wrapper"}))
            html_content=dl_dependencies(html_content,path,data[block_id_id])
            data["html_content"]=str(html_content)
        elif data["type"] == "problem":
            data["html_content"]="<h3> Sorry, problem are not available for the moment</h3>"
        elif data["type"] == "discution":
            data["html_content"]="<h3> Sorry, this is not available </h3>"
        elif data["type"] == "video":
            video_path=os.path.join(path,"video.mp4")
            video_final_path=os.path.join(path,"video.webm")
            if not os.path.exists(video_final_path):
                if "fallback" in data["student_view_data"]["encoded_videos"]:
                    download(data["student_view_data"]["encoded_videos"]["fallback"]["url"], video_path)
                    convert_video_to_webm(video_path, video_final_path)
                elif "mobile_low" in data["student_view_data"]["encoded_videos"]:
                    download(data["student_view_data"]["encoded_videos"]["mobile_low"]["url"], video_path)
                    convert_video_to_webm(video_path, video_final_path)
                elif "youtube" in data["student_view_data"]["encoded_videos"]:
                    download_youtube(data["student_view_data"]["encoded_videos"]["youtube"]["url"], video_path)
                download_and_convert_subtitles(path,data["student_view_data"]["transcripts"], headers)
            data["video_path"]=os.path.join(data[block_id_id], "video.webm")
            data["transcripts_file"]=[ {"file": os.path.join(data[block_id_id], lang + ".vtt"), "code": lang } for lang in data["student_view_data"]["transcripts"] ]

    return data


def download(url, output, timeout=None):
    if url[0:2] == "//":
            url="http:"+url
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    response = urlopen(url, timeout=timeout, context=ctx)
    output_content = response.read()
    with open(output, 'wb') as f:
        f.write(output_content)
    return response.headers

def download_and_convert_subtitles(path,transcripts_data,headers):
    for lang in transcripts_data:
        path_lang=os.path.join(path,lang + ".vtt")
        subtitle=get_page(transcripts_data[lang],headers).decode('utf-8')
        with open(path_lang, 'w') as f:
            f.write(str(subtitle))
        exec_cmd("sed -i 's/^0$/1/' " + path_lang) #This little hack is use because WebVTT.from_srt check is the first line is 1

        webvtt = WebVTT().from_srt(path_lang)
        webvtt.save()

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

def dl_dependencies(content,path, folder_name):
    body = string2html(content)
    imgs = body.xpath('//img')
    for img in imgs:
        src = img.attrib['src']
        ext = os.path.splitext(src.split("?")[0])[1]
        filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
        out = os.path.join(path, filename)
        # download the image only if it's not already downloaded
        if not os.path.exists(out): 
            try:
                headers=download(src, out, timeout=180)
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
        src = a.attrib['href']
        ext = os.path.splitext(src.split("?")[0])[1]
        filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
        out = os.path.join(path, filename)
        # download the image only if it's not already downloaded
        if ext in [".doc", ".docx", ".pdf", ".DOC", ".DOCX", ".PDF"]: #TODO better solution for extention (black list?)
            if not os.path.exists(out):
                try:
                    headers=download(src, out, timeout=180)
                except :
                    logging.warning("error with " + src)
                    pass
            src = os.path.join(folder_name,filename )
            a.attrib['href'] = src

    if imgs or docs:
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
        vertical_path_list.append({ "url" :path, "type_icon": type_icon, "title": data["display_name"]})
    return vertical_path_list


def render_course(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,):
    path=os.path.join(parent_path, data[block_id_id])
    all_data=data
    for des in data["descendants"]:
        vertical_num_start=render_chapter(des,vertical_path_list,output_path,path,vertical_num_start,vertical_num_stop,all_data,block_id_id)

def render_chapter(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,all_data,block_id_id):
    path=os.path.join(parent_path, data[block_id_id])
    jinja(
        os.path.join(output_path,path,"index.html"),
        "chapter_menu.html",
        False,
        chapter=data,
        all_data=all_data,
        rooturl="../.."
    )
    for des in data["descendants"]:
        vertical_num_start=render_sequential(des,vertical_path_list,output_path,path,vertical_num_start,vertical_num_stop,all_data,block_id_id)
    return vertical_num_start

def render_sequential(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,all_data,block_id_id):
    path=os.path.join(parent_path, data[block_id_id])
    vertical_num_stop=vertical_num_start+len(data["descendants"])
    next_in_sequence=1
    for des in data["descendants"]:
        render_vertical(des,vertical_path_list,output_path,path,vertical_num_start,vertical_num_stop,all_data,next_in_sequence,block_id_id)
        next_in_sequence+=1
    return vertical_num_stop

def render_vertical(data,vertical_path_list,output_path,parent_path,vertical_num_start,vertical_num_stop,all_data,next_in_sequence,block_id_id):
    path=os.path.join(parent_path, data[block_id_id])
    if vertical_num_start == 0:
        pred_seq=None
    else:
        pred_seq=vertical_path_list[vertical_num_start-1]
    if vertical_num_start+next_in_sequence >= len(vertical_path_list):
        next_seq=None
    else:
        next_seq=vertical_path_list[vertical_num_start+next_in_sequence] 
    jinja(
        os.path.join(output_path,path,"index.html"),
        "vertical.html",
        False,
        pred_seq=pred_seq,
        sequential=vertical_path_list[vertical_num_start:vertical_num_stop],
        next_seq=next_seq,
        vertical=data,
        rooturl="../../../..",
        all_data=all_data
    )

def make_welcome_page(first_vertical,output,course_url,headers,mooc_name,instance):
    content=get_page(course_url,headers).decode('utf-8')
    soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
    html_content=soup.find('div', attrs={"id": "msg-content-0"}).prettify()
    if not os.path.exists(os.path.join(output,"home")):
        os.makedirs(os.path.join(output,"home"))
    html_content_offline=dl_dependencies(html_content,os.path.join(output, "home"),"home")
    jinja(
        os.path.join(output,"index.html"),
        "home.html",
        False,
        first_vertical=first_vertical,
        first_message=html_content_offline,
        mooc_name=mooc_name
    )
    download("https://www.google.com/s2/favicons?domain=" + instance,os.path.join(output,"favicon.png"))

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
    filters = dict(slugify=slugify)
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

def create_zims(title, lang_input, publisher,description, creator,html_dir,zim_path):
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

    cmd = ('zimwriterfs --welcome="{home}" --favicon="{favicon}" '
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
    arguments = docopt(__doc__, version='0.0')
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    if not arguments['--nozim'] and not bin_is_present("zimwriterfs"):
        sys.exit("zimwriterfs is not available, please install it.")
    for bin in [ "jpegoptim", "pngquant", "advdef", "gifsicle", "mogrify", "sed" ]:
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

    logging.info("Get info about course")
    info=get_api_json(conf["instance_url"], "/api/courses/v1/courses/" + course_id, headers)
    output=os.path.join("output",slugify(info["name"]))
    if not os.path.exists(output):
        os.makedirs(output)

    logging.info("Get course blocks")
    blocks=get_api_json(conf["instance_url"], "/api/courses/v1/blocks/?course_id=" + course_id + "&username="+username +"&depth=all&requested_fields=graded,format,student_view_multi_device&student_view_data=video,discussion&block_counts=video,discussion,problem&nav_depth=3", headers)

    logging.info("Find root block")
    course_root=None
    for x in blocks["blocks"]:
        if blocks["blocks"][x]["type"] == "course":
            course_root=x


    block_id_id="block_id"
    #TODO : we need to do something because some instance/course doesn't have block_id
    logging.info("Make folder tree")
    json_tree=make_json_tree_and_folder_tree(course_root,blocks["blocks"], headers, output,block_id_id) 

    logging.info("Get content")
    json_tree_content=get_content(json_tree, headers,output,block_id_id) 
    vertical_path_list=vertical_list(json_tree_content,"/",block_id_id)

    logging.info("Render course")
    render_course(json_tree_content,vertical_path_list,output,"",0,0,block_id_id)
    make_welcome_page(vertical_path_list[0],output,arguments["<course_url>"],headers,info["name"],instance)

    logging.info("Create zim")
    copy_tree(os.path.join(os.path.abspath(os.path.dirname(__file__)) ,'static'), os.path.join(output, 'static'))
    if not arguments['--nozim']:
        done=create_zims(info["name"],"eng",arguments["<publisher>"],info["short_description"], info["org"],output,arguments["--zimpath"])



if __name__ == '__main__':
    run()

