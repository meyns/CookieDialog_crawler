import json
import random
import sqlite3
import pprint

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expect
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
from selenium.webdriver.chrome.service import Service
from multiprocessing import Process, Value, cpu_count, Queue, freeze_support, Lock, Manager, Pool, Value
import os
import socket
import chromedriver_autoinstaller
import psutil
import PySimpleGUI as sg
import logging

# print('Setting up global fixed variables')
from simpletransformers.classification import ClassificationModel
from simpletransformers.config.model_args import ClassificationArgs

PATH_CHROME = './chromedriver.exe'
PATH_FIREFOX = 'D:/Documenten/Maarten/Open universiteit/VAF/selenium/geckodriver.exe'
# PATH_EDGE
# PATH_SAFARI

ML_dir_cookie_dialog = "D:/temp/cookie-notice selector backup/output/"
ML_dir_buttons = "D:/temp/cookie-notice selector/output 10epochs 2e05 64bs 10 evalbs 64maxsl/"
# ML_dir_cookie_dialog = "Selenium/output_dialog"
# ML_dir_buttons = "Selenium/output_buttons"
#ML_dir_cookie_dialog = "./model_dialog" #Ubuntu
#ML_dir_buttons = "./model_buttons" #Ubuntu

BASE_PATH = "d:/temp/Selenium-model/"
# BASE_PATH = "Selenium/" # voor docker run
#BASE_PATH = "./data/" # Ubuntu

LIMIT_CPU = 1  # cpu_count() - 1 # int(cpu_count()) // 2 #cpu_count() - 1 #int(cpu_count()) // 2
#LIMIT_NR_SITES = 4
#START_SITE = 3715  # 1 = start
TIMEOUT = 90
TYPES_WEBSITES = []  # BE NL COM EU ORG COM
BROWSER = "chrome"  # firefox,chrome,edge,safari
RUNS = 1  # how many repeats
nr_fails = 100

button_dict = {"ACCEPT": 1,
               "DECLINE": 2,
               "MODIFY": 3,
               "SAVE": 4
               }

logging.basicConfig(level=logging.ERROR)
transformers_logger = logging.getLogger("simpletransformers")
transformers_logger.setLevel(logging.ERROR)


# alle directe descendants namen
def all_direct_descendants(element):
    return element.find_elements(By.XPATH, "./*")


def finetune_element(element, type_ifr='normal'):
    # print('Finetuning')
    try:
        iframes = element.find_elements(By.XPATH, './/iframe')
        if element.tag_name == 'iframe':
            pass
        elif iframes and type_ifr == 'normal':
            # print(iframes)
            element = iframes[0]
        else:
            last_element = False
            chi = element.find_elements(By.XPATH, "./*")
            while not last_element and len(chi) <= 2:
                # print(chi)
                if len(chi) == 0:
                    # print('breaking 0 list')
                    last_element = True
                    break
                elif len(chi) == 1:
                    # print('before 1 list')
                    element = chi[0]
                    # print(element)
                    chi = element.find_elements(By.XPATH, "./*")
                else:
                    # print('running 2 list')
                    if chi[0].get_attribute('innerHTML') == "" or chi[0].tag_name == 'head':
                        chi = chi[1].find_elements(By.XPATH, "./*")
                    elif chi[1].get_attribute('innerHTML') == "":
                        chi = chi[0].find_elements(By.XPATH, "./*")
                    else:
                        last_element = True

    except Exception as err:
        print(err)

    return element


def volgende_laag(element, driver, candidates):
    # print('Testing layer ', end="")
    # print(element.id)
    try:
        # children = all_direct_descendants(element)
        children = driver.execute_script("return \
                  Array.from(arguments[0].children)\
                    .map((el) => ({zIndex: Number(getComputedStyle(el).zIndex), element: el }))\
                    .filter(({ zIndex }) => !isNaN(zIndex))\
                    .filter(({ zIndex }) => (zIndex > 0))\
                    .sort((r1, r2) => r2.zIndex - r1.zIndex)\
                    .slice(0, 10);\
                  console.table(data);", element)
        # time.sleep(0.05)
        if not children:  # Er zijn geen kinderen met een z-index neem dan alle kinderen van alle elementen
            children = all_direct_descendants(element)
            for e in children:
                volgende_laag(e, driver, candidates)
        else:
            for e_dict in children[5]:
                e = e_dict['element']
                if len(e.get_attribute('innerHTML')) > 50 and e.size['width'] > 0 and e.size['height'] > 0:
                    highest_z_score = e_dict['zIndex']
                    highest_element = finetune_element(e)

                    # print(highest_element.is_displayed())
                    '''print("z-score candidate: " + str(highest_z_score) + "-" + highest_element.tag_name + "-" + str(
                        highest_element.size['width'])) # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
                    candidates.append(highest_element)
                else:
                    # print('pass')
                    pass
    except Exception as err:
        print(err)


def highest_z_index(driver, candidates, do_layers):
    try:
        z_indexes = driver.execute_script("""return \
          Array.from(document.querySelectorAll('*'))\
            .map((el) => ({zIndex: Number(getComputedStyle(el).zIndex), element: el }))\
            .filter(({ zIndex }) => !isNaN(zIndex))\
            .filter(({ zIndex }) => (zIndex > 0))\
            .sort((r1, r2) => r2.zIndex - r1.zIndex)\
            .slice(0, 10);\
          console.table(data);""")  # sorted list of z-indexes
        # time.sleep(0.05)
        # print(z_indexes)
        if z_indexes:
            if z_indexes[0]['zIndex'] > 0:
                do_layers = True
        for e_dict in z_indexes:
            element = e_dict['element']
            z_score = e_dict['zIndex']
            element = finetune_element(element)
            if element not in candidates:
                # print(element.tag_name)
                if element.size['width'] > 10 and element.size['height'] > 10 and (
                        len(element.get_attribute('innerHTML')) > 50 or element.tag_name == "iframe"):
                    '''print("highest z-score candidate: " + str(z_score) + "-" + element.tag_name + "-" + str(
                        element.size['width'])) # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
                    candidates.append(element)
    except Exception as err:
        print(err)


