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

    # url="https://ganhaim.localtimeline.com/index.php?lang=he#", level=0):
    def scan(self):
        site_name = self.get_site_name()
        self.downloader = open(f"/home/haim/download_{site_name}.bash", "w", encoding="utf-8")
        self.plan = open(f"/home/haim/{site_name}.txt", "w", encoding="utf-8")
        soup = self.get_soup(self.url)
        lst = soup.find_all(attrs={"class": "timeline-year"})
        x = len(lst)
        print(f"{x} years")
        n = 0
        lst.reverse()
        # lst = lst[:5] # Temporary!!!!!!!!!!!!!!!!!!!
        for div in lst:
            n += 1
            # print(f"div #{n}")
            inner = div.find("div", attrs={"class": "year-inner"})
            year_title = inner.find(self.is_title_item)
            span = year_title.find("span")
            year = span.string.strip()
            self.year = year
            self.plan.write(f"year={year}\n")
            self.plan.flush()
            print(year, end=" ")
            year_images = inner.find(
                "div", attrs={"class": "year-images bg-background-light"})
            links = year_images.find_all('a')
            for link in links:
                # self.curr_item = dict(year=year)
                href = link.attrs['href']
                self.scan_images(href)
                self.scan_iframes(href)
                self.scan_texts(href)
            year_events = inner.find(self.is_event_list)
            # print(f"year events: {year_events}")
            events = year_events.find_all("a")
            for event in events:
                self.scan_event(event)
        json_str = json.dumps(self.plan_list, ensure_ascii=False, indent=4)
        with open("/home/haim/plan.txt", "w", encoding="utf-8") as f:
            f.write(json_str)

    def scan_texts(self, href):
        soup = self.get_soup(href)
        texts = soup.find_all(attrs={"class": "textLayer"})
        # print("texts")

    def scan_event(self, event):
        href = event.attrs["href"]
        event_full_text_span = event.find(self.is_full_text)
        event_full_text = event_full_text_span.get_text().strip()
        # print(f"href: {href}")
        soup = self.get_soup(href)
        cat_names = self.get_categories(soup)
        event_name1 = soup.find("span", attrs={"class": "event-name-inner"})
        event_name_span = event_name1.find(
            "span", attrs={"class": "hidden-mobile"})
        event_name = event_name_span.get_text().strip()
        # print(f"event name: {event_name}")
        read_more_content = soup.find(
            "div", attrs={"class": "read-more-content-inner"})
        if read_more_content:
            read_more_text = (read_more_content.get_text().strip())
        else:
            read_more_text = None
        # print(f"read_more_text: {read_more_text}")
        credits_span = soup.find("span", attrs={"class": "credits-content"})
        if credits_span:
            credits = credits_span.get_text().strip()
        else:
            credits = None
        # print(f"credits: {credits}")
        event = dict(year=self.year,
                     kind="event",
                     event_name=event_name,
                     event_full_text=event_full_text,
                     read_more_text=read_more_text,
                     credits=credits,
                     items=[],
                     categories=cat_names
                     )
        self.plan_list.append(event)
        imgs = soup.find_all("img")
        num_images = len(imgs)
        for img in imgs:
            # print(img.attrs)
            if "data-src" not in img.attrs:
                continue
            src = img.attrs["data-src"]
            path = f"photos/oversize/uploads/{self.year}"
            photo_path = path + "/" + self.file_name_of_src(src)
            img_data = dict(
                year=self.year,
                kind="image", 
                src=src,
                photo_path=photo_path, 
                caption=img.attrs["alt"])
            event["items"].append(img_data)
            self.downloader.write(f"wget -P ./{path} {src}\n")
        iframes = soup.find_all("iframe")
        num_iframes = len(iframes)
        for ifr in iframes:
            if "data-src" not in ifr.attrs:
                continue
            src = ifr.attrs["data-src"]
            if "main-item--iframe-pdf" in ifr.attrs["class"]:
                kind = "pdf"
            elif "main-item--iframe-video" in ifr.attrs["class"]:
                kind = "video"
            else:
                print("unknown iframe type")
            ifr_data = dict(year=self.year,
                            kind=kind,
                            src=src)
            if kind == "pdf":
                path = f"uploads/{self.year}"
                doc_path = path + "/" + self.file_name_of_src(src)
                ifr_data["doc_path"] = doc_path
                self.downloader.write(f"wget -P ./docs/{path} {src}\n")
            # ifr_data.update(event_head)
            event["items"].append(ifr_data)
            # print(ifr.attrs)
        # sub_links = soup.find_all("a")
        # num_sublinks = len(sub_links)

    def scan_images(self, url):
        soup = self.get_soup(url)
        cat_names = self.get_categories(soup)
        if len(cat_names) > 0:
            print(f"cat_names in scan images: {cat_names}")
        main_image_items = soup.find_all(self.is_image_item)
        event_head = dict(year=self.year)
        for item in main_image_items:
            cat_names = self.get_categories(item)
            if len(cat_names) > 0:
                print(f"cat names: {cat_names}")
            images = item.find_all('img')
            for image in images:
                curr_image = dict(year=self.year, kind="image")
                # if 'image_placeholder' in src:
                #     continue
                image_src = image.attrs['data-src']
                image_caption = image.attrs["alt"]
                # print(image_src)
                # print(image_caption)
                curr_image["src"] = image_src
                self.downloader.write(f"wget -P ./photos/oversize/uploads/{self.year} {image_src}\n")
                curr_image["image_caption"] = image_caption
                curr_image.update(event_head)
                self.plan_list.append(curr_image)

            # ------------------------------------------
            iframes = item.find_all("iframe")
            num_iframes = len(iframes)
            if num_iframes:
                print(f"{num_iframes} iframes found in scan_images")
            for ifr in iframes:
                if "data-src" not in ifr.attrs:
                    continue
                src = ifr.attrs["data-src"]
                if "main-item--iframe-pdf" in ifr.attrs["class"]:
                    kind = "pdf"
                elif "main-item--iframe-video" in ifr.attrs["class"]:
                    kind = "video"
                else:
                    print("unknown iframe type")
                if kind == "pdf":
                    path = f"uploads/{self.year}"
                    doc_path = path + "/" + self.file_name_of_src(src)
                    self.downloader.write(f"wget -P ./docs/{path} {src}\n")
                    ifr_data = dict(kind=kind,
                                    doc_path=doc_path, 
                                    src=src)
                    ifr_data.update(event_head)
                    self.plan_list.append(ifr_data)
            categories_list = item.find("ul", attrs={"category-list"})

    def scan_iframes(self, url):
        soup = self.get_soup(url)
        iframes = soup.find_all("iframe")
        # print(f"{len(iframes)} iframes found")
        for iframe in iframes:
            curr_iframe = dict(year=self.year)
            if "class" in iframe.attrs:
                if "main-item--iframe-video" in iframe.attrs["class"]:
                    curr_iframe["kind"] = "video"
                    curr_iframe["src"] = iframe.attrs["data-src"]
                elif "main-item--iframe-pdf" in iframe.attrs["class"]:
                    curr_iframe["kind"] = "pdf"
                    curr_iframe["src"] = iframe.attrs["data-src"]
                else:
                    print("Unknown iframe kind")

            self.plan_list.append(curr_iframe)
            # print(f"iframe: {iframe.attrs}")

    def get_soup(self, url):
        response = urlopen(url)
        html = response.read()
        return BeautifulSoup(html, "lxml")

    # ------------selector functions-------------

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
        return cat_names


port_tl = PortTL(url="https://ganhaim.localtimeline.com/index.php?lang=he#")
t0 = datetime.datetime.now()
port_tl.scan()
t1 = datetime.datetime.now()
elapsed_time = t1 - t0
print(f"Elapsed time: {elapsed_time}")
