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
import getpass
import sys
import json
import logging
import re

def get_config(instance):
        configuration = { "courses.edx.org" : { "login_page" : "/login_ajax", "account_page": "/account/settings", "course_page_name": "/course", "course_prefix": "/courses/", "instance_url": "https://courses.edx.org" }, "courses.edraak.org" :  {"login_page" : "/login_ajax", "account_page": "/account/settings", "course_page_name": "/", "course_prefix": "/courses/", "instance_url": "https://courses.edraak.org" } }
        if instance not in configuration:
            return { "login_page" : "/login_ajax", "account_page": "/account/settings", "course_page_name": "/info", "course_prefix": "/courses/", "instance_url": "https://" + instance }
        else:
            return configuration[instance]

class Connection:

    def __init__(self,password,course_url,email):
        if password == None:
            self.pw=getpass.getpass(stream=sys.stderr)
        else:
            self.pw=password
        self.instance=course_url.split("//")[1].split("/")[0]
        self.conf=get_config(self.instance) #but in object
        if self.conf == None:
            sys.exit("No configuation found for this instance, please open a issue https://github.com/openzim/openedx/issues")
        #Make headers
        cookiejar = LWPCookieJar()
        opener = build_opener(HTTPCookieProcessor(cookiejar))
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        install_opener(opener)
        opener.open(self.conf["instance_url"])
        for cookie_ in cookiejar:
            if cookie_.name == 'csrftoken':
                cookie = cookie_
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Referer': self.conf["instance_url"] + self.conf["login_page"],
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': cookie.value,
        }
        post_data = urlencode({'email': email,
                            'password': self.pw,
                            'remember': False}).encode('utf-8')
        self.connection=self.get_api_json(self.conf["login_page"],post_data) # We can also use API login : /user_api/v1/account/login_session/
        if not self.connection.get('success', False):
            sys.exit("error at connection (Email or password is incorrect)")
        else:
            logging.info("Your login is ok!")
        for cookie_ in cookiejar:
            if cookie_.name == 'edx-user-info' or cookie_.name == 'prod-edx-user-info':
                self.user=json.loads(json.loads(cookie_.value.replace(r'\054', ',')))["username"]

    def get_api_json(self,page, post=None, referer=None):
        if referer:
            tmp_headers = self.headers
            tmp_headers['Referer'] = referer
            request = Request(self.conf["instance_url"] + page, post, tmp_headers)
        else:
            request = Request(self.conf["instance_url"] + page, post, self.headers)
        response = urlopen(request)
        resp = json.loads(response.read().decode('utf-8'))
        return resp

    def get_page(self,url):
        request = Request(url, None, self.headers)
        try:
            response = urlopen(request)
        except:
            response = urlopen(request)
        return response.read()


    """
    def get_and_save_specific_pages(self,course_id, output,first_page):
        content=get_page(self.instance_url + "/courses/" +  course_id,self.headers).decode('utf-8')
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
                html_content=dl_dependencies(good_part_of_page_content,os.path.join(output,sub_dir),sub_dir,c)
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
    """

