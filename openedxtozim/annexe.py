from urllib.parse import urlparse
import bs4 as BeautifulSoup
import os
import re
from uuid import uuid4
import json
from collections import defaultdict, OrderedDict
import logging
from html import unescape
from openedxtozim.utils import make_dir, download, dl_dependencies, jinja, markdown
from urllib.error import HTTPError

def forum(c,mooc):
    forum_output=os.path.join(mooc.output_path, "forum")
    make_dir(forum_output)
    content=c.get_page(mooc.instance_url + "/courses/" +  mooc.course_id + "/discussion/forum")
    good_content=BeautifulSoup.BeautifulSoup(content, 'lxml').find("script", attrs={"id": "thread-list-template"})
    category=OrderedDict()
    if good_content:
        soup=BeautifulSoup.BeautifulSoup(content, 'lxml')

        all_category=soup.find_all('li', attrs={"class": "forum-nav-browse-menu-item"})
        if len(all_category) == 0:
            soup=BeautifulSoup.BeautifulSoup(good_content.text, 'lxml') #On Fun plateform, categorie list is in script with id thread-list-template
            all_category=soup.find_all('li', attrs={"class": "forum-nav-browse-menu-item"}) 
        for cat in all_category:
            if (cat.has_attr("id") and cat["id"] in [ "all_discussions", "posts_following" ]) or (cat.has_attr("class") and ("forum-nav-browse-menu-all" in cat["class"] or "forum-nav-browse-menu-following" in cat["class"])):
                continue
            if not cat.has_attr("data-discussion-id"): #and cat.find("a") != None:
                category[str(uuid4())] = { "title" : cat.find(["a", "span"], attrs={"class": "forum-nav-browse-title"}).text, "catego_with_sub_catego" : True}
            elif cat.has_attr("data-discussion-id"):
                category[cat["data-discussion-id"]] = {"title": str(cat.text).replace("\n","")}

    else:
        logging.error("No forum category found")
    threads=[]

    #Search for Staff user :
    json_user={}
    section_user = BeautifulSoup.BeautifulSoup(content, 'lxml').find("section", attrs={"id": "discussion-container"})
    if section_user and section_user.has_attr("data-roles"):
        if "&#34;" in section_user["data-roles"]:
            json_user = json.loads(unescape(section_user["data-roles"]))
        else:
            json_user = json.loads(section_user["data-roles"])
    else:
        section_user = re.search("roles: [^\n]*", content)
        if section_user: #TODO check ok in this case
            json_user=json.loads(re.sub(r"roles: (.*),", r'\1', section_user.group()))
    staff_user = []
    for x in json_user:
        staff_user += [ str(y) for y in json_user[x]]

    #Search category
    for x in category:
        make_dir(os.path.join(forum_output,x))
        url="/courses/" + mooc.course_id + "/discussion/forum/" + x + "/inline?ajax=1&page=1&sort_key=activity&sort_order=desc"
        data=c.get_api_json(url)
        d=data["discussion_data"]
        threads+=d
        for i in range(1,data["num_pages"]):
            url="/courses/" + mooc.course_id + "/discussion/forum/" + x + "/inline?ajax=1&page=" + str(i+1) + "&sort_key=activity&sort_order=desc"
            data=c.get_api_json(url)
            d=data["discussion_data"]
            threads+=d

    for thread in threads:
        url = "/courses/" + mooc.course_id + "/discussion/forum/" + thread["commentable_id"] + "/threads/" + thread["id"] + "?ajax=1&resp_skip=0&resp_limit=100"
        make_dir(os.path.join(forum_output,thread["id"]))
        try:
            thread["data_thread"]=c.get_api_json(url, referer=mooc.instance_url+url.split("?")[0])
            total_answers = 100
            while total_answers < thread["data_thread"]["content"]["resp_total"]:
                url = "/courses/" + mooc.course_id + "/discussion/forum/" + thread["commentable_id"] + "/threads/" + thread["id"] + "?ajax=1&resp_skip="+ str(total_answers) + "&resp_limit=100"
                new_answers=c.get_api_json(url, referer=mooc.instance_url+url.split("?")[0])["content"]["children"]
                thread["data_thread"]["content"]["children"] += new_answers
                total_answers += 100
        except:
            try:
                thread["data_thread"]=c.get_api_json(url)
            except:
                logging.log("Can not get " + mooc.instance_url + url + "discussion")
        if ("endorsed_responses" in thread["data_thread"]["content"] or "non_endorsed_responses" in thread["data_thread"]["content"]) and "children" in thread["data_thread"]["content"]:
            logging.warning("pb endorsed VS children" + thread["id"])
        if "children" not in thread["data_thread"]["content"]:
            thread["data_thread"]["content"]["children"] = []
        if "endorsed_responses" in thread["data_thread"]["content"]:
            thread["data_thread"]["content"]["children"] += thread["data_thread"]["content"]["endorsed_responses"]
        if "non_endorsed_responses" in thread["data_thread"]["content"]:
            thread["data_thread"]["content"]["children"] += thread["data_thread"]["content"]["non_endorsed_responses"]
        thread["data_thread"]["content"]["body"] = dl_dependencies(markdown(thread["data_thread"]["content"]["body"]),os.path.join(forum_output,thread["id"]),"",c)
        for children in thread["data_thread"]["content"]["children"]:
            children["body"]=dl_dependencies(markdown(children["body"]),os.path.join(forum_output,thread["id"]),"",c)
            if "children" in children:
                for children_children in children["children"]:
                    children_children["body"]=dl_dependencies(markdown(children_children["body"]),os.path.join(forum_output,thread["id"]),"",c)

    return threads, category, staff_user

