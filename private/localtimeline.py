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
        if "img" in a.attrs:
            print("img found")


scan()