import pprint
import random
import sqlite3
import requests

from bs4 import BeautifulSoup
from bs4.element import Comment
from langdetect import detect

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

BASE_PATH = ""

conn = sqlite3.connect(BASE_PATH + 'cookies.db')
cursor = conn.cursor()

buckets = [[0, 25000],
           [25001,100000],
           [100001,250000],
           [250001,1000000]]

url_buckets = []
samples = []
i = 0
languages = ["en", "nl"]
dutch = ["nl"]

for index, bucket in enumerate(buckets):
    url_buckets.append([])

    # Extract allowed language sites
    cursor.execute('SELECT E.site_nr, V.site_url, E.sitename FROM elements as E LEFT JOIN visits as V ON E.site_nr == V.site_nr and E.element_type = V.visit_type where E.visited == 1 and E.element_type = 0 and E.site_nr > ? and E.site_nr < ?'\
                   'and (not E.element_text = "" or E.element_css = "& No cookie dialog found during visit") and E.sitename like "%.com" ORDER BY E.site_nr ASC', (bucket[0], bucket[1]))
    res = cursor.fetchall()
    res = list(res)

    print(f"Voor: {len(res)}")
    random.shuffle(res)
    i = 0
    while len(url_buckets[index]) <= 175:
        r = res[i]
        if not r[1] is None:
            url = r[1][:r[1].find('/', 8)]
            if r[2] in url:
                try:
                    html = requests.request('GET', url, timeout=3).content
                    soup = BeautifulSoup(html)
                    l = (detect(soup.getText()))
                    #print(f"Site: {url}, language {l}")
                    if l in languages:
                        url_buckets[index].append([str(r[0]), url])
                        print(f"({index+1}-{len(url_buckets[index])}) Adding {url} ({r[0]}), language {l}")
                        with open('800_sites_list_from_crawl.csv', '+a') as file:
                            file.write(str(r[0]) + ";" + url + '\n')
                except:
                    pass
        i += 1

    # Extract Dutch sites
    cursor.execute('SELECT E.site_nr, V.site_url, V.sitename FROM elements as E LEFT JOIN visits as V ON E.site_nr == V.site_nr and E.element_type = V.visit_type where E.visited == 1 and E.element_type = 0 and E.site_nr > ? and E.site_nr < ?'\
                   'and (not E.element_text = "" or E.element_css = "& No cookie dialog found during visit") and E.sitename like "%.nl" ORDER BY E.site_nr ASC', (bucket[0], bucket[1]))
    res = cursor.fetchall()
    res = list(res)

    print(f"Voor: {len(res)}")
    random.shuffle(res)
    i = 0
    while len(url_buckets[index]) <= 200:
        r = res[i]
        if not r[1] is None:
            url = r[1][:r[1].find('/', 8)]
            if r[2] in url:
                try:
                    html = requests.request('GET', url, timeout=3).content
                    soup = BeautifulSoup(html)
                    l = (detect(soup.getText()))
                    #print(f"Site: {url}, language {l}")
                    if l in languages:
                        url_buckets[index].append([str(r[0]), url])
                        print(f"({index+1}-{len(url_buckets[index])}) Adding {url} ({r[0]}), language {l}")
                        with open('800_sites_list_from_crawl.csv', '+a') as file:
                            file.write(str(r[0]) + ";" + url + '\n')
                except:
                    pass
        i += 1

conn.close()

#pprint.pprint(url_buckets)

for url_bucket in url_buckets:
    for url in url_bucket:
        with open('800_sites_list_from_crawl_endresult.csv', '+a') as file:
            line = ";".join(url[:2])
            #print(line)
            file.write(line + '\n')
