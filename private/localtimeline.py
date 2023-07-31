from bs4 import BeautifulSoup
from urllib.request import urlopen

def scan(url="https://ganhaim.localtimeline.com/index.php?lang=he#", level=0):
    response = urlopen(url)
    html = response.read()

    soup = BeautifulSoup(html, "lxml")

    all_as = soup.find_all(["a","img"])

    print(f"number of as: {len(all_as)}")

    cnt = 0
    for a in all_as:
        if level == 0:
            if 'class' not in a.attrs:
                continue
            if a.attrs['class'] != ['year-info-event-link']:
                continue
        cnt += 1
        print(f"-----------{level}:{cnt}---------")
        if "href" in a.attrs:
            href = a.attrs['href']
            if "localtimeline" in href:
                scan(href, level + 1)
        if a.name == 'img':
            print(f"img found: {a}")

def scan1(url="https://ganhaim.localtimeline.com/index.php?lang=he#", level=0):
    soup = get_soup(url)
    # response = urlopen(url)
    # html = response.read()

    # soup = BeautifulSoup(html, "lxml")

    lst = soup.find_all(attrs={"class":"timeline-year"})
    x = len(lst)
    print(f"{x} divs")
    n = 0
    for div in lst:
        n += 1
        print(f"div #{n}")
        inner = div.find("div", attrs={"class":"year-inner"})
        year_title = inner.find(title_item)
        span = year_title.find("span")
        year = span.string.strip()
        print(year)
        year_images = inner.find("div", attrs={"class":"year-images bg-background-light"})
        links = year_images.find_all('a')
        for link in links:
            href = link.attrs['href']
            scan_images(href)
            scan_iframes(href)
        year_events = inner.find(detect_event)
        print(f"year events: {year_events}")
        links = year_events.find_all("a")
        for link in links:
            href = link.attrs["href"]
            link_full_text_span = link.find(is_full_text)
            link_full_text = link_full_text_span.get_text().strip()
            # print(f"href: {href}")
            soup = get_soup(href)
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

def is_full_text(tag):
    if tag.name != "span":
        return False
    if "class" not in tag.attrs:
        return False
    if "event-link-text-full" in tag.attrs["class"]:
        return True
    return False

def title_item(tag):
    if "year-title" in tag.attrs["class"]:
        return True;
    return False

def detect_event(tag):
    if tag.name != "div":
        return False
    if not tag.has_attr("class"):
        return False
    if "year-event-list" in tag.attrs["class"]:
        return True
    return False

def scan_images(url):
    soup = get_soup(url)
    main_image_items = soup.find_all(main_image_item)
    for item in main_image_items:
        images = item.find_all('img')
        for image in images:
            # if 'image_placeholder' in src:
            #     continue
            image_src = image.attrs['data-src']
            image_caption = image.attrs["alt"]
            print(image_src)
            print(image_caption)

def scan_iframes(url):
    soup = get_soup(url)
    iframes = soup.find_all("iframe")
    print(f"{len(iframes)} iframes found")
    for iframe in iframes:
        print(f"iframe: {iframe.attrs}")

def get_soup(url):
    response = urlopen(url)
    html = response.read()
    return BeautifulSoup(html, "lxml")

def main_image_item(tag):
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

scan1()