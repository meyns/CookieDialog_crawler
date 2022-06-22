# Load list of websites
# urls = []
import pprint
import random
import sqlite3

from sys import platform

# This file is used to populate the database for the big crawl, it includes the sites from the manual crawl

BASE_PATH = "d:/temp/Selenium-model/"
aerts_country_list = ['fr', 'ir', 'nl', 'co.uk', 'ch', 'lu', 'be', 'es', 'it', 'tr', 'se', 'pt', 'mt', 'fi', 'si', 'ro', 'de', 'lt', 'lv', 'gr', 'cz', 'hu', 'hr', 'sk', 'ee', 'no', 'bg', 'pl']

if platform == "linux" or platform == "linux2":
    BASE_PATH = "./data/" # Ubuntu
    buckets = [[0, 5000, 5000],
               [5000, 25000, 20000],
               [25000, 100000, 32500],
               [100000, 1000000, 32500]]
elif platform == "darwin":
    # OS X
    pass
elif platform == "win32":
    BASE_PATH = "d:/temp/Selenium-model/"
    buckets = [[0, 5000, 5000],
               [5000, 25000, 20000],
               [25000, 100000, 32500],
               [100000, 1000000, 32500]]
    buckets2 = [[0, 5000, 5000],
                [5000, 25000, 20000],
                [25000, 100000, 32500],
                [100000, 1000000, 32500]]


print('Getting manual list from Koen -> int(site_nr), url (zonder www.)')
filename = "domains_18-06-2022.csv"
urls_manual_crawl = [] # manual crawl url list
with open(BASE_PATH + filename) as file:
    lines = file.read()
    lines = lines.splitlines()

for line in lines:
    line = line.replace('"','').split(',')
    urls_manual_crawl.append([int(line[0]), line[1].replace('www.','')])
urls_manual_crawl.sort()


print("Getting 1m list -> site_nr, url")
with open('top-1m.csv') as file:
    lines = file.read()
    lines = lines.splitlines()
list_1m = []
for line in lines:
    line = line.split(',')
    list_1m.append([int(line[0]), line[1]])


print("Filling up final list of urls with manual crawl list and reducing the buckets and list_1m")
list_1m = dict(list_1m) # Omzetten in dictionary om gemakkelijk te filteren
final_urls = []
for url in urls_manual_crawl:
    #print(url[0])
    pos = list(list_1m).index(url[0])
    del list_1m[url[0]]
    final_urls.append([int(url[0]), url[1], 0])
    for k in range(len(buckets)):
        if pos > buckets[k][0] and pos <= buckets[k][1]:
            buckets[k][2] -= 1
        if pos <= buckets[k][1]:
            buckets[k][1] -= 1
        if pos <= buckets[k][0]:
            buckets[k][0] -= 1

print(buckets)
print(len(list_1m))

print("Current final_urls bucket counts:")
count_buckets = [0,0,0,0]
for url in final_urls:
    for i, bucket in enumerate(buckets2):
        if url[0] > bucket[0] and url[0] <= bucket[1]:
            count_buckets[i] += 1
print(count_buckets)

print("Getting first 500 urls from all European websites")
urls_top_500 = {}
for country in aerts_country_list:
    urls_top_500[country] = []

for site_nr, url in list_1m.items():
    for country in aerts_country_list:
        if len(urls_top_500[country]) < 500:
            if url.endswith("." + country):
                urls_top_500[country].append([site_nr, url])

'''for country, urls in urls_top_500.items():
    print(f"{country} {len(urls)}")'''


print("Filling up final list of urls with top 500 list and reducing the buckets and list_1m")
for country, sites_from_country in urls_top_500.items():
    for url in sites_from_country:
        #print(url[0])
        try:
            pos = list(list_1m).index(url[0])
            del list_1m[int(url[0])]
            final_urls.append([int(url[0]), url[1], 0])
            for k in range(len(buckets)):
                if pos > buckets[k][0] and pos <= buckets[k][1]:
                    buckets[k][2] -= 1
                if pos <= buckets[k][1]:
                    buckets[k][1] -= 1
                if pos <= buckets[k][0]:
                    buckets[k][0] -= 1
        except:
            print(f"Skipping url because already filtered by manual list: {url[0]}-{url[1]}")


