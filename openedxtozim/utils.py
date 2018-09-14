import subprocess
import shlex
import os
import datetime
import logging
from jinja2 import Environment
from jinja2 import FileSystemLoader
from slugify import slugify
import ssl
import html
from urllib.error import HTTPError, URLError
from urllib.request import urlopen,Request
import urllib.parse
from urllib.parse import urlparse
from urllib.parse import unquote
from lxml.etree import parse as string2xml
from lxml.html import fromstring as string2html
from lxml.html import tostring as html2string
from hashlib import sha256
from webvtt import WebVTT
import youtube_dl
import re
from iso639 import languages as iso_languages
import mistune #markdown

MARKDOWN = mistune.Markdown()

def is_absolute(url):
    return bool(urlparse(url).netloc)

def exec_cmd(cmd, timeout=None):
    try:
        return subprocess.call(shlex.split(cmd), timeout=timeout)
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

def check_missing_binary(no_zim):
    if not no_zim and not bin_is_present("zimwriterfs"):
        sys.exit("zimwriterfs is not available, please install it.")
    for bin in [ "jpegoptim", "pngquant", "advdef", "gifsicle", "mogrify"]:
        if not bin_is_present(bin):
            sys.exit(bin + " is not available, please install it.")
    if not (bin_is_present("ffmpeg") or bin_is_present("avconv")):
        sys.exit("You should install ffmpeg or avconv")

