from bs4 import BeautifulSoup
from urllib.request import urlopen
import json
import datetime


class PortTL():

    def __init__(self, url):
        self.url = url
        self.plan_list = []
        self.curr_item = None
        self.year = None
        self.categories = dict()
        self.urls = set()

    def scan(self):
        self.site_name = self.get_site_name()
        self.downloader = open(f"/home/haim/migrations/{self.site_name}/downloader.bash", "w", encoding="utf-8")
        soup = self.get_soup(self.url)
        lst = soup.find_all(attrs={"class": "timeline-year"})
        x = len(lst)
        print(f"{x} years")
        n = 0
        # lst.reverse()
        # lst = lst[:5] # Temporary!!!!!!!!!!!!!!!!!!!
        for div in lst:
            n += 1
            inner = div.find("div", attrs={"class": "year-inner"})
            year_title = inner.find(self.is_title_item)
            span = year_title.find("span")
            year = span.string.strip()
            self.year = year
            print(year, end=" ")
            # year_events = inner.find(self.is_event_list)
            # -----------------------
            year_images = inner.find("div", class_="year-images")
            links = year_images.find_all('a')
            for link in links:
                href = link.attrs['href']
                self.scan_link(href) # will replace the code below

            year_events = inner.find("div", class_="year-event-list")
            # -----------------------
            events = year_events.find_all("a")
            for event in events:
                self.scan_event(event)
            # -----------------------
        json_str = json.dumps(self.plan_list, ensure_ascii=False, indent=4)
        with open(f"/home/haim/migrations/{self.site_name}/plan.txt", "w", encoding="utf-8") as f:
            f.write(json_str)
        json_str = json.dumps(self.categories, ensure_ascii=False, indent=4)
        with open(f"/home/haim/migrations/{self.site_name}/all_categories.txt", "w", encoding="utf-8") as f:
            f.write(json_str)
        print("\nDone")

    def scan_link(self, href):
        soup = self.get_soup(href)
        gallery = soup.find("div", class_="gallery-main")
        comments = self.get_comments(soup)
        event_name_span = soup.find("span", class_="event-name-inner")
        span = event_name_span.find("span", class_="hidden-mobile")
        event_name = span.get_text()
        read_more_div = gallery.find("div", "read-more-content_inner")
        if read_more_div:
            read_more_text = read_more_div.get_text()
        else:
            read_more_text = ""
        cat_names = self.get_categories(soup)
        credits = self.get_link_credits(soup)
        titles_dic = self.get_link_titles(soup)
        event = dict(year=self.year,
                     kind="ievent",
                     event_name=event_name,
                     read_more_text=read_more_text,
                     items=[],
                     categories=cat_names
                     )
        item_divs = gallery.find_all("div", "main-item-wrapper")
        for item_div in item_divs:
            data_type = item_div.attrs["data-type"]
            data_id = item_div.attrs["data-id"]
            item_credit = credits.get(data_id, None)
            item_title = titles_dic.get(data_id, None)
            item_rec = dict(year=self.year,
                            credit=item_credit,
                            categories=cat_names,
                            title=item_title,
                            data_type=data_type)
            if data_type == "pdf":
                iframe = item_div.find("iframe")
                src = iframe.attrs["data-src"]
                src = self.normalize_pdf_url(src)
            elif data_type == "image":
                img = item_div.find("img")
                src = img.attrs["data-src"]
                caption = img.attrs.get("alt", "")
                item_rec["caption"] = caption
            elif data_type == "video":
                iframe = item_div.find("iframe")
                src = iframe.attrs["data-src"]
            else:
                print(f"Unexpected data type {data_type}")
            if src in self.urls:
                item_rec["duplicate"] = True
            else:
                item_rec["duplicate"] = False
                if data_type == "pdf":
                    path = f"ported/{self.year}"
                    doc_path = path + "/" + self.file_name_of_src(src)
                    item_rec["doc_path"] = doc_path
                    path = "docs/" + path
                    self.downloader.write(f"wget -P ./{path} {src}\n")
                elif data_type == "image":
                    path = f"ported/{self.year}"
                    photo_path = path + "/" + self.file_name_of_src(src)
                    item_rec["photo_path"] = photo_path
                    path = "photos/oversize/" + path
                    self.downloader.write(f"wget -P ./{path} {src}\n")
                self.urls.add(src)
                item_comments = comments.get(data_id, [])
                item_rec["comments"] = item_comments
                event["items"].append(item_rec)
        self.plan_list.append(event)

    def get_link_credits(self, soup):
        result = dict()
        credit_arr = soup.find_all("div", class_="main-image-credits-wrapper nice-scroll-bar hidden-by-default")
        for credit_rec in credit_arr:
            data_id = credit_rec.attrs["data-id"]
            span = credit_rec.find("span", class_="credits-content")
            name = span.get_text().strip()
            result[data_id] = name
        return result
    
    def get_link_titles(self, soup):
        result = dict()
        title_arr = soup.find_all("span", class_="main-title-text")
        for title_rec in title_arr:
            data_id = title_rec.attrs["data-id"]
            result[data_id] = title_rec.get_text().strip()
        return result

    def scan_event(self, event):
        href = event.attrs["href"]
        event_full_text_span = event.find(self.is_full_text)
        event_full_text = event_full_text_span.get_text().strip()
        soup = self.get_soup(href)
        cat_names = self.get_categories(soup)
        event_name1 = soup.find("span", attrs={"class": "event-name-inner"})
        event_name_span = event_name1.find(
            "span", attrs={"class": "hidden-mobile"})
        event_name = event_name_span.get_text().strip()
        read_more_content = soup.find(
            "div", attrs={"class": "read-more-content-inner"})
        if read_more_content:
            read_more_text = (read_more_content.get_text().strip())
        else:
            read_more_text = None
        comments = self.get_comments(soup)
        event = dict(year=self.year,
                     kind="event",
                     event_name=event_name,
                     event_full_text=event_full_text,
                     read_more_text=read_more_text,
                     items=[],
                     categories=cat_names
                     )
        main_items = soup.find_all(self.is_main_item_wrapper)
        credits_dic = self.get_link_credits(soup)
        titles_dic = self.get_link_titles(soup)

        for item in main_items:
            data_type = item.attrs.get("data-type", "unknown")
            data_id = item.attrs["data-id"]
            if data_type == "pdf":
                item_data = self.handle_pdf(item)
            elif data_type == "video":
                item_data = self.handle_video(item)
            elif data_type == "image":
                item_data = self.handle_image(item)
            else:
                print(f"Unknown data type {data_type}")
                continue
            if item_data and item_data != "duplicate":
                credits = credits_dic.get(data_id, None)
                item_data["credits"] = credits
                item_data["comments"] = self.get_item_comments(comments, data_id)
                item_data["title"] = titles_dic.get(data_id, None)
                event["items"].append(item_data)
        if len(event["items"]) > 0:
            self.plan_list.append(event)

    def handle_pdf(self, item):
        iframe = item.find("iframe")
        if "data-src" not in iframe.attrs:
            return None
        src = iframe.attrs["data-src"]
        if src in self.urls:
            # print("duplicate iframe")
            return "duplicate"
        self.urls.add(src)
        if "main-item--iframe-pdf" not in iframe.attrs["class"]:
            print("---------------not pdf???---------------")
        src = self.normalize_pdf_url(src)
        ifr_data = dict(year=self.year,
                        kind="pdf",
                        src=src)
        path = f"ported/{self.year}"
        doc_path = path + "/" + self.file_name_of_src(src)
        ifr_data["doc_path"] = doc_path
        self.downloader.write(f"wget -P ./docs/{path} {src}\n")
        return ifr_data

    def handle_video(self, item):
        iframe = item.find("iframe")
        if "data-src" not in iframe.attrs:
            return None
        src = iframe.attrs["data-src"]
        if src in self.urls:
            # print("duplicate iframe")
            return "duplicate"
        self.urls.add(src)
        if "main-item--iframe-video" not in iframe.attrs["class"]:
            print("---------------not video???---------------")
        ifr_data = dict(year=self.year,
                        kind="video",
                        src=src)
        return ifr_data

    def handle_image(self, item):
        # print("handle image")            
        img = item.find("img")
        if (not img) or "data-src" not in img.attrs:
            return None
        src = img.attrs["data-src"]
        if src in self.urls:
            return "duplicate"
        self.urls.add(src)
        path = f"ported/{self.year}"
        photo_path = path + "/" + self.file_name_of_src(src)
        data_id = item.attrs["data-id"]
        img_data = dict(
            year=self.year,
            kind="image", 
            src=src,
            photo_path=photo_path, 
            data_id=data_id,
            caption=img.attrs["alt"])
        path = "photos/oversize/" + path
        self.downloader.write(f"wget -P ./{path} {src}\n")
        return img_data
    
    def get_item_comments(self, comments, data_id):
        # print("get item comments")
        return comments.get(data_id, None)   

    def get_soup(self, url):
        response = urlopen(url)
        html = response.read()
        return BeautifulSoup(html, "lxml")
    
    def normalize_pdf_url(self, src):
        if "%3A" not in src:
            return src
        r = src.rfind("https%3A")
        s = src[r:]
        s = s.replace("%3A", ":").replace("%2F", "/")
        return s
    
    def get_comments(self, soup):
        comments = soup.find("div", class_="comment-list")
        result = None
        if comments:
            result = dict()
            comment_list = comments.find_all("div", class_="comment-container")
            for comment in comment_list:
                data_for = comment.attrs["data-for"]
                if data_for not in result:
                    result[data_for] = []
                comment = dict(
                    commenter_name = comment.find("div", class_="commenter-name").get_text().strip(),
                    comment_content = comment.find("div", "comment-content-full").get_text().strip()
                )
                result[data_for].append(comment)
        return result


    # ------------selector functions-------------

    def is_comment_container(self, tag):
        if tag.name != "div":
            return False
        if "class" not in tag.attrs:
            return False
        if "comment_container" in tag.attrs["class"]:
            return True
        return False


    def is_main_item_wrapper(self, tag):
        if tag.name != "div":
            return False
        if "class" not in tag.attrs:
            return False
        if "main-item-wrapper" in tag.attrs["class"]:
            return True
        return False


    def is_full_text(self, tag):
        if tag.name != "span":
            return False
        if "class" not in tag.attrs:
            return False
        if "event-link-text-full" in tag.attrs["class"]:
            return True
        return False

    def is_title_item(self, tag):
        if "year-title" in tag.attrs["class"]:
            return True
        return False

    def is_event_list(self, tag):
        if tag.name != "div":
            return False
        if not tag.has_attr("class"):
            return False
        if "year-event-list" in tag.attrs["class"]:
            return True
        return False

    def is_image_item(self, tag):
        if tag.name != 'div':
            return False
        if not tag.has_attr("class"):
            return False
        if (not tag.has_attr('data-type')) or tag.attrs['data-type'] != 'image':
            return False
        class_list = tag.attrs["class"]
        if "main-item-wrapper" in class_list:  # and "active" in class_list:
            return True
        return False

    def get_site_name(self):
        r1 = self.url.find("//") + 2
        r2 = self.url.find(".")
        return self.url[r1:r2]
    
    def file_name_of_src(self, src):
        r = src.rfind("/")
        return src[r+1:]
    
    def get_categories(self, soup):
        categories = soup.find("ul", attrs={"class":"category-list"})
        # cat_names = []
        if not categories:
            return []
        cat_list = categories.find_all("li")
        cat_names = [c.get_text() for c in cat_list]
        for cn in cat_names:
            if cn not in self.categories:
                self.categories[cn] = 0
            self.categories[cn] += 1
        return cat_names


port_tl = PortTL(url="https://ganhaim.localtimeline.com/index.php?lang=he#")
t0 = datetime.datetime.now()
port_tl.scan()
t1 = datetime.datetime.now()
elapsed_time = t1 - t0
print(f"Elapsed time: {elapsed_time}")
