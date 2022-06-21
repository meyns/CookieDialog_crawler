# Load list of websites
# urls = []
import pprint
import random
import sqlite3

from sys import platform

# This file is used to populate the database for the big crawl, it includes the sites from the manual crawl

BASE_PATH = "d:/temp/Selenium-model/"

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

filename = "total_800_17-06-2022 adjusted.csv"

urls = [] # manual crawl url list
with open(BASE_PATH + filename) as file:
    lines = file.read()
    lines = lines.splitlines()
#urls.append([])
for line in lines:
    line = line.replace('"','').split(',')
    urls.append([int(line[0]), line[1]])
urls.sort()

#pprint.pprint(urls)

print('Populating databases')

with open('top-1m.csv') as file:
    lines = file.read()
    lines = lines.splitlines()
list_1m = []
for line in lines:
    line = line.split(',')
    list_1m.append([int(line[0]), line[1]])

list_1m = dict(list_1m)
#print(list_1m)

final_urls = []
for i, url in enumerate(urls):
    print(url[0])
    del list_1m[int(url[0])]
    final_urls.append([int(url[0]), url[1].replace('www.',''), 0])
    for k in range(len(buckets)):
        if int(url[0]) > buckets[k][0] and int(url[0]) <= buckets[k][1]:
            buckets[k][2] -= 1
        if int(url[0]) <= buckets[k][1]:
            buckets[k][1] -= 1
        if int(url[0]) <= buckets[k][0]:
            buckets[k][0] -= 1

print(buckets)
print(len(list_1m))
#print(list_1m[:20])
#print(final_urls[:20])
#input('-------------')
list_1m = list(list_1m.items())
print(list_1m[:20])

for k in range(4):
    print(buckets[k])
    if buckets[k][2] == (buckets[k][1] - buckets[k][0]):
        for line in list_1m[buckets[k][0]:buckets[k][1]]:
            final_urls.append([line[0], line[1], 0])
        #print(urls)
    else:
        sample = random.sample(range(buckets[k][0], buckets[k][1]), buckets[k][2])
        sample.sort()
        #print(sample)
        for s in sample:
            #print(s)
            final_urls.append([list_1m[s][0], list_1m[s][1], 0])
    print(len(final_urls))

final_urls.sort()
print(len(final_urls))
#print(list_1m[:20])
#print(lfinal_urls[:20])

#print(final_urls)
input('-----------------')


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
    "CREATE TABLE if not exists redirects (visit_id bigint, status_code int, data varchar(32), url_from varchar(1024), url_to varchar(1024), content_type varchar(264))")
cursor.execute(
    "CREATE TABLE if not exists all_requests (visit_id bigint, status_code int, data varchar(32), url_from varchar(1024), url_to varchar(1024), content_type varchar(264))")
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
