import json
import random
import socket
import time

import requests
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By


def check_response(url):
    result = False
    try:
        socket.gethostbyname(url)
        result = url
    except:
        try:
            socket.gethostbyname("www." + url)
            result = "www." + url
        except:
            result = False
    print(url + " -> " + str(result))
    return result

def get_status_code(url):
    for entry in driver.get_log('performance'):
        for k, v in entry.items():
            if k == 'message' and 'status' in v:
                msg = json.loads(v)['message']['params']
                for mk, mv in msg.items():
                    if mk == 'response':
                        response_url = mv['url']
                        response_status = mv['status']
                        if response_url == url:
                            return response_status

PATH_CHROME = './chromedriver.exe'
#TYPES_WEBSITES = [".com", "co.uk", ".be", ".nl", ".eu", ".org", ".net", ".edu", ".gov"]
TYPES_WEBSITES = [".com", "co.uk", ".be", ".eu", ".org", ".net", ".edu", ".gov"]
TYPES_WEBSITES2 = [".nl"]
NOT_TYPES_WEBSITES = []
for tw in TYPES_WEBSITES:
    NOT_TYPES_WEBSITES.append(tw + ".")
NOT_TYPES_WEBSITES2 = []
for tw in TYPES_WEBSITES2:
    NOT_TYPES_WEBSITES2.append(tw + ".")

# Load list of websites
urls = []

with open('top-1m.csv') as file:
    # lines = file.readlines()
    lines = file.readlines()
#print(lines)

for line in lines:
    urls.append([line.replace('\n','').split(',')[0], line.replace('\n','').split(',')[1]])

print(urls)

# Buckets (telkens 200 websites)
# 0-25000
# 25001-100000
# 100001-250000
# 250001-1000000
buckets = [[0, 25000],
           [25001,100000],
           [100001,250000],
           [250001,1000000]]

visited = []
final_urls = [[],[],[],[]]
for k in range(0,4):
    i = 0
    while i < 250:
        visit = False
        if i < 220:
            number = random.randint(buckets[k][0], buckets[k][1])
            if any(website_type in urls[number][1] for website_type in TYPES_WEBSITES) \
                    and not any(website_type in urls[number][1] for website_type in NOT_TYPES_WEBSITES):
                visit = True
        else:
            number = random.randint(buckets[k][0], buckets[k][1])
            if any(website_type in urls[number][1] for website_type in TYPES_WEBSITES2) \
                    and not any(website_type in urls[number][1] for website_type in NOT_TYPES_WEBSITES2):
                visit = True
        if visit and number not in visited:
            visited.append(number)
            response = check_response(urls[number][1])
            if response:
                try:
                    options = webdriver.ChromeOptions()

                    # Running headless makes the detection of selenium more likely
                    options.add_argument('--headless')  # headfull not working in docker
                    options.add_argument('--disable-gpu')
                    # options.add_argument("--incognito")
                    '''Incognito does not block third party cookies in combination with headless. Incognito + headfull does block the third party cookies'''

                    options.add_argument('--disable-extensions')
                    options.add_argument('--disable-cookie-encryption')  # ?
                    # options.add_argument('--https_only_mode_enabled')
                    options.page_load_strategy = 'normal'  # eager -> enkel DOM laden
                    options.add_argument(
                        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36")
                    # ????    options.enable_mobile()
                    options.add_argument("--disable-notifications")
                    # options.add_argument("--disable-geolocation")
                    # options.add_argument("--disable-media-stream")
                    options.add_argument("--disable-infobars")
                    options.add_argument("--log-level=3")
                    options.add_experimental_option('excludeSwitches', ['enable-logging'])
                    options.add_argument("enable-automation")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    # options.add_argument("--disable-browser-side-navigation")
                    # options.add_argument("--dns-prefetch-disable")
                    # options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation": 1,
                    #                                          "profile.managed_default_content_settings.images": 2})

                    # Make detection of automation less likely
                    options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    options.add_experimental_option('useAutomationExtension', False)

                    # This works only in headless
                    options.add_argument('--blink-settings=imagesEnabled=false')
                    options.add_argument('--blink-settings=loadsImagesAutomatically=false')
                    options.add_argument('--disable-blink-features=AutomationControlled')

                    capabilities = DesiredCapabilities.CHROME
                    capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}

                    driver = webdriver.Chrome(options=options, desired_capabilities=capabilities)

                    driver.set_window_size(1920, 1080)
                    driver.set_page_load_timeout(10)
                    driver.set_script_timeout(10)

                    driver.get("http://" + response)
                    #driver.get("http://" + "www.pornhub.com")
                    time.sleep(1)

                    if get_status_code(driver.current_url) == 200:
                        #html = driver.find_element(By.XPATH, "/*").text
                        html = driver.page_source
                        ascii_count = html.encode("ascii", "ignore")


                        if len(ascii_count) < len(html) - len(ascii_count):
                            # print("Skipping url because more non-ascii letters than ascii letters (probably chinese website)")
                            print(urls[number][1] + " skipped because chinese")
                        elif "ERR_SSL_PROTOCOL_ERROR" in html:
                            # Website wordt geblokkeerd door de virusscanner
                            print(urls[number][1] + " skipped because virusscanner")
                        elif "ERR_NAME_NOT_RESOLVED" in html:
                            print(urls[number][1] + " skipped because can't be reached")
                        elif 'ERR_' in html or '_ERR' in html or "This site has been blocked" in html or "HTTP ERROR" in html:
                            print(urls[number][1] + " skipped because ...")
                        elif "Website Blocked" in html or "This site is blocked due" in html or "block.opendns.com" in driver.current_url:
                            print(urls[number][1] + " skipped because virusscanner 2")
                        else:
                            # iframes check?
                            to_add = urls[number]
                            to_add.append(response)
                            final_urls[k].append(to_add)
                            i += 1
                            #filename = "800_sites_list_bucket_" + str(buckets[k][0]) + "_" + str(buckets[k][1]) + ".csv"
                            filename = "800_sites_list_bucket.csv"
                            with open(filename, 'a+') as file:
                                file.write(to_add[0] + ";" + to_add[1] + ";" + to_add[2] + "\n")
                except:
                    print(urls[number][1] + " skipped because error during visit")
                finally:
                    driver.quit()
            else:
                print(urls[number][1] + " skipped because no response")
        else:
            print(urls[number][1] + " skipped because wrong extension")

'''
print(final_urls)
for k in range(4):
    filename = "800_sites_list_bucket_" + str(buckets[k][0]) + "_" + str(buckets[k][1]) + ".csv"
    with open(filename, 'a+') as file:
        for final_url in final_urls[k]:
            file.write(final_url[0] + ";" + final_url[1] + ";" + final_url[2] + "\n")'''