print(buckets)
print(len(list_1m))

print("Current final_urls bucket counts:")
count_buckets = [0,0,0,0]
for url in final_urls:
    for i, bucket in enumerate(buckets2):
        if url[0] > bucket[0] and url[0] <= bucket[1]:
            count_buckets[i] += 1
print(count_buckets)

print("Filling final list with extra sites to fill bucket")
list_1m = list(list_1m.items())
for k in range(4):
    print(buckets[k])
    if buckets[k][2] == (buckets[k][1] - buckets[k][0]):
        for line in list_1m[buckets[k][0]:buckets[k][1]]:
            final_urls.append([line[0], line[1], 0])
        #print(urls)
    else:
        sample = random.sample(range(buckets[k][0], buckets[k][1]), buckets[k][2])
        sample.sort()
        print(len(sample))
        for s in sample:
            #print(s)
            final_urls.append([list_1m[s][0], list_1m[s][1], 0])
    #print(len(final_urls))


print(len(final_urls))

print(buckets)
print(len(list_1m))

#print(list_1m[:20])
#print(lfinal_urls[:20])

#print(final_urls)

print("Current final_urls bucket counts:")
count_buckets = [0,0,0,0]
for url in final_urls:
    for i, bucket in enumerate(buckets2):
        if url[0] > bucket[0] and url[0] <= bucket[1]:
            count_buckets[i] += 1
print(count_buckets)


#input('-----------------')

# Populating database
print('setting up database')
conn = sqlite3.connect(BASE_PATH + 'cookies.db')
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE if not exists visits (visit_id bigint, site_nr int, sitename varchar(255), visit_type int, site_url varchar(255), cookie_numbers int)")
cursor.execute(
    "CREATE TABLE if not exists cookies (visit_id bigint, before_after varchar(24), short_url varchar(255), domain varchar(255), expires float(24), httpOnly bool, name varchar(255), path varchar(255), priority varchar(24), sameParty bool, sameSite varchar(25), secure bool, session bool, size int, sourcePort int, sourceScheme varchar(255), value varchar(255))")
cursor.execute(
    "CREATE TABLE if not exists elements (visit_id bigint, site_nr int, sitename varchar(255), element_type tinyint, visited tinyint, result varchar(255), element_text varchar(255), element_css varchar(255), iframe_css varchar(255), location_x int, location_y int, text_color varchar(255), background_color varchar(255), width varchar(24), height varchar(24), font_size varchar(24), PRIMARY KEY (site_nr, element_type))")
cursor.execute(
    "CREATE TABLE if not exists redirects (visit_id bigint, status_code int, date varchar(32), url_from varchar(1024), url_to varchar(1024), content_type varchar(264))")
cursor.execute(
    "CREATE TABLE if not exists all_requests (visit_id bigint, status_code int, date varchar(32), url_from varchar(1024), url_to varchar(1024), content_type varchar(264))")
# Fill in all rows of to be visited websites if they do not exist
for url in final_urls:
    #print(url)
    # cursor.execute("INSERT OR IGNORE INTO cookie_numbers VALUES (?,?,?,?,?,?,?,?,?)", (url[0], url[1], None, None, None, None, None, None, None))
    #cursor.execute("INSERT OR IGNORE INTO cookie_numbers (site_nr, sitename) VALUES (?,?)",
    #               (url[0], url[1]))
    cursor.execute("INSERT OR IGNORE INTO elements (site_nr, sitename, element_type, visited) VALUES (?,?,?,?)",
                   (url[0], url[1], 0, 0))
cursor.execute('commit')
cursor.close()
conn.close()
