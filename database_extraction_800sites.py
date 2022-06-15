import pprint
import random
import sqlite3
import time

import requests

from bs4 import BeautifulSoup
from langdetect import detect
from multiprocessing import Process, Value, cpu_count, Queue, freeze_support, Lock, Manager, Pool, Value
from termcolor import colored


# Gets website text and checks if it is in the languages
def add_website(r, languages, url_buckets, lock, i, url):
    #print('Starting process')
    if r[2] in url:
        try:
            #print(f'trying {r[2]}')
            html = requests.request('GET', url, timeout=3).content
            html2 = html.decode("utf-8")
            soup = BeautifulSoup(html, features="lxml")
            iframes = soup.find_all("iframe")
            text = soup.getText()
            l = detect(soup.getText())
            # print(f"Site: {url}, language {l}")
            if l not in languages:
                print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}), language {l}")
            elif len(text) < 1000:
                print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}), short text")
            elif "iframe" in html2:
                print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}), iframe")
            elif 'onetrust' in html2:
                print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}), onetrust")
            elif iframes:
                print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}), soup iframes")
            elif "Access Denied" in text or "Website Blocked" in text or "Bot detection" in text:
                print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}), access denied")
            elif "_err" in text or "err_" in text:
                print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}), other error")
            else:
                url_buckets.append([str(r[0]), url])
                print(f"({i + 1}-{len(url_buckets)}) Adding {url} ({r[0]}), language {l}")
                with lock:
                    with open('800_sites_list_from_crawl.csv', '+a') as file:
                        file.write(str(r[0]) + ";" + url + '\n')
        except:
            print(f"({i + 1}-{len(url_buckets)}) Skipping {url} ({r[0]}) error")
    #print('Ending process')


if __name__ == '__main__':
    conn = sqlite3.connect('cookies.db')
    cursor = conn.cursor()

    buckets = [[1, 1000],
               [1001,10000],
               [10001,100000],
               [100001,1000000]]

    url_buckets = Manager().list([])
    lock = Lock()

    languages = ["en", "nl"]
    dutch = ["nl"]

    '''with open("800_sites_list_from_crawl.csv") as file:
        lines = file.read().splitlines()
    i = len(lines)'''

    '''for line in lines:
        url_buckets.append(line.split(";")[1])'''

    for index, bucket in enumerate(buckets):
        #url_buckets.append([])

        # Extract Dutch sites
        cursor.execute('SELECT E.site_nr, V.site_url, V.sitename FROM elements as E LEFT JOIN visits as V ON E.site_nr == V.site_nr and E.element_type = V.visit_type where E.visited == 1 and E.element_type = 0 and E.site_nr > ? and E.site_nr < ?'\
                       'and (not E.element_text = "" or E.element_css = "& No cookie dialog found during visit") and E.sitename like "%.nl" ORDER BY E.site_nr ASC', (bucket[0], bucket[1]))
        res = cursor.fetchall()
        res = list(res)

        print(f"Voor: {len(res)}")
        random.shuffle(res)

        i = 0
        while len(url_buckets) < (25 + 200*index) and i < len(res):
            r = res[i]
            if not r[1] is None:
                url = r[1][:r[1].find('/', 8)]
                #print('Starting process')
                p = Process(target=add_website, args=(r, dutch, url_buckets, lock, i, url))
                p.start()
                time.sleep(0.5)
                #add_website(r, dutch, url_buckets, lock, i, url)
            i += 1

        # Extract allowed language sites
        cursor.execute('SELECT E.site_nr, V.site_url, E.sitename FROM elements as E LEFT JOIN visits as V ON E.site_nr == V.site_nr and E.element_type = V.visit_type where E.visited == 1 and E.element_type = 0 and E.site_nr > ? and E.site_nr < ?'\
                       'and (not E.element_text = "" or E.element_css = "& No cookie dialog found during visit") and E.sitename like "%.com" ORDER BY E.site_nr ASC', (bucket[0], bucket[1]))
        res = cursor.fetchall()
        res = list(res)

        print(f"Voor: {len(res)}")
        random.shuffle(res)

        i = 0
        while len(url_buckets) < 200*(index+1) and i < len(res):
            r = res[i]
            if not r[1] is None:
                url = r[1][:r[1].find('/', 8)]
                #print('Starting process')
                p = Process(target=add_website, args=(r, languages, url_buckets, lock, i, url))
                p.start()
                time.sleep(0.5)
                #add_website(r, languages, url_buckets, lock, i, url)
            i += 1

    conn.close()

    #pprint.pprint(url_buckets)

    for url_bucket in url_buckets:
        for url in url_bucket:
            with open('800_sites_list_from_crawl_endresult.csv', '+a') as file:
                line = ";".join(url[:2])
                #print(line)
                file.write(line + '\n')
