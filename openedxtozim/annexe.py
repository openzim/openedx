from urllib.parse import urlparse
import bs4 as BeautifulSoup
import os
from uuid import uuid4
import json
from collections import defaultdict
from openedxtozim.utils import make_dir, download, dl_dependencies, jinja, markdown

def forum(c,mooc):
    forum_output=os.path.join(mooc.output_path, "forum")
    make_dir(forum_output)
    content=c.get_page(mooc.instance_url + "/courses/" +  mooc.course_id + "/discussion/forum")
    good_content=BeautifulSoup.BeautifulSoup(content, 'html.parser').find("script", attrs={"id": "thread-list-template"})
    category={}
    if good_content:
        soup=BeautifulSoup.BeautifulSoup(good_content.text, 'html.parser')
        all_category=soup.find_all('li', attrs={"class": "forum-nav-browse-menu-item"})
        if len(all_category) == 0:
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            all_category=soup.find_all('li', attrs={"class": "forum-nav-browse-menu-item"})
        see=[]
        for cat in all_category:
            if not cat.has_attr("data-discussion-id") and cat.find("a") != None:
                random_id=str(uuid4())
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
    else:
        print("not find")
#https://courses.edraak.org/courses/course-v1:Edraak+IoT+2018_T1/discussion/forum/search?ajax=1&page=1&commentable_ids=3be3558ae81f49e0d89898b99712a33c1247fcd2&sort_key=date&sort_order=desc
#https://courses.edx.org/courses/course-v1:Microsoft+DEV274x+1T2018a/discussion/forum/course/inline?ajax=1&page=1&commentable_ids=course&sort_key=activity&sort_order=desc
    threads=[]
    """
    for x in category:
        url="/courses/" + mooc.course_id + "/discussion/forum/" + x + "/inline?ajax=1&page=1&sort_key=activity&sort_order=desc"
        #url="/courses/" + mooc.course_id + "/discussion/forum/search?ajax=1&page=1&commentable_ids=" + x + "&sort_key=activity&sort_order=desc"
        #url="/courses/" + "course-v1:Microsoft+DEV274x+1T2018a" + "/discussion/forum/inline/?ajax=1&page=1&sort_key=activity&sort_order=desc"
        data=c.get_api_json(url)
        threads=data["discussion_data"]
        for i in range(1,data["num_pages"]):
            url="/courses/" + mooc.course_id + "/discussion/forum/" + x + "/inline?ajax=1&page=" + str(i+1) + "&sort_key=activity&sort_order=desc"
            #url="/courses/" + mooc.course_id + "/discussion/forum/search?ajax=1&page=" + str(i+1) + "&commentable_ids=" + x + "&sort_key=activity&sort_order=desc"
            data=c.get_api_json(url)
            threads+=data["discussion_data"]

    print(threads)
    """

    threads= [ {"id": "5ac1976624451a09c7003386", "commentable_id": "course" }]
    for thread in threads:
        print("We try :"+ thread["id"])
        url = "/courses/" + mooc.course_id + "/discussion/forum/" + thread["commentable_id"] + "/threads/" + thread["id"] + "?ajax=1&resp_skip=0&resp_limit=25" #TODO limit here
        url = "/courses/course-v1:Microsoft+DEV274x+1T2018a/discussion/forum/course/threads/5ac1976624451a09c7003386?ajax=1&resp_skip=0&resp_limit=25"
        url = "/courses/" + mooc.course_id + "/discussion/forum/" + thread["id"] + "/inline?ajax=1&resp_skip=0&resp_limit=25"
        make_dir(os.path.join(forum_output,thread["commentable_id"]))
        try:
            thread["data_thread"]=c.get_api_json(url)
        except: #TODO better
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

    with open('data_forum_bis.json', 'w') as outfile:
        json.dump(threads, outfile)
    """
    f=open('data_forum.json', 'r')
    threads=json.loads(f.read())
    """
    #    headers["X-Requested-With"] = ""

    return threads, category

