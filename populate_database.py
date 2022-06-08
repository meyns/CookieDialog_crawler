# Load list of websites
# urls = []
import random
import sqlite3

BASE_PATH = "d:/temp/Selenium-model/"
# BASE_PATH = "Selenium/" # voor docker run
BASE_PATH = "./data/" # Ubuntu

buckets = [[0, 25000, 25000],
           [25001,100000, 25000],
           [100001,250000, 25000],
           [250001,1000000, 25000]]

print('Populating databases')

with open('top-1m.csv') as file:
    lines = file.read()
    lines = lines.splitlines()
    #lines = [next(file) for x in range(START_SITE + LIMIT_NR_SITES)]
#lines = lines[START_SITE - 1:-1]
# print(lines)
lines2 = []
for line in lines:
    lines2.append(line.split(','))


urls = []

for k in range(4):
    print(buckets[k])
    if k == 0 and buckets[k][2] == buckets[k][1] - buckets[k][0]:
        for line in lines2[buckets[k][0]:buckets[k][1]]:
            urls.append([line[0], line[1], 0])
        #print(urls)
    else:
        sample = random.sample(range(buckets[k][0], buckets[k][1]), buckets[k][2])
        sample.sort()
        #print(sample)
        for s in sample:
            urls.append([lines2[s][0], lines2[s][1], 0])

print(urls)


# Populating database
print('setting up database')
conn = sqlite3.connect(BASE_PATH + 'cookies.db')
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE if not exists visits (site_nr int, sitename varchar(255), visit_type int, visit_id int, site_url varchar(255), cookie_numbers int)")
cursor.execute(
    "CREATE TABLE if not exists cookies (visit_id int, before_after varchar(24), short_url varchar(255), domain varchar(255), expires float(24), httpOnly bool, name varchar(255), path varchar(255), priority varchar(24), sameParty bool, sameSite varchar(25), secure bool, session bool, size int, sourcePort int, sourceScheme varchar(255), value varchar(255))")
cursor.execute(
    "CREATE TABLE if not exists elements (site_nr int, sitename varchar(255), element_type int, visited int, element_text varchar(255), element_css varchar(255), iframe_css varchar(255), location_x int, location_y int, text_color varchar(255), background_color varchar(255), width varchar(24), height varchar(24), font_size varchar(24), PRIMARY KEY (site_nr, element_type))")
# Fill in all rows of to be visited websites if they do not exist
for url in urls:
    print(url)
    # cursor.execute("INSERT OR IGNORE INTO cookie_numbers VALUES (?,?,?,?,?,?,?,?,?)", (url[0], url[1], None, None, None, None, None, None, None))
    #cursor.execute("INSERT OR IGNORE INTO cookie_numbers (site_nr, sitename) VALUES (?,?)",
    #               (url[0], url[1]))
    cursor.execute("INSERT OR IGNORE INTO elements (site_nr, sitename, element_type, visited) VALUES (?,?,?,?)",
                   (url[0], url[1], 0, 0))
cursor.execute('commit')
cursor.close()
conn.close()