def get_active_element(driver, candidates):
    try:
        element = driver.execute_script("return document.activeElement")
        # print(element)
        if element.tag_name in []:  # ["body", "html"]:
            pass
        else:
            element = finetune_element(element)
            if element.size['width'] > 10 and element.size['height'] > 10 and len(
                    element.get_attribute('innerHTML')) > 50:
                is_parent_in_candidates = False
                '''for index, c in enumerate(candidates):
                    if element.get_attribute('outerHTML') in c.get_attribute('outerHTML'):
                        is_parent_in_candidates = True
                if not is_parent_in_candidates:'''
                '''print("Active element: " + element.tag_name + "-" + str(
                    element.size['width']))  # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
                candidates.append(element)
    except Exception as err:
        print(err)


def candidate_filter(candidates):
    try:
        for index, c in reversed(list(enumerate(candidates))):
            # innerText = driver.execute_script("""return arguments[0].innerText;""", c)
            # innerHTML = ' '.join(c.get_attribute('innerHTML').split()).replace('\n', '')
            text3 = c.text
            if c.tag_name in ["style", "ul", "il", "a", "svg", "button"]:  # Element that can't be a cookie dialog
                # print('Candidate popped = ' + c.tag_name)
                candidates.pop(index)
            elif c.tag_name == 'iframe':
                pass
            elif len(text3) < 50:
                # print(c.tag_name)
                # print('Candidate popped too small text')
                candidates.pop(index)
    except Exception as err:
        print(err)

    i = 0
    while i < len(candidates):
        for index, c in enumerate(candidates):
            if index == i:
                pass
            elif candidates[i].get_attribute('outerHTML') in c.get_attribute('outerHTML'):
                candidates.pop(index)
                # print('Candidate popped, is father of other element')
                if index <= i:
                    i -= 1
        i += 1


def adding_iframe(driver, candidates):
    try:
        elements = driver.find_elements(By.XPATH, '//iframe')
        if elements:
            for element in elements:
                if element not in candidates:
                    if element.size['width'] > 10 and element.size['height'] > 10:
                        # print("i-frame candidate: " + element.tag_name + "-" + str(
                        #    element.size[
                        #        'width']))  # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))
                        candidates.append(element)
    except Exception as err:
        print(err)


def get_status_code(driver, url):
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


def main():
    # kill_processes()
    chromedriver_autoinstaller.install()  # only used for docker run

    # print(os.listdir())

    # Setting up folders
    '''if not os.path.exists(BASE_PATH + 'screenshots'):
        os.mkdir(BASE_PATH + 'screenshots')
    if not os.path.exists(BASE_PATH + 'screenshots_clicked_0'):
        os.mkdir(BASE_PATH + 'screenshots_clicked_0')
    if not os.path.exists(BASE_PATH + 'screenshots_not_clicked_0'):
        os.mkdir(BASE_PATH + 'screenshots_not_clicked_0')
    if not os.path.exists(BASE_PATH + 'screenshots_clicked_1'):
        os.mkdir(BASE_PATH + 'screenshots_clicked_1')
    if not os.path.exists(BASE_PATH + 'screenshots_not_clicked_1'):
        os.mkdir(BASE_PATH + 'screenshots_not_clicked_1')'''

    ''''# Load list of websites
    # urls = []
    urls = Manager().list([])

    with open('top-1m.csv') as file:
        # lines = file.readlines()
        lines = [next(file) for x in range(START_SITE + LIMIT_NR_SITES)]
    lines = lines[START_SITE - 1:-1]
    # print(lines)

    if LIMIT_NR_SITES < 100:
        batch_size = LIMIT_NR_SITES
    else:
        batch_size = 100
    batch = 0
    while batch < LIMIT_NR_SITES:
        for visit_type in range(1, 2):  # 0=collect elements 1=accept 2=decline 3=modify 4=save
            append = False
            for line in lines[batch:batch + batch_size]:
                line2 = line.replace('\n', "").split(",")
                if not TYPES_WEBSITES or any(type in line2[1] for type in TYPES_WEBSITES):
                    urls.append([line2[0], line2[1], visit_type])
        batch += batch_size
    # print(urls)

    # Seting up databases if not exisits
    print('setting up database')
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE if not exists cookie_numbers (site_nr int PRIMARY KEY, sitename varchar(255), visit_result varchar(255), method varchar(24), button_accept varchar(255), button_decline varchar(255), cookies_before int, cookies_after_accept int, cookies_after_decline int)")
    cursor.execute(
        "CREATE TABLE if not exists visits (site_nr int, sitename varchar(255), visit_type int, visit_nr int, site_url varchar(255))")
    cursor.execute(
        "CREATE TABLE if not exists cookies (visit_id int, before_after varchar(24), short_url varchar(255), domain varchar(255), expires float(24), httpOnly bool, name varchar(255), path varchar(255), priority varchar(24), sameParty bool, sameSite varchar(25), secure bool, session bool, size int, sourcePort int, sourceScheme varchar(255), value varchar(255))")
    cursor.execute(
        "CREATE TABLE if not exists elements (site_nr int, sitename varchar(255), element_type int, visited int, element_text varchar(255), element_css varchar(255), iframe_css varchar(255), text_color varchar(255), background_color varchar(255), width varchar(24), height varchar(24), font_size varchar(24), PRIMARY KEY (site_nr, element_type))")
    # Fill in all rows of to be visited websites if they do not exist
    for url in urls:
        print(url)
        # cursor.execute("INSERT OR IGNORE INTO cookie_numbers VALUES (?,?,?,?,?,?,?,?,?)", (url[0], url[1], None, None, None, None, None, None, None))
        cursor.execute("INSERT OR IGNORE INTO cookie_numbers (site_nr, sitename) VALUES (?,?)",
                       (url[0], url[1]))
        cursor.execute("INSERT OR IGNORE INTO elements (site_nr, sitename, element_type, visited) VALUES (?,?,?,?)",
                       (url[0], url[1], 0, 0))
    cursor.execute('commit')
    cursor.close()
    conn.close()'''

    '''# Read in buttons list
    accept_buttons_list = []
    try:
        file = open('accept_buttons_list.txt', 'r')
        accept_buttons_list = file.read().splitlines()
        file.close()
        # print(buttons_list)
    except:
        pass

    decline_buttons_list = []
    try:
        file = open('decline_buttons_list.txt', 'r')
        decline_buttons_list = file.read().splitlines()
        file.close()
        # print(buttons_list)
    except:
        pass'''

    # read in already visited sites
    previously_visited_nrs = [[], []]
    '''if os.path.exists('cookies.db'):
        conn = sqlite3.connect('cookies.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cookie_numbers")
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            if not r[0] == 0:
                previously_visited_nrs[r[1]].append(r[2])
        print(previously_visited_nrs)'''

    do_not_visit = Manager().list([])
    '''if os.path.exists(BASE_PATH + 'cookies.db'):
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        cursor.execute("SELECT site_nr, visit_result, cookies_before, cookies_after_accept, cookies_after_decline FROM cookie_numbers")
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            #if (not r[4] is None) or (not r[2] is None and r[3] is None):
            if not r[1] is None:
                do_not_visit.append(r[0])
    print(do_not_visit)'''

    # Read in to visit sites from populated database
    print('Reading in database')
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    cursor.execute('SELECT site_nr, sitename, element_type FROM elements where visited == ? ORDER BY site_nr ASC', (0,))
    res = cursor.fetchall()
    conn.close()

    print(res)
    urls = Manager().list([])
    for r in res:
        urls.append(list(r))
    print(urls)

    # kill_processes()
    now = time.time()

    cookies = Manager().list([])
    cookies2 = Manager().list([])
    visits = Manager().list([])
    elements = Manager().list([])
    lock = Lock()

    session_ch = []

    # print('Starting run {}'.format(r+1))

    # Loading in models
    '''print('Loading in prediction models')
    model_dialog = ClassificationModel("xlmroberta", ML_dir_cookie_dialog,
                                       use_cuda=False)
    model_buttons = ClassificationModel("xlmroberta", ML_dir_buttons,
                                        use_cuda=False)'''

    # Load variables
    runn = Value('i', 1)
    stop = Value('b', False)
    fails = Value('i', 0)

    # Read in previously visited nrs of sites -> reread every run to only visit unvisited sites
    '''if os.path.exists(BASE_PATH + 'cookies.txt'):
        with open(BASE_PATH + 'cookies.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                line2 = line.replace('\n', "").split(",")
                previously_visited_nrs.append(int(line2[2]))
    print(previously_visited_nrs)'''

    # start processes
    while not stop.value:
        print('Staring while loop')

        # Start GUI thread
        n = Process(target=gui_thread, args=(stop, fails))
        n.start()

        # start writing process
        o = Process(target=writing_thread,
                    args=(lock, urls, stop, fails, cookies, cookies2, visits, do_not_visit, elements))
        o.start()

        fails.value = 0

        # start browser sessions
        for thread_nr in range(LIMIT_CPU):
            p = Process(target=session_checker, args=(
                lock, thread_nr, runn, stop, now, urls, fails, cookies, cookies2, previously_visited_nrs, visits,
                do_not_visit, elements))
            session_ch.append(p)
            p.start()
            time.sleep(5)  # To make sure not all threads start at the same time

        # wait until > nr_fails fails or stop value
        while fails.value < nr_fails and not stop.value:
            time.sleep(1)

        if stop.value:
            print("------------------------------Stop signal received going to shut down")
        else:
            print("------------------------------Fails reached trying to shut down")

        # nr_fails fails have occurred, or we want to stop -> wait until all running processes timeout
        start = time.time()
        while time.time() - start <= TIMEOUT + 20:
            if not any(p.is_alive() for p in session_ch):
                # All the processes have finished, break now.
                for s in session_ch:
                    s.terminate()
                    s.join()
                print("All processes are finished breaking down now")
                '''for p in session_ch:
                    p.join()'''
                print(session_ch)
                session_ch = []
                break
            time.sleep(1)  # Just to avoid hogging the CPU

        # A timeout has occured (no break) all threads need to be killed off
        else:
            i = 0
            for p in session_ch:  # go through all processes that have 'timed out'
                print(str(i) + ' process has timed out')
                fails.value += 1
                i += 1
                with lock:
                    # killtree(os.getpid())
                    p.terminate()
                    p.join()
                    pass
            print("{} threads have timed out".format(i))

        # killtree(os.getpid())

    print('One last write')
    print(cookies)
    print(cookies2)
    print(visits)
    print(elements)
    writing(lock, urls, stop, cookies, cookies2, visits, do_not_visit, elements)

    print('Main thread finished')
    killtree(os.getpid(), including_parent=True)


def gui_thread(stop, fails):
    print('Starting gui thread')
    layout = [
        [sg.Text(size=(400, 400), key='-CPU-', background_color="black")]
    ]
    window = sg.Window('My Program', layout, size=(400, 400), finalize=True)

    while fails.value < nr_fails and not stop.value:
        window.read(1000)
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        line = "CPU " + str(cpu) + "% - RAM " + str(ram) + "%"
        if cpu > 70:
            line += " CPU WARNING"
        if ram > 70:
            line += " RAM WARNING"
        line += '\n'
        window['-CPU-'].update(line + window['-CPU-'].get())

        with open(BASE_PATH + "resources.txt", "a") as file:
            file.write(time.ctime() + " " + line + "\n")

    window.close()


def writing_thread(lock, urls, stop, fails, cookies, cookies2, visits, do_not_visit, elements):
    print("Starting writing thread")
    while fails.value < nr_fails and not stop.value:
        time_slept = 0
        while fails.value < nr_fails and not stop.value and time_slept < 30:
            time.sleep(1)
            time_slept += 1
        if time_slept == 30:
            writing(lock, urls, stop, cookies, cookies2, visits, do_not_visit, elements)
    print('End writing thread')


def writing(lock, urls, stop, cookies, cookies2, visits, do_not_visit, elements):
    # print('Locking cookie data')
    cookies_dupl = []
    cookies2_dupl = []
    visits_dupl = []
    elements_dupl = []

    with lock:
        '''if len(cookies) > 0:
            cookies_dupl = list(cookies)
            del cookies[:]'''
        if len(cookies2) > 0:
            cookies2_dupl = list(cookies2)
            del cookies2[:]
        if len(visits) > 0:
            visits_dupl = list(visits)
            del visits[:]
        if len(elements) > 0:
            elements_dupl = list(elements)
            del elements[:]

    with lock:
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')

        '''if len(cookies_dupl) > 0:
            cursor = conn.cursor()
            for c in cookies_dupl:
                cursor.execute('INSERT INTO cookie_numbers VALUES(?,?,?,?)',
                               (c[0], c[1], c[2], c[3]))
            cursor.execute('COMMIT')
            cursor.close()'''

        if len(cookies2_dupl) > 0:
            # print('Writing to database file cookies')
            cursor = conn.cursor()
            for c in cookies2_dupl:
                cursor.execute('INSERT INTO cookies VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12], c[13],
                                c[14], c[15], c[16]))
            cursor.execute('COMMIT')
            cursor.close()

        if len(visits_dupl) > 0:
            # print('Writing to database file visits')
            cursor = conn.cursor()
            for v in visits_dupl:
                cursor.execute('INSERT INTO visits VALUES(?, ?, ?, ?, ?, ?)',
                               (v[0], v[1], v[2], v[3], v[4], v[5]))
            cursor.execute('COMMIT')
            cursor.close()

        if len(elements_dupl) > 0:
            # print('Writing to database file elements')
            cursor = conn.cursor()
            for e in elements_dupl:
                print(e)
                cursor.execute('INSERT OR IGNORE INTO elements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                               (e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], e[12]))
                cursor.execute('UPDATE elements SET visited = ?, element_text = ?, element_css = ?, iframe_css = ?, '
                               'location = ?, text_color = ?, background_color = ?, width = ?, height = ?, '
                               'font_size = ? WHERE site_nr = ? AND element_type = ?',
                                (e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], e[12], e[0], e[2]))
            cursor.execute('COMMIT')
            cursor.close()

        conn.close()

    print('Finished writing to cookies files')


def kill_processes():
    # kill all chrome instances
    os.system("taskkill /f /im chromedriver.exe")
    os.system("taskkill /f /im operadriver.exe")
    os.system("taskkill /f /im geckodriver.exe")
    os.system("taskkill /f /im IEDriverServer.exe")
    if BROWSER == "chrome":
        os.system("taskkill /f /im Chrome.exe")
    if BROWSER == "firefox":
        os.system("taskkill /f /im Firefox.exe")


# used to kill the partent-child tree
def killtree(pid, including_parent=False):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        print("Killing child: {}".format(child.pid))
        child.kill()

    if including_parent:
        print("Killing parent: {}".format(parent.pid))
        parent.kill()


# Try the website if it is alive
def check_response(url):
    try:
        socket.gethostbyname(url)
        response = url
    except:
        try:
            socket.gethostbyname("www." + url)
            response = "www." + url
        except:
            response = False
    # print(url + " -> " + str(response))
    return response


# writing to cookies variable
def write_cookies(before_after, visit_id, cookies_temp, cookies2, short_url):
    list_items = ["visit_id", "before_after", "short_url", "domain", "expires", "httpOnly", "name", "path", "priority",
                  "sameParty", "sameSite",
                  "secure", "session", "size", "sourcePort", "sourceScheme", "value"]
    # pprint.pprint(cookies_temp)
    for c in cookies_temp:
        # print(c)
        list_temp = [visit_id, before_after, short_url, "", 0.0, None, "", "", "", None, "", None, None, 0, 0, "", ""]
        for item in list_items:
            # print(item)
            if item in c:
                # print(c[item])
                list_temp[list_items.index(item)] = c[item]
        cookies2.append(list_temp)
        # print(list_temp)


# def search_for_elements(driver):


# This is the session that visits the website
def session(lock, stop, start_time, short_url, url, visit_type, site_nr, fails, cookies, cookies2, visit_id, visits,
            elements, urls, runn):
    print('')
    #pprint.pprint(list(urls))
    print(str(runn.value) + '-(' + str(site_nr) + '-' + str(visit_type) + ') Thread started ' + url + " - Visit_id: " + str(visit_id) + " - Visit_type: " + str(
        visit_type))
    this_url_start = time.time()

    if BROWSER == "chrome":
        options = webdriver.ChromeOptions()
    if BROWSER == "firefox":
        options = webdriver.FirefoxOptions()

    # Running headless makes the detection of selenium more likely
    options.add_argument('--headless')  # headfull not working in docker
    options.add_argument('--disable-gpu')
    options.add_argument("--incognito")
    '''Incognito does not block third party cookies in combination with headless. Incognito + headfull does block the third party cookies'''

    options.add_argument('--disable-extensions')
    options.add_argument('--disable-cookie-encryption')  # ?
    # options.add_argument('--https_only_mode_enabled')
    options.page_load_strategy = 'eager'  # eager -> enkel DOM laden
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

    # print('Opstart tijd driver: {:.2f}'.format(time.time() - this_thread_start))

    # Prepare variables
    has_clicked = False
    button = ""
    method = ""
    cookies_voor = None
    cookies_na = None
    # cookies_temp = []
    if visit_type == 2:
        type_text = "DECLINE"
    elif visit_type == 3:
        type_text = "MODIFY"
    elif visit_type == 4:
        type_text = "SAVE"

    # starting up webdriver
    if BROWSER == "chrome":
        # driver = webdriver.Chrome(service=Service(PATH_CHROME), options=options)
        driver = webdriver.Chrome(options=options, desired_capabilities=capabilities)
    if BROWSER == "firefox":
        driver = webdriver.Firefox(service=Service(PATH_FIREFOX), options=options, desired_capabilities=capabilities)

    driver.set_window_size(1920, 1080)
    # driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)

    #############################

    # Check database for entries
    with lock:
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM elements where site_nr == ? ORDER BY element_type ASC', (site_nr,))
        res = cursor.fetchall()
        conn.close()
        # print(res)

    visit = False
    element_css = ""
    if (res[0][2] == 0 and res[0][3] == 0) and visit_type == 0:
        visit = True
        try:
            driver.get("http://" + url)
            time.sleep(5)

            visits.append([site_nr, short_url, visit_type, visit_id, driver.current_url, -1])

            # Count the non ascii characters if more than half are non-ascii characters then skip this site (probably chinese)
            html = driver.find_element(By.XPATH, "/*").text
            ascii_count = html.encode("ascii", "ignore")
            if len(ascii_count) < len(html) - len(ascii_count):
                print(str(site_nr) + "-" + short_url + " - Skipping url because more non-ascii letters than ascii letters (probably chinese website)")
                with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(str(site_nr) + "°" + short_url + " Skipped because probably Chinese\n")
                elements.append(
                    [site_nr, short_url, 0, 1, "# Skipped Chinese website", "", "", "", "", "", "", "", ""])
                visits.append([site_nr, short_url, visit_type, visit_id, "chinese", -1])

            elif not get_status_code(driver, driver.current_url) == 200:
                print(str(site_nr) + "-" + short_url + " - Skipping url because not 200 status code")
                with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(str(site_nr) + "°" + short_url + " Skipped because not 200 status code\n")
                elements.append(
                    [site_nr, short_url, 0, 1, "# Skipped no 200 response", "", "", "", "", "", "", "", ""])
                visits.append([site_nr, short_url, visit_type, visit_id, "no 200 respone", -1])
            elif "ERR_" in html:
                print(str(site_nr) + "-" + short_url + " - Skipping url because error code")
                with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(str(site_nr) + "°" + short_url + " Skipping url because error code\n")
                elements.append(
                    [site_nr, short_url, 0, 1, "# Skipped error code", "", "", "", "", "", "", "", ""])
                visits.append([site_nr, short_url, visit_type, visit_id, "error code", -1])
            elif "Website Blocked" in html:
                print(str(site_nr) + "-" + short_url + " - Skipping url because website blocked")
                with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(str(site_nr) + "°" + short_url + " Skipping url because website blocked\n")
                elements.append(
                    [site_nr, short_url, 0, 1, "# Skipped website blocked", "", "", "", "", "", "", "", ""])
                visits.append([site_nr, short_url, visit_type, visit_id, "website blocked", -1])
            else:
                do_layers = False

                candidates = []
                # print("----{:2f}s-----URL loaded--".format(time.time() - this_url_start))

                # print('Testing highest z_scores')
                highest_z_index(driver, candidates, do_layers)
                # print(candidates)
                # print("----{:2f}s-----Finished highest z-scores--".format(time.time() - this_url_start))

                if do_layers:
                    # print('Testing layers')
                    volgende_laag(driver.find_element(By.XPATH, "/*"), driver, candidates)  # root element
                    # print(candidates)
                    # print("----{:2f}s-----Finished layers--".format(time.time() - this_url_start))
                else:
                    # print('Skipping layers, no z-scores')
                    pass

                # print('Adding iframe')
                adding_iframe(driver, candidates)
                # print(candidates)
                # print("----{:2f}s-----Finished iframes--".format(time.time() - this_url_start))

                # print('Testing active element')
                get_active_element(driver, candidates)
                # print(candidates)
                # print("----{:2f}s-----Finished active element--".format(time.time() - this_url_start))

                # print('Filtering candidates {}'.format(len(candidates)))
                # print(candidates)
                candidate_filter(candidates)
                # print(candidates)
                # print("----{:2f}s-----Finished filtering candidates--".format(time.time() - this_url_start))

                cookie_dialog_found = False
                if not candidates:
                    print("No candidates found")
                    pass

                else:
                    print('Processing candidates ' + str(len(candidates)))
                    model_dialog = ClassificationModel("xlmroberta", ML_dir_cookie_dialog, args={"silent": True},
                                                       use_cuda=False)
                    for index, c in enumerate(candidates):
                        # print('Saving cadidate ' + str(index))
                        try:
                            # print(c.size['width'])
                            # print(c.size['height'])
                            # print(c.get_attribute('innerHTML'))
                            iframe_test = (c.tag_name == 'iframe')
                            if iframe_test:
                                iframe = c
                                driver.switch_to.frame(c)
                                c = driver.find_element(By.XPATH, '/*')  # first child in iframe
                                c = finetune_element(c, 'iframe')
                                # print(c)

                            # text = driver.execute_script("""return arguments[0].innerText;""", c)
                            # text2 = c.get_attribute('innerHTML')
                            text3 = c.text
                            # print(text3)

                            try:
                                # check = isinstance(c.screenshot_as_png, str)
                                if c.size['width'] > 10 and c.size['height'] > 10 and text3 and len(text3) >= 20:
                                    # Check for cookie dialog with trained model
                                    with lock:
                                        predictions, raw_outputs = model_dialog.predict(
                                            [text3.lower().replace('\n', ' ').replace(';', ',')])

                                    print("Prediction made, result: {} - {}".format(predictions[0], ''.join(
                                        [x for index, x in enumerate(text3.replace('\n', ' ')) if index < 50])))

                                    if predictions[0] == "True":
                                        cookie_dialog_found = True
                                        with open(BASE_PATH + str(site_nr).zfill(7) + "°" + short_url + "°" + str(
                                                index).zfill(2) + "°" + c.tag_name + "°element.png", "wb") as file:
                                            # print('Saved screenshot1')
                                            file.write(c.screenshot_as_png)
                                            # print('Saved screenshot2')
                                        with open(BASE_PATH + str(site_nr).zfill(7) + "-" + short_url + "°" + str(
                                                index).zfill(2) + "°" + c.tag_name + "°element.txt", "w") as file:
                                            file.write(text3)
                                            # print('Saved txt file')

                                        c.get_attribute("style")
                                        text_color = c.value_of_css_property('color')
                                        background_color = c.value_of_css_property('background-color')
                                        width = c.value_of_css_property('width')
                                        height = c.value_of_css_property('height')
                                        font_size = c.value_of_css_property('font-size')
                                        location = str(c.location).replace("{", "").replace("}", "")
                                        '''if not isinstance(location, str):
                                            location = ""
                                            print("##################################")'''

                                        short_text = ''.join([x for index, x in enumerate(text3.replace('\n', ' ')) if index < 240])

                                        elements.append([site_nr, short_url, 0, 1, short_text, "",
                                                        "", location, text_color, background_color, width, height, font_size])

                                        # Extract elements from cookie dialog:
                                        # print(c.text)
                                        # pprint.pprint(c.get_attribute('innerHTML'))
                                        # print("-------------------collecting children")
                                        cookie_elements = c.find_elements(By.XPATH,
                                                                          ".//button | .//a | .//span | .//svg")
                                        # pprint.pprint(elements)
                                        all_texts = []
                                        model_buttons = ClassificationModel("xlmroberta", ML_dir_buttons,
                                                                            args={"silent": True},
                                                                            use_cuda=False)
                                        for el in cookie_elements:
                                            text = el.text
                                            # print('Trying element: ' + text)

                                            if len(text) > 0 and text not in all_texts:
                                                all_texts.append(text)
                                                # print(el.tag_name, end=" - ")
                                                # print(text)

                                                # Check elements for buttons with trained model
                                                with lock:
                                                    predictions2, raw_outputs2 = model_buttons.predict(
                                                        [text.replace("\n", " ")])
                                                print("Prediction made, result: {} - {}".format(predictions2[0],
                                                                                                ''.join(
                                                                                                    [x for index, x in
                                                                                                     enumerate(
                                                                                                         text.replace(
                                                                                                             '\n', ' '))
                                                                                                     if index < 50])))

                                                button_type = predictions2[0]

                                                '''button_type = "OTHER"
                                                if text.lower().replace(" ","").replace('"', '').replace("::before","") in accept_buttons_list:
                                                    button_type = "ACCEPT"
                                                elif text.lower().replace(" ","").replace('"', '').replace("::before","") in decline_buttons_list:
                                                    button_type = "DECLINE"
                                                elif text.lower().replace(" ","").replace('"', '').replace("::before","") in modify_buttons_list:
                                                    button_type = "MODIFY"'''

                                                if not button_type == "OTHER":
                                                    save_element_class = (el.get_attribute('class') or '')
                                                    if not save_element_class == '':
                                                        save_element_class = "." + ".".join(
                                                            el.get_attribute('class').split())
                                                    save_element_name = el.tag_name
                                                    save_element_text = el.text
                                                    save_element_id = (el.get_attribute('id') or '')
                                                    if not save_element_id == '':
                                                        save_element_id = "#" + save_element_id

                                                    save_element_css = save_element_name + save_element_class + save_element_id

                                                    el.get_attribute("style")
                                                    text_color = el.value_of_css_property('color')
                                                    background_color = el.value_of_css_property('background-color')
                                                    width = el.value_of_css_property('width')
                                                    height = el.value_of_css_property('height')
                                                    font_size = el.value_of_css_property('font-size')
                                                    location = str(c.location).replace("{", "").replace("}", "")
                                                    '''if not isinstance(location, str):
                                                        location = ""
                                                        print("##################################")'''

                                                    # To use for ACCEPT visit
                                                    if button_type == "ACCEPT":
                                                        element_text = save_element_text
                                                        element_css = save_element_css

                                                    # Writing buttons to csv file
                                                    line_to_add = str(site_nr).zfill(
                                                        7) + ";" + short_url + ";" + save_element_name + ";" + save_element_text.replace(
                                                        ";", ",").replace(
                                                        '\n', '') + ";" + button_type
                                                    line_to_add = line_to_add + ";" + save_element_css
                                                    with open(BASE_PATH + "buttons.csv", 'a', encoding='utf-8') as file:
                                                        file.write(line_to_add + '\n')

                                                    iframe_element_css = ""
                                                    if iframe_test:
                                                        iframe_element_class = "." + ".".join(
                                                            iframe.get_attribute('class').split())
                                                        iframe_element_name = iframe.tag_name
                                                        iframe_element_id = (iframe.get_attribute('id') or '')
                                                        if not iframe_element_id == '':
                                                            iframe_element_id = "#" + iframe_element_id

                                                        iframe_element_css = iframe_element_name + iframe_element_class + iframe_element_id

                                                    # Writing to database
                                                    # [site nr, sitename, element_type, visited?, element_text, element_css]
                                                    elements.append([site_nr, short_url, button_dict[button_type], 0,
                                                                     save_element_text, save_element_css,
                                                                     iframe_element_css, location, text_color, background_color, width, height, font_size])

                                                    # Add the new visits for detected buttons to url list. If list is too low then add to end of list
                                                    try:
                                                        urls.insert(runn.value + button_dict[button_type] * 5 + LIMIT_CPU, [site_nr, short_url, button_dict[button_type]])
                                                    except:
                                                        urls.append([site_nr, short_url, button_dict[button_type]])
                                                    # print([site_nr, short_url, button_dict[button_type], 0, save_element_text, save_element_css, iframe_element_css])

                                        # print("-------------------elements printed")
                                        del model_buttons

                            except Exception as err:
                                print(err)

                            try:
                                if iframe_test:
                                    driver.switch_to.parent_frame()
                            except Exception as err:
                                # print("Error while switching to parent frame")
                                pass

                            '''if c.is_displayed():
                                # take screenshot from element
                                with open("d:/temp/cookie-notice selector/" + short_url[0] + "-" + short_url[1] + "-" + str(index) + "-element.png", "wb") as elem_file:
                                    elem_file.write(c.screenshot_as_png)
                            else:
                                print('Candidate is not displayed')'''

                        except Exception as err:
                            print(err)
                            cookie_dialog_found = True
                            elements.append(
                                [site_nr, short_url, 0, 1, "% Error during visit", "", "", "", "", "", "", "", ""])

                    del model_dialog
                if not cookie_dialog_found:
                    elements.append(
                        [site_nr, short_url, 0, 1, "& No cookie dialog found during visit", "", "", "", "", "", "", "", ""])

                # print('Saving page source')
                # html = driver.execute_script("""return arguments[0].innerText;""", driver.find_element(By.XPATH, "/*"))
                html = driver.find_element(By.XPATH, "/*").text
                with open(BASE_PATH + str(site_nr).zfill(7) + "°" + short_url + ".txt",
                          "w") as file:
                    file.write(html)

                # Save screenshot
                driver.save_screenshot(
                    BASE_PATH + str(site_nr).zfill(7) + "°" + short_url + ".png")

                # Save cookies
                cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                print('({}) {}: Vooraf {} cookies   {:.2f}-{:.2f}'.format(site_nr, url, len(cookies_temp),
                                                                          time.time() - this_url_start,
                                                                          time.time() - start_time))
                write_cookies(0, visit_id, cookies_temp, cookies2, short_url)
                visits.append([site_nr, short_url, 0, visit_id, driver.current_url, len(cookies_temp)])

                print("----{:2f}s-----Finished URL visit--".format(time.time() - this_url_start))

                '''with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(short_url[0] + "-" + short_url[1] + " Normal visit\n")'''

                # Visit accept button
                if element_css:
                    if iframe_element_css:
                        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, iframe_element_css))

                    css_element = driver.find_elements(By.CSS_SELECTOR, element_css)
                    for element in css_element:
                        if element.text == element_text:
                            element.get_attribute("style")
                            text_color = element.value_of_css_property('color')
                            background_color = element.value_of_css_property('background-color')
                            width = element.value_of_css_property('width')
                            height = element.value_of_css_property('height')
                            font_size = element.value_of_css_property('font-size')
                            location = str(c.location).replace("{", "").replace("}", "")
                            if not isinstance(location, str):
                                location = ""
                                print("##################################""")

                            elements.append(
                                [site_nr, short_url, 1, 1, element_text, element_css, iframe_element_css, location, text_color,
                                 background_color, width, height, font_size])

                            element.click()
                            time.sleep(3)

                            # Save cookies
                            cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                            print(
                                '({}) {}: Na accept {} cookies   {:.2f}-{:.2f}'.format(site_nr, url, len(cookies_temp),
                                                                                       time.time() - this_url_start,
                                                                                       time.time() - start_time))
                            write_cookies(1, visit_id, cookies_temp, cookies2, short_url)
                            visits.append([site_nr, short_url, 1, visit_id, driver.current_url, len(cookies_temp)])

                            # Save screenshot
                            driver.save_screenshot(
                                BASE_PATH + str(site_nr).zfill(7) + "°" + short_url + "°" + str(1) + ".png")

                            # print('Added element to elements', end="")
                            # print([site_nr, short_url, 1, 1, element_text, element_css, iframe_element_css])

                    if iframe_element_css:
                        driver.switch_to.parent_frame()

        except TimeoutError as err:
            print('({}) http://{} Timeout      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                      time.time() - this_url_start,
                                                                                      time.time() - start_time,
                                                                                      type(err)))
            fails.value += fails.value
        except WebDriverException as err:
            print("({}){} WebDriverException     {:.2f}-{:.2f} (Error type {} - Message)".format(site_nr, url,
                                                                                                 time.time() - this_url_start,
                                                                                                 time.time() - start_time,
                                                                                                 type(err), err.msg))
            fails.value += fails.value
        except Exception as err:
            print('({}) http://{} Error      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                    time.time() - this_url_start,
                                                                                    time.time() - start_time,
                                                                                    type(err)))
            print(err)
            fails.value += fails.value

        finally:
            driver.quit()
            killtree(os.getpid())

    if visit_type > 0 and not visit:
        for r in res:
            if r[2] == visit_type and r[3] == 0:
                visit = True
                #elements.append([r[0], r[1], r[2], 1, r[4], r[5], r[6]])
                try:
                    driver.get("http://" + url)
                    time.sleep(5)

                    visits.append([site_nr, short_url, visit_type, visit_id, driver.current_url, -1])

                    if r[6]:
                        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, r[6]))

                    css_elements = driver.find_elements(By.CSS_SELECTOR, r[5])
                    for element in css_elements:
                        if element.text == r[4]:
                            print('element reached')
                            elements.append(
                                [r[0], r[1], r[2], 1, r[4], r[5], r[6], r[7], r[8], r[9],
                                 r[10], r[11], r[12]])

                            element.click()

                            # Save cookies
                            cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                            print('({}) {}: Na {} {} cookies   {:.2f}-{:.2f}'.format(site_nr, url, type_text.lower(),
                                                                                     len(cookies_temp),
                                                                                     time.time() - this_url_start,
                                                                                     time.time() - start_time))
                            write_cookies(visit_type, visit_id, cookies_temp, cookies2, short_url)
                            visits.append([site_nr, short_url, visit_type, visit_id, driver.current_url, len(cookies_temp)])

                            # Save screenshot
                            driver.save_screenshot(
                                BASE_PATH + str(site_nr).zfill(7) + "°" + short_url + "°" + str(visit_type) + ".png")

                            #elements.append([r[0], r[1], r[2], 1, r[4], r[5], r[6]])
                            # print('Added element to elements', end="")
                            # print([r[0], r[1], r[2], 1, r[4], r[5], r[6]])

                    if r[6]:
                        driver.switch_to.parent_frame()


                except TimeoutError as err:
                    print('({}) http://{} Timeout      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                              time.time() - this_url_start,
                                                                                              time.time() - start_time, type(err)))
                    fails.value += 1
                except WebDriverException as err:
                    print("({}){} WebDriverException     {:.2f}-{:.2f} (Error type {} - Message)".format(site_nr, url,
                                                                                                         time.time() - this_url_start,
                                                                                                         time.time() - start_time,
                                                                                                         type(err), err.msg))
                    fails.value += 1
                except Exception as err:
                    print('({}) http://{} Error      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                            time.time() - this_url_start,
                                                                                            time.time() - start_time, type(err)))
                    print(err)
                    fails.value += 1

                finally:
                    driver.quit()
                    killtree(os.getpid())

    '''with lock:
        if has_clicked:
            #cookies.append([visit_id, visit_type, site_nr, short_url, url, cookies_voor, cookies_na, method, button])
            if visit_type == 0:
                cookies.append([site_nr, short_url, "click accept", method, button, None, cookies_voor, cookies_na, None])
            elif visit_type == 1:
                cookies.append([site_nr, short_url, "click decline", method, None, button, cookies_voor, None, cookies_na])
        else:
            #cookies.append([visit_id, visit_type, site_nr, short_url, url, cookies_voor, cookies_na, method, button])
            cookies.append([site_nr, short_url, None, None, None, None, cookies_voor, None, None])'''

    # driver.close()
    # driver.quit()

    if visit:
        print('URL visit finished - ' + short_url)
    else:
        print('URL skipped - ' + short_url)


# i = thread number
def session_checker(lock, thread_nr, runn, stop, now, urls, fails, cookies, cookies2, previously_visited_nrs, visits,
                    do_not_visit, elements):
    # lock file, thread_nr,
    print('Starting session ' + str(thread_nr))

    while fails.value < nr_fails and not stop.value:  # keep this running until stop signal
        with runn:
            j = runn.value
            runn.value += 1
            if runn.value > len(urls):
                stop.value = True
                print('Starting visit of last website, finishing visits')

        site_nr = int(urls[j - 1][0])
        short_url = urls[j - 1][1]
        visit_type = int(urls[j - 1][2])

        visit_url = check_response(short_url)

        if not visit_url:
            print("({}) http://{} has been skipped because it can't be reached".format(site_nr, short_url))
            elements.append(
                [site_nr, short_url, 0, 1, "# Skipped because can't be reached", "", "", "", "", "", "", "", ""])
            visits.append([site_nr, short_url, visit_type, -1, "can't be reached", -1])
        else:
            visit_id = random.randrange(1, 100000000)
            p = Process(target=session, args=(
                lock, stop, now, short_url, visit_url, visit_type, site_nr, fails, cookies, cookies2, visit_id, visits,
                elements, urls, runn))
            p.start()

            start = time.time()
            while time.time() - start <= TIMEOUT:
                if not p.is_alive():
                    p.terminate()
                    p.join()
                    # The process are done, break now.
                    break
                time.sleep(1)  # Just to avoid hogging the CPU

            else:
                if p.is_alive():
                    # We only enter this if we didn't 'break' above.
                    print("({}) http://{} Session timed out after {:.2f} seconds".format(site_nr, short_url,
                                                                                         time.time() - start))
                    fails.value += 1
                    with lock:
                        # p.terminate()
                        # killing all children
                        killtree(os.getpid())
                        # Writing empty row in database
                        # cookies.append([0, visit_type, site_nr, short_url, "", -1, -1, "", ""])
                        cookies.append(
                            [site_nr, short_url, "error", None, None, None, None, None, None])
                        visits.append([site_nr, short_url, visit_type, visit_id, "error", -1])
                else:
                    p.terminate()
                    p.join()

    print('Ending session ' + str(thread_nr))


if __name__ == '__main__':
    freeze_support()  # needed for Windows
    main()
