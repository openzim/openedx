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
import requests
import ssl
import getpass
import sys
import json
import logging
import re
import copy

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
        self.conf=get_config(self.instance)
        #Make headers
        self.cookiejar = LWPCookieJar('lol.cookies')
        opener = build_opener(HTTPCookieProcessor(self.cookiejar))
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        install_opener(opener)
        opener.open(self.conf["instance_url"] + "/login")
        cookie = None
        for cookie_ in self.cookiejar:
            if cookie_.name == 'csrftoken':
                cookie = cookie_
        #self.cookiejar.save()
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Referer': self.conf["instance_url"] + self.conf["login_page"],
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': cookie.value
        }
        post_data = urlencode({'email': email,
                            'password': self.pw,
                            'remember': False}).encode('utf-8')
        self.connection=self.get_api_json(self.conf["login_page"],post_data) # We can also use API login : /user_api/v1/account/login_session/
        if not self.connection.get('success', False):
            sys.exit("error at connection (Email or password is incorrect)")
        else:
            logging.info("Your login is ok!")
        for cookie_ in self.cookiejar:
            if cookie_.name == 'edx-user-info' or cookie_.name == 'prod-edx-user-info':
                self.user=json.loads(json.loads(cookie_.value.replace(r'\054', ',')))["username"]

    def get_api_json(self,page, post=None, referer=None):
        if referer:
            tmp_headers = copy.deepcopy(self.headers)
            tmp_headers['Referer'] = referer
            request = Request(self.conf["instance_url"] + page, post, tmp_headers)
            if "hint" in page: #see with xblocks_extractor/Problem.py
                return {}
        else:
            request = Request(self.conf["instance_url"] + page, post, self.headers)

        response = urlopen(request)
        r=response.read().decode('utf-8')
        resp = json.loads(r)
        return resp

    def get_page(self,url):
        h=copy.deepcopy(self.headers)
        h["X-Requested-With"]=""
        request = Request(url, None, h)
        try:
            response = urlopen(request)
        except:
            response = urlopen(request)
        return response.read().decode('utf-8')

    def get_redirection(self,url):
        request = Request(url, None, self.headers)
        response = urlopen(request)
        return response.geturl()
