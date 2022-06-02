import time

import scrapy
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import random

url = "https://cookiepedia.co.uk/cookies/"

cookie_names = ["__gads", "recently_watched_video_id_list", "lkgmqdkngmsdgq"]
'''cookie_names = []
try:
    with open('cookie_names.txt', 'r') as file:
        cookie_names = file.read().splitlines()
except:
    pass'''

user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
               "Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"]

cookie_list = []
i = 0
while i < len(cookie_names):
    # Driver wordt elke 10 cookies heropgestart, anders wordt de driver hergebruikt
    if i%10 == 0:
        # Start driver
        options = webdriver.ChromeOptions()

        # Running headless makes the detection of selenium more likely
        options.add_argument('--headless')  # headfull not working in docker
        options.add_argument('--disable-gpu')
        options.add_argument("--incognito")
        '''Incognito does not block third party cookies in combination with headless. Incognito + headfull does block the third party cookies'''

        options.add_argument('--disable-extensions')
        options.add_argument('--disable-cookie-encryption')  # ?
        # options.add_argument('--https_only_mode_enabled')
        options.page_load_strategy = 'eager'  # eager -> enkel DOM laden
        rand = random.randrange(len(user_agents))
        options.add_argument("user-agent=" + user_agents[rand])
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

        driver = webdriver.Chrome(options=options)

        driver.set_window_size(1920, 1080)
        # driver.set_page_load_timeout(10)
        driver.set_script_timeout(10)

    print("Trying: " + cookie_names[i])
    driver.get(url + cookie_names[i])
    #time.sleep(1)

    try:
        element = driver.find_element(By.XPATH, "/html[1]/body[1]/div[3]/div[1]/p[2]/strong[1]")
        print(element.text)
        cookie_list.append([cookie_names[i], element.text])
        with open("cookie_names_class.txt", "a+") as file:
            file.write(cookie_names[i] + ";" + element.text + "\n")
    except Exception as err:
        cookie_list.append([cookie_names[i], "No matches"])
        with open("cookie_names_class.txt", "a+") as file:
            file.write(cookie_names[i] + ";" + "No matches" + "\n")

    if i % 10 == (10-1):
        # Shutdown driver for new session
        driver.quit()

    i += 1

print(cookie_list)