def render_forum(mooc):
    threads=mooc.forum_thread
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
            mooc=mooc,
            rooturl="../"
    )
    for thread in threads:
        """
        #TODO update and remove done plus haut
        make_dir(os.path.join(forum_output,thread["id"])) #if not done ?
        if ("endorsed_responses" in thread["data_thread"]["content"] or "non_endorsed_responses" in thread["data_thread"]["content"]) and "children" in thread["data_thread"]["content"]:
            logging.warning("pb endorsed VS children" + thread["id"])
        if "children" not in thread["data_thread"]["content"]:
            thread["data_thread"]["content"]["children"] = []
        if "endorsed_responses" in thread["data_thread"]["content"]:
            thread["data_thread"]["content"]["children"] += thread["data_thread"]["content"]["endorsed_responses"]
        if "non_endorsed_responses" in thread["data_thread"]["content"]:
            thread["data_thread"]["content"]["children"] += thread["data_thread"]["content"]["non_endorsed_responses"]
        #Fin todo remove
        thread["data_thread"]["content"]["body"] = dl_dependencies(markdown(thread["data_thread"]["content"]["body"]),os.path.join(forum_output,thread["id"]),"",c)
        for children in thread["data_thread"]["content"]["children"]:
            children["body"]=dl_dependencies(markdown(children["body"]),os.path.join(forum_output,thread["id"]),"",c)

            if "children" in children:
                for children_children in children["children"]:
                    children_children["body"]=dl_dependencies(markdown(children_children["body"]),os.path.join(forum_output,thread["id"]),"",c)


        #Fin update
        """
        jinja(
                os.path.join(forum_output,thread["id"],"index.html"),
                "forum.html",
                False,
                thread=thread["data_thread"]["content"],
                category=category,
                thread_by_category=thread_by_category,
                mooc=mooc,
                rooturl="../../../"
        )





def wiki(c,mooc):
    #Get redirection to wiki
    first_page=c.get_redirection(self.mooc.instance_url + "/courses/" +  mooc.course_id + "/course_wiki")
    page_to_visit=[first_page]
    wiki_data={} #Data from page already visit
    # "[url]" : { "rooturl": , "path": , "text": , "title": , "dir" : , "children": [] }
    #Extract wiki name
    wiki_name = first_page.replace(self.mooc.instance_url + "/wiki/", "")[:-1]

    while page_to_visit:
        url = page_to_visit.pop()
        try:
            content=c.get_page(url)
        except HTTPError as e:
            if e.code == 404 or e.code == 403:
                pass

        wiki_data[url]={}
        web_path=os.path.join("wiki", url.replace(self.mooc.instance_url + "/wiki/",""))
        path=os.path.join(mooc.output_path, web_path)
        make_dir(path)
        wiki_data[url]["path"] = path
        rooturl="../"
        for x in range(0,len(web_path.split("/"))):
            rooturl+="../"
        wiki_data[url]["rooturl"]= rooturl


        #Parse content page
        soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
        text=soup.find("div", attrs={"class": "wiki-article"})
        if text != None : #If it's a page (and not a list of page)
            #Find new wiki page in page content
            for link in text.find_all("a"):
                if link.has_attr("href") and "/wiki/" in link["href"]:
                    if link not in wiki_data and link not in page_to_visit:
                        if not link["href"][0:4] == "http":
                            page_to_visit.append(self.mooc.instance_url + link["href"])
                        else:
                            page_to_visit.append(link["href"])

                    if not link["href"][0:4] == "http": #Update path in wiki page
                        link["href"] = rooturl[:-1] + link["href"].replace(self.mooc.instance_url,"") + "/index.html"

            wiki_data[url]["text"] = dl_dependencies(str(text),path,"",c)
            wiki_data[url]["title"] = soup.find("title").text
            wiki_data[url]["last-modif"] = soup.find("span", attrs={"class": "date"}).text
            wiki_data[url]["children"]=[]

        #find new url of wiki in the list children page
        see_children=soup.find('div', attrs={"class": "see-children"})
        if see_children:
            allpage_url=str(see_children.find("a")["href"])
            wiki_data[url]["dir"] = allpage_url 
            content=c.get_page(self.mooc.instance_url + allpage_url)
            soup=BeautifulSoup.BeautifulSoup(content, 'html.parser')
            table=soup.find("table")
            if table != None:
                for link in table.find_all("a"):
                    if link.has_attr("class") and "list-children" in link["class"]:
                        pass
                    else:
                        if link["href"] not in wiki_data and link["href"] not in page_to_visit:
                            page_to_visit.append(self.mooc.instance_url + link["href"])
                        wiki_data[url]["children"].append(self.mooc.instance_url + link["href"])
    return wiki_data, wiki_name

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
def booknav(mooc, book, url, output_path):
    #IMPROUVEMENT pdf viewer
    pdf = book.find_all("a")
    html_content='<ul id="booknav">'
    for url in pdf:
        file_name=os.path.basename(urlparse(url["rel"][0]).path)
        download(url["rel"][0], os.path.join(output_path,file_name), mooc.instance_url)
        html_content+='<li><a href="{}" > {} </a></li>'.format(file_name,url.get_text())
    html_content+='</ul>'
    return html_content

