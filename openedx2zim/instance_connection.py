import copy
import getpass
import http
import json
import sys
import requests

from .constants import getLogger, LANGUAGE_COOKIES, OPENEDX_LANG_MAP

logger = getLogger()



class InstanceConnection:
    def __init__(self, email, password, instance_config, locale, build_dir, debug):
        self.email = email
        self.password = password if password else getpass.getpass(stream=sys.stderr)
        self.instance_config = instance_config
        self.cookie_jar = http.cookiejar.LWPCookieJar("lol.cookies")
        self.headers = None
        self.instance_connection = None
        self.user = None
        self.locale = locale
        self.build_dir = build_dir
        self.debug = debug

    def get_response(self, url, post_data, headers, max_attempts=5):
        req = requests.post(url, data=post_data, headers=headers)
        for attempt in range(max_attempts):
            try:
                requests.urlopen(req).content.decode("utf-8")
            except requests.exceptions.HTTPError as exc:
                logger.debug(f"HTTP Error (won't retry this kind of error) while opening {url}: {exc}")
                if self.debug:
                    responseData = exc.read().decode("utf8", 'ignore')
                    print(responseData, file=sys.stderr)
                raise exc
            except requests.exceptions.RequestException as exc:
                if attempt < max_attempts - 1:
                    logger.debug(f"Error opening {url}: {exc}\nRetrying ...")
                    continue
                logger.debug(
                    f"Error opening {url}: {exc},"
                    f" max attempts ({max_attempts}) exceeded"
                )
                raise exc
            except Exception as exc:
                logger.debug(f"Fatal error opening {url}: {exc}")
                raise exc

    def update_csrf_token_in_headers(self):
        csrf_token = None
        for cookie in self.cookie_jar:
            if cookie.name == "csrftoken":
                csrf_token = cookie.value
        self.headers.update({"X-CSRFToken": csrf_token})

    def generate_connection_headers(self):
        opener = requests.Session().cookies.update(self.cookie_jar)
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]
        requests.Session().cookies = opener.cookies
        opener.open(self.instance_config["instance_url"] + "/login")
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Referer": self.instance_config["instance_url"]
            + self.instance_config["login_page"],
            "X-Requested-With": "XMLHttpRequest",
        }
        self.update_csrf_token_in_headers()

    def establish_connection(self):
        self.generate_connection_headers()
        post_data = {"email": self.email, "password": self.password, "remember": False}
        # API login can also be used : /user_api/v1/account/login_session/
        self.instance_connection = self.get_api_json(
            self.instance_config["login_page"], post_data, max_attempts=1
        )
        if not self.instance_connection.get("success", False):
            raise SystemExit("Provided e-mail or password is incorrect")
        logger.info("Successfully logged in")
        for cookie in self.cookie_jar:
            if cookie.name == "edx-user-info" or cookie.name == "prod-edx-user-info":
                self.user = json.loads(
                    cookie.value.replace(r"\054", ",").replace("\\", "")[1:-1]
                )["username"]
            elif cookie.name in LANGUAGE_COOKIES:
                cookie.value = OPENEDX_LANG_MAP.get(self.locale, self.locale)

    def get_api_json(self, page, post_data=None, referer=None, max_attempts=None):
        self.update_csrf_token_in_headers()
        headers = self.headers
        if referer:
            headers = copy.deepcopy(self.headers)
            headers["Referer"] = referer
        if max_attempts:
            resp = self.get_response(
                self.instance_config["instance_url"] + page, post_data, headers,
                max_attempts=max_attempts
            )
        else:
            resp = self.get_response(
                self.instance_config["instance_url"] + page, post_data, headers
            )
        try:
            json_resp = json.loads(resp)
            return json_resp
        except json.JSONDecodeError as exc:
            logger.debug(f"Failed to decode JSON response below.\n{resp}")
            raise exc

    def get_page(self, url):
        self.update_csrf_token_in_headers()
        headers = copy.deepcopy(self.headers)
        headers["X-Requested-With"] = ""
        return self.get_response(url, None, headers)

    def get_redirection(self, url):
        self.update_csrf_token_in_headers()
        response = requests.get(url, headers=self.headers, allow_redirects=False)
        return response.headers.get('Location', response.url)