def create_zims(title, lang_input, publisher,description, creator,html_dir,zim_path,noindex,home):
    if zim_path == None:
        zim_path = os.path.join("output/", "{title}_{lang}_all_{date}.zim".format(title=slugify(title),lang=lang_input,date=datetime.datetime.now().strftime('%Y-%m')))

    if description == "":
        description = " "

    logging.info("Writting ZIM for {}".format(title))

    context = {
        'languages': iso_languages.get(alpha2=lang_input,).part3,
        'title': title,
        'description': description,
        'creator': creator,
        'publisher': publisher,
        'home': home,
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

def markdown(text):
    return MARKDOWN(text)[3:-5].replace("\n","<br>")

def remove_newline(text):
    return text.replace("\n", "")

def download(url, output, instance_url,timeout=20,retry=2):
    if url[0:2] == "//":
            url="http:"+url
    elif url[0] == "/":
            url= instance_url + url

    #for IRI
    split_url = list(urllib.parse.urlsplit(url))
    #split_url[2] = urllib.parse.quote(split_url[2])    # the third component is the path of the URL/IRI
    url = urllib.parse.urlunsplit(split_url)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    request_headers={'User-Agent': 'Mozilla/5.0'}
    try:
        request = Request(url, headers=request_headers)
        response = urlopen(request, timeout=timeout, context=ctx)
        output_content = response.read()
        with open(output, 'wb') as f:
            f.write(output_content)
        return response.headers
    except HTTPError as e:
        if retry >= 0:
            if e.code == 403 or e.code == 404:
                logging.warning(str(e.code) + " : " + url)
                return False
            logging.warning(str(e) + " : " + url + " but retry download")
            return download(url, output, instance_url,timeout=timeout,retry=retry-1)
        else:
            return False


def download_and_convert_subtitles(path,lang_and_url,c):
    real_subtitles={}
    for lang in lang_and_url:
        path_lang=os.path.join(path,lang + ".vtt")
        if not os.path.exists(path_lang):
            try:
                subtitle=c.get_page(lang_and_url[lang])
                subtitle=re.sub(r'^0$', '1', str(subtitle), flags=re.M)
                subtitle=html.unescape(subtitle)
                with open(path_lang, 'w') as f:
                    f.write(subtitle)
                if not is_webvtt(path_lang):
                    webvtt = WebVTT().from_srt(path_lang)
                    webvtt.save()
                real_subtitles[lang]=lang + ".vtt"
            except HTTPError as e:
                if e.code == 404 or e.code == 403:
                    logging.error("Fail to get subtitle from {}".format(lang_and_url[lang]))
                    pass
            except Exception as e:
                logging.error("Error when converting subtitle {} : {}".format(lang_and_url[lang],e))
                pass
        else:
            real_subtitles[lang]=lang + ".vtt"
    return real_subtitles

def is_webvtt(path):
    f = open(path,"r")
    first_line = f.readline()
    f.close()
    return "WEBVTT" in first_line or "webvtt" in first_line

def download_youtube(youtube_url, video_path):
    parametre={"outtmpl" : video_path, 'preferredcodec': 'mp4', 'format' : 'mp4'}
    with youtube_dl.YoutubeDL(parametre)  as ydl:
        ydl.download([youtube_url])

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
    if headers == None:
        file_type=os.path.splitext(path.split("?")[0])[1]
    else:
        file_type=headers.get_content_type()
    type="none"
    if ("png" in file_type) or ("PNG" in file_type):
        type="png"
    elif ("jpg" in file_type) or ("jpeg" in file_type) or ("JPG" in file_type) or ("JPEG" in file_type):
        type="jpeg"
    elif ("gif" in file_type) or ("GIF" in file_type):
        type="gif"
    return type

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

def jinja(output, template,deflate, **context):
    template = ENV.get_template(template)
    page = template.render(**context, output_path=output)
    if output == None:
        return page
    else:
        with open(output, 'w') as f:
            if deflate:
                f.write(zlib.compress(page.encode('utf-8')))
            else:
                f.write(page)

def jinja_init():
    global ENV
    templates = os.path.join(os.path.abspath(os.path.dirname(__file__)),"templates/")
    ENV = Environment(loader=FileSystemLoader((templates,)))
    filters = dict(
            slugify=slugify,
            markdown=markdown,
            remove_newline=remove_newline,
            first_word=first_word,
            clean_top=clean_top,
        )
    ENV.filters.update(filters)

def clean_top(t):
        return "/".join(t.split("/")[:-1])

def dl_dependencies(content, path, folder_name,c):
    body = string2html(str(content))
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
                    headers=download(src, out,c.conf["instance_url"], timeout=180)
                    type_of_file=get_filetype(headers,out)
                    optimize_one(out,type_of_file)
                except Exception as e:
                    logging.warning(str(e) + " : error with " + src)
                    pass
            src = os.path.join(folder_name,filename)
            img.attrib['src'] = src
            if 'style' in img.attrib:
                img.attrib['style']+= " max-width:100%"
            else:
                img.attrib['style'] = " max-width:100%"
    docs = body.xpath('//a')
    for a in docs:
        if "href" in a.attrib:
            src = a.attrib['href']
            ext = os.path.splitext(src.split("?")[0])[1]
            filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
            out = os.path.join(path, filename)
            if ext in [".doc", ".docx", ".pdf", ".DOC", ".DOCX", ".PDF", ".mp4", ".MP4", ".webm", ".WEBM", ".mp3", ".MP3", ".zip", ".ZIP", ".TXT", ".txt", ".CSV", ".csv", ".R", ".r"] or (not is_absolute(src) and not "wiki" in src): #Download when ext match, or when link is relatif (but not in wiki, because links in wiki are relatif)
                if not os.path.exists(out):
                    try:
                        download(unquote(src), out,c.conf["instance_url"] , timeout=180) 
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
                    download(src, out,c.conf["instance_url"], timeout=180)
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
                    download(src, out,c.conf["instance_url"], timeout=180)
                except :
                    logging.warning("error with " + src)
                    pass
            src = os.path.join(folder_name,filename )
            js.attrib['src'] = src 
    sources = body.xpath('//source')
    for source in sources:
        if "src" in source.attrib:
            src = source.attrib['src']
            ext = os.path.splitext(src.split("?")[0])[1]
            filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
            out = os.path.join(path, filename)
            if not os.path.exists(out):
                try:
                    download(src, out,c.conf["instance_url"], timeout=180)
                except :
                    logging.warning("error with " + src)
                    pass
            src = os.path.join(folder_name,filename )
            source.attrib['src'] = src
    iframes = body.xpath('//iframe')
    for iframe in iframes:
        if "src" in iframe.attrib:
            src = iframe.attrib['src']
            if "youtube" in src:
                name=src.split("/")[-1]
                out_dir=os.path.join(path, name)
                make_dir(out_dir)
                out=os.path.join(out_dir,"video.mp4")
                if not os.path.exists(out):
                    try:
                        download_youtube(src, out)
                    except Exception as e:
                        logging.warning(str(e) + " : error with " + src)
                        pass
                x = jinja(
                            None,
                            "video.html",
                            False,
                            format="mp4",
                            folder_name=name,
                            subs=[]
                )
                iframe.getparent().replace(iframe,string2html(x))
            elif ".pdf" in src:
                filename_src = src.split("/")[-1]
                ext = os.path.splitext(filename_src.split("?")[0])[1]
                filename = sha256(str(src).encode('utf-8')).hexdigest() + ext
                out = os.path.join(path, filename)
                if not os.path.exists(out):
                    try:
                        download(unquote(src), out,c.conf["instance_url"], timeout=180)
                    except :
                        logging.warning("error with " + src)
                        pass
                src = os.path.join(folder_name,filename )
                iframe.attrib['src'] = src
    if imgs or docs or csss or jss or sources or iframes:
        content = html2string(body, encoding="unicode")
    return content



def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def first_word(text):
    return " ".join(text.split(" ")[0:5])
