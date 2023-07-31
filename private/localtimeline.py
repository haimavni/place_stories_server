from bs4 import BeautifulSoup
from urllib.request import urlopen
class PortTL():

    def __init__(self, url):
        self.url = url


    def scan(self): #url="https://ganhaim.localtimeline.com/index.php?lang=he#", level=0):
        site_name = self.get_site_name()
        self.plan = open(f"/home/haim/{site_name}.txt", "w", encoding="utf-8")
        soup = self.get_soup(self.url)
        lst = soup.find_all(attrs={"class":"timeline-year"})
        x = len(lst)
        print(f"{x} divs")
        n = 0
        for div in lst:
            n += 1
            print(f"div #{n}")
            inner = div.find("div", attrs={"class":"year-inner"})
            year_title = inner.find(self.title_item)
            span = year_title.find("span")
            year = span.string.strip()
            self.plan.write(f"year={year}\n")
            self.plan.flush()
            print(year)
            year_images = inner.find("div", attrs={"class":"year-images bg-background-light"})
            links = year_images.find_all('a')
            for link in links:
                href = link.attrs['href']
                self.scan_images(href)
                self.scan_iframes(href)
            year_events = inner.find(self.detect_event)
            print(f"year events: {year_events}")
            links = year_events.find_all("a")
            for link in links:
                href = link.attrs["href"]
                link_full_text_span = link.find(self.is_full_text)
                link_full_text = link_full_text_span.get_text().strip()
                # print(f"href: {href}")
                soup = self.get_soup(href)
                event_name1 = soup.find("span", attrs={"class":"event-name-inner"})
                event_name_span = event_name1.find("span", attrs={"class":"hidden-mobile"})
                event_name = event_name_span.get_text().strip()
                print(f"event name: {event_name}")
                read_more_content = soup.find("div", attrs={"class":"read-more-content-inner"})
                if read_more_content:
                    read_more_text = (read_more_content.get_text().strip())
                else:
                    read_more_text = None 
                print(f"read_more_text: {read_more_text}")
                credits_span = soup.find("span", attrs={"class":"credits-content"})
                credits = credits_span.get_text().strip()
                print(f"credits: {credits}")

    def is_full_text(self, tag):
        if tag.name != "span":
            return False
        if "class" not in tag.attrs:
            return False
        if "event-link-text-full" in tag.attrs["class"]:
            return True
        return False

    def title_item(self, tag):
        if "year-title" in tag.attrs["class"]:
            return True;
        return False

    def detect_event(self, tag):
        if tag.name != "div":
            return False
        if not tag.has_attr("class"):
            return False
        if "year-event-list" in tag.attrs["class"]:
            return True
        return False

    def scan_images(self, url):
        soup = self.get_soup(url)
        main_image_items = soup.find_all(self.main_image_item)
        for item in main_image_items:
            images = item.find_all('img')
            for image in images:
                # if 'image_placeholder' in src:
                #     continue
                image_src = image.attrs['data-src']
                image_caption = image.attrs["alt"]
                print(image_src)
                print(image_caption)

    def scan_iframes(self, url):
        soup = self.get_soup(url)
        iframes = soup.find_all("iframe")
        print(f"{len(iframes)} iframes found")
        for iframe in iframes:
            print(f"iframe: {iframe.attrs}")

    def get_soup(self, url):
        response = urlopen(url)
        html = response.read()
        return BeautifulSoup(html, "lxml")

    def main_image_item(self, tag):
        if tag.name != 'div':
            return False
        if not tag.has_attr("class"):
            return False
        if (not tag.has_attr('data-type')) or tag.attrs['data-type'] != 'image':
            return False
        class_list = tag.attrs["class"]
        if "main-item-wrapper" in class_list: # and "active" in class_list:
            return True
        return False
    
    def get_site_name(self):
        r1 = self.url.find("//") + 2
        r2 = self.url.find(".")
        return self.url[r1:r2]

port_tl = PortTL(url="https://ganhaim.localtimeline.com/index.php?lang=he#")
port_tl.scan()