def render_forum(mooc):
    threads=mooc.forum_thread
    staff_user=mooc.staff_user_forum
    forum_output=os.path.join(mooc.output_path, "forum")
    category=mooc.forum_category

    thread_by_category=defaultdict(list)
    for thread in threads: 
        thread_by_category[thread["commentable_id"]].append(thread)
    jinja(
            os.path.join(forum_output,"index.html"),
            "forum.html",
            False,
            category=category,
            thread_by_category=thread_by_category,
            staff_user=staff_user,
            mooc=mooc,
            rooturl="../",
            display_on_mobile=True
    )
    for thread in threads:
        jinja(
                os.path.join(forum_output,thread["id"],"index.html"),
                "forum.html",
                False,
                thread=thread["data_thread"]["content"],
                category=category,
                thread_by_category=thread_by_category,
		staff_user=staff_user,
                mooc=mooc,
                rooturl="../../../",
                forum_menu=True
        )





def wiki(c,mooc):
    #Get redirection to wiki
    first_page=c.get_redirection(mooc.instance_url + "/courses/" +  mooc.course_id + "/course_wiki")
    page_to_visit=[first_page]
    wiki_data={} #Data from page already visit
    # "[url]" : { "rooturl": , "path": , "text": , "title": , "dir" : , "children": [] }
    #Extract wiki name
    wiki_name = first_page.replace(mooc.instance_url + "/wiki/", "")[:-1]
    wiki_path = os.path.join("wiki", first_page.replace(mooc.instance_url + "/wiki/",""))

    while page_to_visit:
        get_page_error=False
        url = page_to_visit.pop()
        try:
            content=c.get_page(url)
        except HTTPError as e:
            if e.code == 404 or e.code == 403:
                get_page_error=True 
            else:
                logging.warning("Fail to get " + url + "Error :" + str(e.code))
                pass

        wiki_data[url]={}
        web_path=os.path.join("wiki", url.replace(mooc.instance_url + "/wiki/",""))
        path=os.path.join(mooc.output_path, web_path)
        make_dir(path)
        wiki_data[url]["path"] = path
        rooturl="../"
        for x in range(0,len(web_path.split("/"))):
            rooturl+="../"
        wiki_data[url]["rooturl"]= rooturl
        wiki_data[url]["children"]=[]


        #Parse content page
        soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
        text=soup.find("div", attrs={"class": "wiki-article"})
        if text != None : #If it's a page (and not a list of page)
            #Find new wiki page in page content
            for link in text.find_all("a"):
                if link.has_attr("href") and "/wiki/" in link["href"]:
                    if link not in wiki_data and link not in page_to_visit:
                        if not link["href"][0:4] == "http":
                            page_to_visit.append(mooc.instance_url + link["href"])
                        else:
                            page_to_visit.append(link["href"])

                    if not link["href"][0:4] == "http": #Update path in wiki page
                        link["href"] = rooturl[:-1] + link["href"].replace(mooc.instance_url,"") + "/index.html"

            wiki_data[url]["text"] = dl_dependencies(str(text),path,"",c)
            wiki_data[url]["title"] = soup.find("title").text
            wiki_data[url]["last-modif"] = soup.find("span", attrs={"class": "date"}).text
            wiki_data[url]["children"]=[]
        elif get_page_error:
            wiki_data[url]["text"] = """<div><h1 class="page-header">Permission Denied</h1><p class="alert denied">Sorry, you don't have permission to view this page.</p></div>""" 
            wiki_data[url]["title"] = "Permission Denied | Wiki" 
            wiki_data[url]["last-modif"] = "Unknow" 
            wiki_data[url]["children"]=[]

        #find new url of wiki in the list children page
        see_children=soup.find('div', attrs={"class": "see-children"})
        if see_children:
            allpage_url=str(see_children.find("a")["href"])
            wiki_data[url]["dir"] = allpage_url 
            content=c.get_page(mooc.instance_url + allpage_url)
            soup=BeautifulSoup.BeautifulSoup(content, 'lxml')
            table=soup.find("table")
            if table != None:
                for link in table.find_all("a"):
                    if link.has_attr("class") and "list-children" in link["class"]:
                        pass
                    else:
                        if link["href"] not in wiki_data and link["href"] not in page_to_visit:
                            page_to_visit.append(mooc.instance_url + link["href"])
                        wiki_data[url]["children"].append(mooc.instance_url + link["href"])
    return wiki_data, wiki_name, wiki_path

