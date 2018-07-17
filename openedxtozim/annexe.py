class Annexe:
    self.has_wiki=False
    self.has_forum=False



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

