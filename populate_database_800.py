# Load list of websites
# urls = []
import random
import sqlite3

from sys import platform

if platform == "linux" or platform == "linux2":
    BASE_PATH = "./data/" # Ubuntu
elif platform == "darwin":
    # OS X
    pass
elif platform == "win32":
    BASE_PATH = "d:/temp/Selenium-model/"


# BASE_PATH = "Selenium/" # voor docker run

print('Populating databases')
filenames = ["bucket1_1-5000.txt", "bucket2_5000-25000.txt", "bucket3_25000-100000.txt", "bucket4_100000-1000000.txt"]

urls = []
for filename in filenames:
    with open(BASE_PATH + filename) as file:
        lines = file.read()
        lines = lines.splitlines()

    for line in lines:
        line = line.split(',')
        urls.append([int(line[0]), line[1]])

urls.sort()
print(urls)


# Populating database
print('setting up database')
conn = sqlite3.connect(BASE_PATH + 'cookies.db')
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE if not exists visits (visit_id bigint, site_nr int, sitename varchar(255), visit_type int, site_url varchar(255), cookie_numbers int)")
cursor.execute(
    "CREATE TABLE if not exists cookies (visit_id bigint, before_after varchar(24), short_url varchar(255), domain varchar(255), expires varchar(24), httpOnly bool, name varchar(255), path varchar(255), priority varchar(24), sameParty bool, sameSite varchar(25), secure bool, session bool, size int, sourcePort int, sourceScheme varchar(255), value varchar(255))")
cursor.execute(
    "CREATE TABLE if not exists elements (visit_id bigint, site_nr int, sitename varchar(255), element_type tinyint, visited tinyint, result varchar(255), element_text varchar(255), element_css varchar(255), iframe_css varchar(255), location_x int, location_y int, text_color varchar(255), background_color varchar(255), width varchar(24), height varchar(24), font_size varchar(24), PRIMARY KEY (site_nr, element_type))")
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