def render_wiki(mooc):
    wiki_data=mooc.wiki
    wiki_name=mooc.wiki_name
    for page in wiki_data:
        if "text" in wiki_data[page]: #this is a page
            jinja(
                os.path.join(wiki_data[page]["path"],"index.html"),
                "wiki_page.html",
                False,
                content=wiki_data[page],
                dir=wiki_data[page]["dir"].replace(mooc.instance_url + "/wiki/","") + "index.html",
                mooc=mooc,
                rooturl=wiki_data[page]["rooturl"]
            )
    
        make_dir(os.path.join(wiki_data[page]["path"],"_dir"))
        if len(wiki_data[page]["children"]) != 0: #this is a list page
            page_to_list=[]
            for child_page in wiki_data[page]["children"]:
                if "title" in wiki_data[child_page]:
                    page_to_list.append({ "url": wiki_data[page]["rooturl"]+ "/.." + child_page.replace(mooc.instance_url,""), "title": wiki_data[child_page]["title"], "last-modif": wiki_data[child_page]["last-modif"]})
            jinja(
                os.path.join(wiki_data[page]["path"],"_dir","index.html"),
                "wiki_list.html",
                False,
                pages=page_to_list,
                wiki_name=wiki_name,
                mooc=mooc,
                rooturl=wiki_data[page]["rooturl"] + "../"
            )
def booknav(mooc, book, output_path):
    pdf = book.find_all("a")
    book_list=[]
    for url in pdf:
        file_name=os.path.basename(urlparse(url["rel"][0]).path)
        download(url["rel"][0], os.path.join(output_path,file_name), mooc.instance_url)
        book_list.append({"url": file_name , "name": url.get_text()})
    return book_list

def render_booknav(mooc):
    for book_nav in mooc.book_list_list:
        jinja(
          os.path.join(book_nav["output_path"], "index.html"),
	  "booknav.html",
	  False,
	  book_list=book_nav["book_list"],
          dir_path=book_nav["dir_path"],
	  mooc=mooc,
	  rooturl="../../../"
        )

