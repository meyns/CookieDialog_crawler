import datetime
import json
import random
import sqlite3
import pprint

from selenium import webdriver
# import seleniumwire.undetected_chromedriver as webdriver
# from seleniumwire import webdriver
# import undetected_chromedriver as uc
# from selenium_stealth import stealth
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
import shutil
import socket
import chromedriver_autoinstaller
import psutil
import PySimpleGUI as sg
import logging
import traceback
from PIL import Image

# print('Setting up global fixed variables')
from simpletransformers.classification import ClassificationModel
from simpletransformers.config.model_args import ClassificationArgs

from sys import platform

if platform == "linux" or platform == "linux2":
    ML_dir_cookie_dialog = "./model_dialog"  # Ubuntu
    ML_dir_buttons = "./model_buttons"  # Ubuntu
    BASE_PATH = "./data/"  # Ubuntu
    PATH_CHROME = "./chromedriver"
elif platform == "darwin":
    # OS X
    pass
elif platform == "win32":
    ML_dir_cookie_dialog = "D:/temp/cookie-notice selector backup/output/"
    ML_dir_buttons = "D:/temp/cookie-notice selector/output 10epochs 2e05 64bs 10 evalbs 64maxsl/"
    BASE_PATH = "d:/temp/Selenium-model/"
    PATH_CHROME = "./chromedriver.exe"

# PATH_CHROME = './chromedriver.exe'
PATH_FIREFOX = 'D:/Documenten/Maarten/Open universiteit/VAF/selenium/geckodriver.exe'
# PATH_EDGE
# PATH_SAFARI

# ML_dir_cookie_dialog = "Selenium/output_dialog"
# ML_dir_buttons = "Selenium/output_buttons"

# BASE_PATH = "Selenium/" # voor docker run

TIMEOUT = 100
TYPES_WEBSITES = []  # BE NL COM EU ORG COM
BROWSER = "chrome"  # firefox,chrome,edge,safari
RUNS = 1  # how many repeats
nr_fails = 100  # How many fails before restarting processes

button_dict = {"ACCEPT": 1,
               "DECLINE": 2,
               "MODIFY": 3,
               "SAVE": 4
               }

MAKE_SCREENSHOTS = True

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"]


def main():
    # chromedriver_autoinstaller.install()  # only used for docker run
    LIMIT_CPU = Value('i', 1)

    if platform == "linux" or platform == "linux2":
        LIMIT_CPU.value = 16
        kill_processes()
    elif platform == "win32":
        LIMIT_CPU.value = 1

    logging.basicConfig(level=logging.ERROR)
    transformers_logger = logging.getLogger("simpletransformers")
    transformers_logger.setLevel(logging.ERROR)

    # print(os.listdir())

    # Setting up folders
    if not os.path.exists(BASE_PATH):
        os.mkdir(BASE_PATH)

    if not os.path.exists(BASE_PATH + 'screenshots'):
        os.mkdir(BASE_PATH + 'screenshots')

    if not os.path.exists(BASE_PATH + 'cookies.db'):
        import populate_database

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
    # cursor.execute('SELECT site_nr, sitename, element_type, result FROM elements where visited == 0 or (result == "# Skipped because can\'t be reached" and site_nr > 320000) ORDER BY element_type DESC')
    cursor.execute(
        'SELECT site_nr, sitename, element_type, result FROM elements where visited == 0 ORDER BY element_type DESC')
    res = cursor.fetchall()
    conn.close()

    urls = Manager().list([])

    for r in res:
        urls.append(list(r))
    print("First 100 sites to visit:")
    print(urls[:100])
    print(f"Number of sites left to visit: {len(urls)}")

    now = time.time()

    cookies = Manager().list([])
    cookies2 = Manager().list([])
    visits = Manager().list([])
    elements = Manager().list([])
    redirects = Manager().list([])
    all_requests = Manager().list([])
    predictions = Manager().list([])
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
    pause = Value('b', False)
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
    while not stop.value and LIMIT_CPU.value > 0:
        print('Starting while loop')
        print("Limit CPU: " + str(LIMIT_CPU.value))

        # Start GUI thread
        n = Process(target=gui_thread, args=(stop, pause, fails, LIMIT_CPU))
        n.start()

        # start writing process
        o = Process(target=writing_thread,
                    args=(lock, urls, stop, pause, fails, cookies, cookies2, visits, do_not_visit, elements, redirects,
                          all_requests, predictions))
        o.start()

        fails.value = 0

        # start browser sessions
        for thread_nr in range(LIMIT_CPU.value):
            p = Process(target=session_checker, args=(
                lock, thread_nr, runn, stop, pause, now, urls, fails, cookies, cookies2, previously_visited_nrs, visits,
                do_not_visit, elements, LIMIT_CPU, redirects, all_requests, predictions))
            session_ch.append(p)
            p.start()
            time.sleep(60 / LIMIT_CPU.value)  # To make sure not all threads start at the same time

        # wait until > nr_fails fails or stop value
        while fails.value < nr_fails and not stop.value:  # and LIMIT_CPU.value/2 > len(p.is_alive() for p in session_ch):
            if not n.is_alive():
                n.join()
                del n
                n = Process(target=gui_thread, args=(stop, pause, fails, LIMIT_CPU))
                n.start()
            if not o.is_alive():
                o.join()
                del o
                o = Process(target=writing_thread,
                            args=(lock, urls, stop, pause, fails, cookies, cookies2, visits, do_not_visit, elements,
                                  redirects, all_requests, predictions))
                o.start()
            while pause.value == True:
                time.sleep(1)
            time.sleep(1)

        if stop.value:
            print("------------------------------Stop signal received going to shut down")
        else:
            print("------------------------------Fails reached trying to shut down")

        # nr_fails fails have occurred, or we want to stop -> wait until all running processes timeout
        start = time.time()
        while time.time() - start <= TIMEOUT + 30:
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

        try:
            if platform == "linux" or platform == "linux2":
                kill_processes()
                print("Cleaning temp files")
                for root, dirs, files in os.walk('/tmp/'):
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
        except:
            pass

    print('One last write')
    print(cookies)
    print(cookies2)
    print(visits)
    print(elements)
    writing(lock, urls, stop, cookies, cookies2, visits, do_not_visit, elements, redirects, all_requests, predictions)

    print('Main thread finished')
    killtree(os.getpid(), including_parent=True)
    kill_processes()


# Interceptor voor seleniumwire (deze items worden geblokkeerd)
def interceptor(request):
    # Block PNG, JPG, JPEG, GIF, ICO and MP3
    # if request.path.endswith('.png') or request.path.endswith('.jpg') or request.path.endswith('.gif') or request.path.endswith('.jpeg') or request.path.endswith('.ico') or request.path.endswith('.mp3'):
    if request.path.endswith('.png') or request.path.endswith('.jpg') or request.path.endswith(
            '.gif') or request.path.endswith('.jpeg') or request.path.endswith('.ico') or request.path.endswith(
        '.mp3'):
        request.abort()


# alle directe descendants namen
def all_direct_descendants(element):
    return element.find_elements(By.XPATH, "./*")


# Finetune element: Zo dicht mogelijk bij de code van het dialoog komen
# Als het over een normaal element gaat, dan zoeken naar eerste iframe eronder
# Als het over een iframe element gaat, dan niets doen
def finetune_element(element, type_ifr='normal'):
    # print('Finetuning')
    try:
        try:
            iframe = element.find_element(By.XPATH, './/iframe')
        except:
            iframe = False

        if element.tag_name == 'iframe':
            pass
        elif iframe and type_ifr == 'normal':
            # print(iframe)
            element = iframe
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
        print(traceback.format_exc())
        print(err)

    return element


def volgende_laag(element, driver):
    new_candidates = []
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
                new_candidates.append(volgende_laag(e, driver))
        else:
            for e_dict in children[5]:
                e = e_dict['element']
                if len(e.get_attribute('innerHTML')) > 50 and e.size['width'] > 0 and e.size['height'] > 0:
                    highest_z_score = e_dict['zIndex']
                    highest_element = finetune_element(e)

                    # print(highest_element.is_displayed())
                    '''print("z-score candidate: " + str(highest_z_score) + "-" + highest_element.tag_name + "-" + str(
                        highest_element.size['width'])) # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
                    new_candidates.append(highest_element)
                else:
                    # print('pass')
                    pass
    except Exception as err:
        print(traceback.format_exc())
        print(err)

    return new_candidates


def highest_z_index(driver, do_layers):
    new_candidates = []
    try:
        z_indexes = driver.execute_script("""return \
          Array.from(document.querySelectorAll('*'))\
            .map((el) => ({zIndex: Number(getComputedStyle(el).zIndex), element: el }))\
            .filter(({ zIndex }) => !isNaN(zIndex))\
            .filter(({ zIndex }) => (zIndex > 0))\
            .sort((r1, r2) => r2.zIndex - r1.zIndex)\
            .slice(0, 30);\
          console.table(data);""")  # sorted list of z-indexes
        # pprint.pprint(z_indexes)
        # time.sleep(0.05)
        # print(z_indexes)
        if z_indexes:
            if z_indexes[0]['zIndex'] > 0:
                do_layers = True
        for e_dict in z_indexes:
            element = e_dict['element']
            element = finetune_element(element)
            '''print(element.get_attribute('innerHTML'))
            print(element.size['width'])
            print(element.size['height'])
            print(element.tag_name)
            print('----------------')'''
            if (element.size['width'] > 10 or element.size['height'] > 10) and (
                    len(element.get_attribute('innerHTML')) > 50 or element.tag_name == "iframe"):
                '''print("highest z-score candidate: " + str(z_score) + "-" + element.tag_name + "-" + str(
                    element.size['width'])) # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
                new_candidates.append(element)
                # print('###############"""')
    except Exception as err:
        print(traceback.format_exc())
        print(err)

    return new_candidates


def get_active_element(driver):
    new_candidates = []
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
                new_candidates.append(element)
    except Exception as err:
        print(traceback.format_exc())
        print(err)

    return new_candidates


def candidate_filter(candidates):
    # Filter out elements that cannot act like a button
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
        print(traceback.format_exc())
        print(err)

    # Filter out elements that are a father of another element (or same element)
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

    return candidates


def adding_iframe(driver):
    new_candidates = []
    try:
        temp_elements = driver.find_elements(By.XPATH, '//iframe')
        if temp_elements:
            for element in temp_elements:
                if element.size['width'] > 10 and element.size['height'] > 10:
                    # print("i-frame candidate: " + element.tag_name + "-" + str(
                    #    element.size[
                    #        'width']))  # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))
                    new_candidates.append(element)
    except Exception as err:
        print(traceback.format_exc())
        print(err)

    return new_candidates


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


def gui_thread(stop, pause, fails, LIMIT_CPU):
    print('Starting gui thread')
    layout = [
        [sg.Button('Pause crawling'), sg.Button('Resume'), sg.Button('Stop crawling')],
        [sg.Text('', key='-TEXT-')],
        [sg.Text(size=(600, 600), key='-CPU-', background_color="black")]
    ]
    window = sg.Window('My Program', layout, size=(400, 400), finalize=True)

    start = time.time()
    count = 0.0
    count2 = 0
    pausebutton = False
    while fails.value < nr_fails and not stop.value:
        event, values = window.read(1)
        if event == 'Pause crawling':
            pausebutton = True
            pause.value = True
            window['-TEXT-'].update('Pause')
        if event == 'Resume':
            pausebutton = False
            pause.value = False
            window['-TEXT-'].update('')
        if event == 'Stop crawling':
            stop.value = True
            window['-TEXT-'].update('Gracefully shutting down')
        if event == sg.WIN_CLOSED:
            window.close()
            sys.exit()

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        line = "CPU " + str(cpu) + "% - RAM " + str(ram) + "% cpu " + str(LIMIT_CPU.value)
        line += ' count ' + str(count)

        if cpu > 70:
            line += " CPU WARNING"
            count2 = 0
        if ram > 70:
            line += " RAM WARNING"
            count2 = 0
        # Check if resource usage is too high, count 5 times and then stop program
        if ram > 90:
            count += 3  # RAM moet bijna direct gestopt worden
        elif cpu > 90:
            count += 1  # CPU maar stoppen na 10 counts
        elif count > 0:
            count -= 0.5
            count = round(count, 1)

        line += '\n'

        '''if pausebutton == False and count > 9:
            pause.value = True
            line += '\n' + ' CPU or RAM usage too high pausing threads'
        if pause.value == True and pausebutton == False and count <= 9:
            pause.value = False'''

        if count > 9:
            pause.value = False
            LIMIT_CPU.value -= 1
            fails.value = nr_fails
            line += ' CPU or RAM usage too high reducing CPU threads' + '\n'

        if count2 > 30 * 60:
            count2 = 0
            LIMIT_CPU.value += 1
            fails.value = nr_fails
            line += ' raising cpu limit not enough resources used last 30 min' + '\n'

        window['-CPU-'].update(line + window['-CPU-'].get())

        with open(BASE_PATH + "resources.txt", "a") as file:
            file.write(time.ctime() + " " + line)

        # Signal that threads need to be restarted (to be able to flush the tmp folder and keep nr of threads at max)
        if (time.time() - start > 60 * 60):  # 60s*60m = 1hour
            fails.value = nr_fails

        count2 += 1

        time.sleep(1)

    window.close()


def writing_thread(lock, urls, stop, pause, fails, cookies, cookies2, visits, do_not_visit, elements, redirects,
                   all_requests, predictions):
    print("Starting writing thread")
    while fails.value < nr_fails and not stop.value:
        time_slept = 0
        while fails.value < nr_fails and not stop.value and time_slept < 30:
            while pause.value:
                time.sleep(1)
            time.sleep(1)
            time_slept += 1
        if time_slept == 30:
            writing(lock, urls, stop, cookies, cookies2, visits, do_not_visit, elements, redirects, all_requests,
                    predictions)
    print('End writing thread')


def writing(lock, urls, stop, cookies, cookies2, visits, do_not_visit, elements, redirects, all_requests, predictions):
    # print('Locking cookie data')
    cookies_dupl = []
    cookies2_dupl = []
    visits_dupl = []
    elements_dupl = []
    redirects_dupl = []
    all_requests_dupl = []
    predictions_dupl = []

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
        if len(redirects) > 0:
            redirects_dupl = list(redirects)
            del redirects[:]
        if len(all_requests) > 0:
            all_requests_dupl = list(all_requests)
            del all_requests[:]
        if len(predictions) > 0:
            predictions_dupl = list(predictions)
            del predictions[:]

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
                # print(e)
                if len(e) == 7:
                    cursor.execute('INSERT OR IGNORE INTO elements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                   (e[0], e[1], e[2], e[3], e[4], e[5], e[6], "", "", "", "", "", "", "", "", ""))
                    cursor.execute(
                        'UPDATE elements SET visit_id = ?, visited = ?, result = ?, element_text = ? WHERE site_nr = ? and sitename = ? and element_type = ?',
                        (e[0], e[4], e[5], e[6], e[1], e[2], e[3]))
                elif len(e) == 6:
                    cursor.execute('INSERT OR IGNORE INTO elements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                   (e[0], e[1], e[2], e[3], e[4], e[5], "", "", "", "", "", "", "", "", "", ""))
                    cursor.execute(
                        'UPDATE elements SET visit_id = ?, visited = ?, result = ? WHERE site_nr = ? and sitename = ? and element_type = ?',
                        (e[0], e[4], e[5], e[1], e[2], e[3]))
                else:
                    cursor.execute('INSERT OR IGNORE INTO elements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                   (e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], e[12],
                                    e[13], e[14], e[15]))
                    cursor.execute(
                        'UPDATE elements SET visit_id = ?, visited = ?, result = ?, element_text = ?, element_css = ?, iframe_css = ?, '
                        'location_x = ?, location_y = ?, text_color = ?, background_color = ?, width = ?, height = ?, '
                        'font_size = ? WHERE site_nr = ? AND element_type = ?',
                        (
                        e[0], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], e[12], e[13], e[14], e[14], e[1], e[3]))
            cursor.execute('COMMIT')
            cursor.close()

        if len(redirects_dupl) > 0:
            # print('Writing to database file visits')
            cursor = conn.cursor()
            for r in redirects_dupl:
                cursor.execute('INSERT INTO redirects VALUES(?, ?, ?, ?, ?, ?)',
                               (r[0], r[1], r[2], r[3], r[4], r[5]))
            cursor.execute('COMMIT')
            cursor.close()

        if len(all_requests_dupl) > 0:
            # print('Writing to database file visits')
            cursor = conn.cursor()
            for a in all_requests_dupl:
                cursor.execute('INSERT INTO all_requests VALUES(?, ?, ?, ?, ?, ?)',
                               (a[0], a[1], a[2], a[3], a[4], a[5]))
            cursor.execute('COMMIT')
            cursor.close()

        if len(predictions_dupl) > 0:
            cursor = conn.cursor()
            for p in predictions_dupl:
                cursor.execute('INSERT INTO predictions VALUES(?,?,?,?,?)',
                               (p[0], p[1], p[2], p[3], p[4]))
            cursor.execute('COMMIT')
            cursor.close()

        conn.close()

    print('Finished writing to cookies files')


def kill_processes():
    global BROWSER
    # kill all chrome instances
    os.system("taskkill /f /im chromedriver.exe")
    os.system("taskkill /f /im operadriver.exe")
    os.system("taskkill /f /im geckodriver.exe")
    os.system("taskkill /f /im IEDriverServer.exe")
    if BROWSER == "chrome":
        os.system("taskkill /f /im Chrome.exe")
    if BROWSER == "firefox":
        os.system("taskkill /f /im Firefox.exe")
    os.system("taskkill /f /im GoogleCrashHandler.exe")


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


# Try the website if it is alive
def check_response2(url):
    try:
        socket.getaddrinfo(url, 80)
        response = url
    except:
        try:
            socket.getaddrinfo("www." + url, 80)
            response = "www." + url
        except:
            response = False
    # print(url + " -> " + str(response))
    return response


# writing to cookies variable
def write_cookies(before_after, visit_id, cookies_temp, cookies2, short_url, driver_time):
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
                if item == "expires":
                    expires = c["expires"]
                    if expires == -1:
                        list_temp[list_items.index(item)] = str(c[item])
                    else:
                        exp = expires - driver_time
                        delta = datetime.timedelta(minutes=round(exp / 60))
                        list_temp[list_items.index(item)] = str(delta)
                else:
                    # print(c[item])
                    list_temp[list_items.index(item)] = c[item]
        cookies2.append(list_temp)
        # print(list_temp)


# Haalt alle redirects op (werkt enkel met Selenium-wire)
def get_redirects(driver, visit_id, redirects, all_requests):
    for req in driver.requests:
        # print(req.response.headers)
        if not req.response is None:
            # print(req)
            location = req.response.headers.get("Location")  # If redirect then this is the to field
            # result = req.headers.get("Host") # From result
            if not location is None and req.response.headers.get(
                    "content-type") is None and req.response.status_code >= 300 and req.response.status_code < 400:
                # print(result)
                # print(req.response.status_code)
                # print(req.date)
                redirects.append(
                    [visit_id, req.response.status_code, req.date.strftime("%Y/%m/%d, %H:%M:%S"), req.url, location,
                     req.response.headers.get("content-type")])
            if not req.headers.get("referer") is None:
                if not req.response.status_code == 403 and not req.url.endswith(".woff2") and not req.url.endswith(
                        ".woff"):  # 403 = blocked and woff is font
                    all_requests.append([visit_id, req.response.status_code, req.date.strftime("%Y/%m/%d, %H:%M:%S"),
                                         req.headers.get("referer"), req.url, req.response.headers.get("content-type")])


# This is the session that visits the website
def session(lock, stop, start_time, short_url, url, visit_type, site_nr, fails, cookies, cookies2, visit_id, visits,
            elements, urls, runn, LIMIT_CPU, redirects, all_requests, thread_nr, predictions):
    print('')
    # pprint.pprint(list(urls))
    print(str(runn.value) + '-(' + str(site_nr) + '-' + str(
        visit_type) + ') Thread started ' + url + " - Visit_id: " + str(visit_id) + " - Visit_type: " + str(
        visit_type))
    this_url_start = time.time()

    if BROWSER == "chrome":
        options = webdriver.ChromeOptions()
    if BROWSER == "firefox":
        options = webdriver.FirefoxOptions()

    # Running headless makes the detection of selenium more likely
    # options.add_argument('--headless')  # headfull not working in docker
    # options.add_argument('--disable-gpu') # seleniumwire.undetected_chromedriver only works headfull
    # options.add_argument("--incognito")
    '''Incognito does not block third party cookies in combination with headless. Incognito + headfull does block the third party cookies'''

    options.add_argument('--disable-extensions')
    options.add_argument('--disable-cookie-encryption')  # ?
    # options.add_argument('--https_only_mode_enabled')
    options.page_load_strategy = 'normal'  # eager -> enkel DOM laden, normal -> alles laden
    options.add_argument(
        "user-agent=" + user_agents[visit_type])
    # ????    options.enable_mobile()
    # options.add_argument("--disable-notifications")
    # options.add_argument("--disable-geolocation")
    # options.add_argument("--disable-media-stream")
    # options.add_argument("--disable-infobars")
    options.add_argument("--log-level=3")
    # options.add_argument("--verbose")
    # options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--disable-automation")
    options.add_argument("enable-automation")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--use--fake-ui-for-media-stream")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--dns-prefetch-disable")
    # options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation": 1,
    #                                          "profile.managed_default_content_settings.images": 2})

    # Make detection of automation less likely
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('--useAutomationExtension=false')

    # This works only in headless for blocking images
    '''options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--blink-settings=loadsImagesAutomatically=false')'''
    options.add_argument('--disable-blink-features=AutomationControlled')

    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')

    capabilities = DesiredCapabilities.CHROME
    # capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}

    '''capabilities['chromeOptions'] = {"prefs": {#"profile.default_content_settings.cookies": 2#,
                                               #"intl.accept_languages": 'nl'
                                               }
                                     }'''
    capabilities['acceptSslCerts'] = True
    '''options.add_experimental_option("prefs", {#"profile.default_content_setting_values.geolocation": 1,
                                              #"profile.default_content_setting_values.cookies": 2,
                                              "profile.managed_default_content_setting_values.images": 2, #only works in headfull to block images
                                              "profile.managed_default_content_settings.images": 2,
                                              "profile.default_content_setting_values.notifications": 2,
                                              #"intl.accept_languages": 'nl, nl-NL'
                                              }
                                    )'''

    # Kan niet in combinatie met undetected chromedriver
    prefs = {  # "profile.default_content_setting_values.geolocation": 1,
        # "profile.default_content_setting_values.cookies": 2,
        # "profile.managed_default_content_setting_values.images": 2,  # only works in headfull to block images
        # "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "intl.accept_languages": 'nl, nl-NL'
    }
    options.add_experimental_option("prefs", prefs)

    # Disable javascript
    options.set_preference('javascript.enabled', False)

    # print('Opstart tijd driver: {:.2f}'.format(time.time() - this_thread_start))

    # Prepare variables
    has_clicked = False
    button = ""
    method = ""
    cookies_voor = None
    cookies_na = None
    # cookies_temp = []
    if visit_type == 1:
        type_text = "ACCEPT"
    elif visit_type == 2:
        type_text = "DECLINE"
    elif visit_type == 3:
        type_text = "MODIFY"
    elif visit_type == 4:
        type_text = "SAVE"

    # Dit werd gebruikt voor Selenium wire
    # ports = [9951, 9952, 9953, 9954, 9955, 9956, 9957, 9958, 9959, 9960, 9961, 9962, 9963, 9964, 9965, 9966, 9967, 9968, 9969, 9970, 9971, 9972, 9973, 9974, 9975, 9976, 9977, 9978, 9979, 9980, 9981]

    # Check database for entries
    with lock:
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM elements where site_nr == ? ORDER BY element_type ASC', (site_nr,))
        res = cursor.fetchall()
        conn.close()
        # print(res)

    # starting up webdriver
    if BROWSER == "chrome":
        driver = webdriver.Chrome(service=Service(PATH_CHROME), options=options, desired_capabilities=capabilities)
        # driver = webdriver.Chrome(service=Service(PATH_CHROME), options=options, desired_capabilities=capabilities, seleniumwire_options={'verify_ssl': False, 'backend': 'mitmproxy', 'mitmproxy_log_level': 'INFO', 'port': ports[thread_nr]})
        '''stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win64",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )'''  # Results in missing cookies
        # driver = uc.Chrome(se_subprocess=True)
    if BROWSER == "firefox":
        driver = webdriver.Firefox(service=Service(PATH_FIREFOX), options=options, desired_capabilities=capabilities)

    driver.set_window_size(1920, 1080)
    # driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    # driver.request_interceptor = interceptor # Voor Selenium-wire
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    #############################

    visit = False
    element_css = ""
    # if (res[0][3] == 0 and res[0][4] == 0) and visit_type == 0:
    if res[0][3] == 0 and visit_type == 0:
        visit = True
        try:
            driver_time = time.time()
            driver.get("http://" + url)
            # driver.get("https://nowsecure.nl/") # cloudflare test
            # driver.get("https://webscraping.pro/wp-content/uploads/2021/02/testresult2.html")
            # driver.get("https://bot.sannysoft.com/") # Automation test
            time.sleep(5)

            # Count the non ascii characters if more than 30% are non-ascii characters then skip this site (probably chinese)
            html = driver.find_element(By.XPATH, "/*").text
            ascii_count = html.encode("ascii", "ignore")  # Haalt alle normale letters uit de html
            if len(html) > 0 and len(ascii_count) / len(html) < 0.7:  # Check for empty html because can be iframe
                print(
                    str(site_nr) + "-" + short_url + " - Skipping url because more non-ascii letters than ascii letters (probably chinese website)")
                with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(str(site_nr) + "°" + short_url + " Skipped because unreadable\n")
                short_text = ''.join([x for i, x in enumerate(html.replace('\n', ' ')) if i < 1020])
                cookies.append(
                    [visit_id, site_nr, short_url, "# unraedable", None, None, None, None, None])
                elements.append(
                    [visit_id, site_nr, short_url, 0, 1, "# Skipped unreadable", short_text])
                visits.append([visit_id, site_nr, short_url, visit_type, "# unreadable", -1])

            # elif not get_status_code(driver, driver.current_url) == 200:
            #    print(str(site_nr) + "-" + short_url + " - Skipping url because not 200 status code")
            #    with open(BASE_PATH + "output.txt", "a") as file:
            #        file.write(str(site_nr) + "°" + short_url + " Skipped because not 200 status code\n")
            #    cookies.append(
            #        [visit_id, site_nr, short_url, "# no 200 response", None, None, None, None, None])
            #    elements.append(
            #        [visit_id, site_nr, short_url, 0, 1, "# Skipped no 200 response", "", "", "", "", "", "", "", "", "", ""])
            #    visits.append([visit_id, site_nr, short_url, visit_type, "no 200 response", -1])

            elif "ERR_" in html or "_ERR" in html or "Website Blocked" in html or "This site is blocked due" in html or "block.opendns.com" in driver.current_url or "Bot detection" in html or "DDoS protection by " in html:
                print(str(site_nr) + "-" + short_url + " - Skipping url because website blocked")
                with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(str(site_nr) + "°" + short_url + " Skipping url because website blocked or error\n")
                short_text = ''.join([x for i, x in enumerate(html.replace('\n', ' ')) if i < 1020])
                cookies.append(
                    [visit_id, site_nr, short_url, "# Website blocked or error", None, None, None, None, None])
                elements.append(
                    [visit_id, site_nr, short_url, 0, 1, "# Skipped website blocked or error", short_text])
                visits.append([visit_id, site_nr, short_url, visit_type, "# Website blocked", -1])
            else:
                #visits.append([visit_id, site_nr, short_url, visit_type, driver.current_url, -1])

                # Save cookies
                cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                print('({}) {}: Vooraf {} cookies   {:.2f}-{:.2f}'.format(site_nr, url, len(cookies_temp),
                                                                          time.time() - this_url_start,
                                                                          time.time() - start_time))
                write_cookies(0, visit_id, cookies_temp, cookies2, short_url, driver_time)
                # write_cookies(0, visit_id, cookies_temp, cookies2, short_url)
                visits.append([visit_id, site_nr, short_url, 0, driver.current_url, len(cookies_temp)])
                # get_redirects(driver, visit_id, redirects, all_requests) # Enkel voor Selenium-wire

                # Save screenshot
                if MAKE_SCREENSHOTS:
                    driver.save_screenshot(
                        BASE_PATH + "screenshots/" + str(site_nr).zfill(7) + "°" + short_url + ".png")

                do_layers = False

                candidates = []
                # print("----{:2f}s-----URL loaded--".format(time.time() - this_url_start))

                # print('Testing highest z_scores')
                candidates.extend(highest_z_index(driver, do_layers))
                print(f"Highest z-indexes: {len(candidates)}")
                # print("----{:2f}s-----Finished highest z-scores--".format(time.time() - this_url_start))

                if do_layers:
                    # print('Testing layers')
                    candidates.extend(
                        volgende_laag(driver.find_element(By.XPATH, "/*"), driver, candidates))  # root element
                    print(f"Do layers: {len(candidates)}")
                    # print("----{:2f}s-----Finished layers--".format(time.time() - this_url_start))
                else:
                    # print('Skipping layers, no z-scores')
                    pass

                # print('Adding iframe')
                candidates.extend(adding_iframe(driver))
                print(f"Adding iframes: {len(candidates)}")
                # print("----{:2f}s-----Finished iframes--".format(time.time() - this_url_start))

                # print('Testing active element')
                candidates.extend(get_active_element(driver))
                print(f"Adding active element: {len(candidates)}")
                # print("----{:2f}s-----Finished active element--".format(time.time() - this_url_start))

                # print('Filtering candidates {}'.format(len(candidates)))
                candidates = candidate_filter(candidates)
                print(f"Filtering candidates: {len(candidates)}")
                # print("----{:2f}s-----Finished filtering candidates--".format(time.time() - this_url_start))

                cookie_dialog_found = False
                if not candidates:
                    print("No candidates found")
                    pass

                else:
                    print('Processing candidates ' + str(len(candidates)))
                    model_dialog = ClassificationModel("xlmroberta", ML_dir_cookie_dialog, args={"silent": True},
                                                       use_cuda=False)
                    index = 0
                    # for index, c in enumerate(candidates):
                    while not cookie_dialog_found and index < len(candidates):
                        c = candidates[index]
                        index += 1
                        print('Saving cadidate ' + str(index))
                        try:
                            # print(c.size['width'])
                            # print(c.size['height'])
                            # print(c.get_attribute('outerHTML'))
                            iframe_element_css = ""
                            iframe_test = (c.tag_name == 'iframe')
                            if iframe_test:
                                # iframe = c
                                # Setting up CSS info for iframe element (only save when right iframe)
                                iframe_element_class = (c.get_attribute('class') or '')
                                if not iframe_element_class == '':
                                    iframe_element_class = "." + ".".join(
                                        iframe_element_class.split())
                                iframe_element_name = c.tag_name
                                iframe_element_id = (c.get_attribute('id') or '')
                                if not iframe_element_id == '':
                                    iframe_element_id = "#" + iframe_element_id

                                # print(c.tag_name)
                                driver.switch_to.frame(c)
                                time.sleep(0.5)
                                c = driver.find_element(By.XPATH, '/*')  # first child in iframe
                                c = finetune_element(c, 'iframe')
                                # print(f"Iframe text: {c.text}")

                            # text = driver.execute_script("""return arguments[0].innerText;""", c)
                            # text2 = c.get_attribute('innerHTML')
                            text3 = c.text
                            # print(text3)

                            try:
                                # check = isinstance(c.screenshot_as_png, str)
                                if (c.size['width'] > 10 or c.size['height'] > 10) and text3 and len(text3) >= 20:
                                    # Check for cookie dialog with trained model
                                    with lock:
                                        prediction_CD, raw_outputs = model_dialog.predict(
                                            [text3.lower().replace('\n', ' ').replace(';', ',')])

                                    print("Prediction made, result: {} - {}".format(prediction_CD[0], ''.join(
                                        [x for i, x in enumerate(text3.replace('\n', ' ')) if i < 124])))
                                    short_text = ''.join(
                                        [x for i, x in enumerate(text3.replace('\n', ' ')) if i < 1020])
                                    predictions.append(
                                        [visit_id, "cookie dialog", c.tag_name, short_text, prediction_CD[0]])

                                    if prediction_CD[0] == "True":
                                        cookie_dialog_found = True
                                        if MAKE_SCREENSHOTS:
                                            try:
                                                with open(BASE_PATH + "screenshots/" + str(site_nr).zfill(
                                                        7) + "°" + short_url + "°" + str(
                                                        index).zfill(2) + "°" + c.tag_name + "°element.png",
                                                          "wb") as file:
                                                    # print('Saved screenshot1')
                                                    file.write(c.screenshot_as_png)
                                                    # print('Saved screenshot2')
                                            except:
                                                print("Screenshot unsuccessful")
                                                img = Image.new("RGB", (1, 1), (255, 255, 255))
                                                img.save(BASE_PATH + "screenshots/" + str(site_nr).zfill(
                                                    7) + "°" + short_url + "°" + str(
                                                    index).zfill(2) + "°" + c.tag_name + "°element.png", "PNG")
                                        '''with open(BASE_PATH + str(site_nr).zfill(7) + "-" + short_url + "°" + str(
                                                index).zfill(2) + "°" + c.tag_name + "°element.txt", "w") as file:
                                            file.write(text3)
                                            # print('Saved txt file')'''

                                        c.get_attribute("style")
                                        text_color = c.value_of_css_property('color')
                                        background_color = c.value_of_css_property('background-color')
                                        width = c.value_of_css_property('width').replace('px', '')
                                        if width.isnumeric():
                                            width = int(width)
                                        height = c.value_of_css_property('height').replace('px', '')
                                        if height.isnumeric():
                                            height = int(height)
                                        font_size = c.value_of_css_property('font-size')
                                        try:
                                            location_x = int(c.location['x'])
                                            location_y = int(c.location['y'])
                                        except:
                                            location_x = ""
                                            location_y = ""

                                        if iframe_test:
                                            iframe_element_css = iframe_element_name + iframe_element_class + iframe_element_id
                                        else:
                                            iframe_element_css = ''

                                        short_text = ''.join(
                                            [x for i, x in enumerate(text3.replace('\n', ' ')) if i < 1020])

                                        # Add cookie dialog info to database
                                        elements.append(
                                            [visit_id, site_nr, short_url, visit_type, 1, "Normal visit", short_text,
                                             "",
                                             iframe_element_css, location_x, location_y, text_color, background_color,
                                             width, height, font_size])

                                        # Extract elements from cookie dialog:
                                        # print(c.text)
                                        # pprint.pprint(c.get_attribute('innerHTML'))
                                        # print("-------------------collecting children")
                                        cookie_elements = c.find_elements(By.XPATH,
                                                                          ".//button | .//a | .//span | .//svg")
                                        # pprint.pprint(elements)
                                        with lock:
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
                                                    prediction_B, raw_outputs2 = model_buttons.predict(
                                                        [text.lower().replace("\n", " ")])
                                                    print("Prediction made, result: {} - {}".format(prediction_B[0],
                                                                                                    ''.join(
                                                                                                        [x for index, x
                                                                                                         in
                                                                                                         enumerate(
                                                                                                             text.replace(
                                                                                                                 '\n',
                                                                                                                 ' '))
                                                                                                         if
                                                                                                         index < 124])))
                                                    predictions.append(
                                                        [visit_id, "button", el.tag_name, text, prediction_B[0]])

                                                    button_type = prediction_B[0]

                                                    if not button_type == "OTHER":
                                                        save_element_class = (el.get_attribute('class') or '')
                                                        if not save_element_class == '':
                                                            save_element_class = "." + ".".join(
                                                                el.get_attribute('class').split())
                                                        save_element_name = el.tag_name
                                                        save_element_text = el.text
                                                        '''save_element_id = (el.get_attribute('id') or '')
                                                        if not save_element_id == '':
                                                            save_element_id = "#" + save_element_id'''
                                                        save_element_id = ""

                                                        save_element_css = save_element_name + save_element_class + save_element_id

                                                        el.get_attribute("style")
                                                        text_color = el.value_of_css_property('color')
                                                        background_color = el.value_of_css_property('background-color')
                                                        width = el.value_of_css_property('width').replace('px', '')
                                                        if width.isnumeric():
                                                            width = int(width)
                                                        height = el.value_of_css_property('height').replace('px', '')
                                                        if height.isnumeric():
                                                            height = int(height)
                                                        font_size = el.value_of_css_property('font-size')
                                                        try:
                                                            location_x = int(el.location['x'])
                                                            location_y = int(el.location['y'])
                                                        except:
                                                            location_x = ""
                                                            location_y = ""

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
                                                        with open(BASE_PATH + "buttons.csv", 'a',
                                                                  encoding='utf-8') as file:
                                                            file.write(line_to_add + '\n')

                                                        # Writing to database all elements without OTHER
                                                        # [site nr, sitename, element_type, visited?, element_text, element_css]
                                                        elements.append(
                                                            [0, site_nr, short_url, button_dict[button_type], 0, "",
                                                             save_element_text, save_element_css,
                                                             iframe_element_css, location_x, location_y, text_color,
                                                             background_color, width, height, font_size])

                                                        # Add the new visits for detected buttons to url list. If list is too low then add to end of list
                                                        if not button_type == 'ACCEPT':
                                                            try:
                                                                urls.insert(runn.value + button_dict[
                                                                    button_type] * 2 + LIMIT_CPU.value,
                                                                            [site_nr, short_url,
                                                                             button_dict[button_type]])
                                                            except:
                                                                urls.append(
                                                                    [site_nr, short_url, button_dict[button_type]])
                                                        # print([site_nr, short_url, button_dict[button_type], 0, save_element_text, save_element_css, iframe_element_css])

                                            # print("-------------------elements printed")
                                            del model_buttons

                            except Exception as err:
                                print(traceback.format_exc())
                                print(err)
                                # elements.append(
                                # [visit_id, site_nr, short_url, 0, 1, "° Error during visit", "", "", "", "", "", "", "", "", "", ""])

                            try:
                                if iframe_test:
                                    driver.switch_to.parent_frame()
                                    # driver.switch_to.default_content()
                                    time.sleep(0.5)
                            except Exception as err:
                                print("Error while switching to parent frame")
                                pass

                        except Exception as err:
                            print(traceback.format_exc())
                            print(err)
                            cookie_dialog_found = True
                            short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
                            elements.append(
                                [visit_id, site_nr, short_url, visit_type, 1, "° Error during visit", short_text])

                    del model_dialog
                if not cookie_dialog_found:
                    elements.append(
                        [visit_id, site_nr, short_url, visit_type, 1, "No cookie dialog found during visit", ""])

                # print('Saving page source')
                # html = driver.execute_script("""return arguments[0].innerText;""", driver.find_element(By.XPATH, "/*"))
                # html = driver.find_element(By.XPATH, "/*").text
                '''with open(BASE_PATH + str(site_nr).zfill(7) + "°" + short_url + ".txt",
                          "w") as file:
                    file.write(html)'''

                '''with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(short_url[0] + "-" + short_url[1] + " Normal visit\n")'''

                # Visit accept button
                try:
                    if element_css:
                        if iframe_element_css:
                            element = driver.find_element(By.CSS_SELECTOR, iframe_element_css)
                            driver.switch_to.frame(element)
                            time.sleep(0.5)

                        css_elements = driver.find_elements(By.CSS_SELECTOR, element_css)
                        for element in css_elements:
                            if element.text == element_text:
                                element.get_attribute("style")
                                text_color = element.value_of_css_property('color')
                                background_color = element.value_of_css_property('background-color')
                                width = element.value_of_css_property('width').replace('px', '')
                                if width.isnumeric():
                                    width = int(width)
                                height = element.value_of_css_property('height').replace('px', '')
                                if height.isnumeric():
                                    height = int(height)
                                font_size = element.value_of_css_property('font-size')
                                '''location = str(c.location).replace("{", "").replace("}", "")
                                if not isinstance(location, str):
                                    location = ""
                                    print("##################################")'''
                                try:
                                    location_x = int(element.location['x'])
                                    location_y = int(element.location['y'])
                                except:
                                    location_x = ""
                                    location_y = ""

                                elements.append(
                                    [visit_id, site_nr, short_url, 1, 1, "Normal visit", element_text, element_css,
                                     iframe_element_css, location_x, location_y, text_color,
                                     background_color, width, height, font_size])

                                element.click()
                                time.sleep(5)

                                # Save cookies
                                cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                                print(
                                    '({}) {}: Na accept {} cookies   {:.2f}-{:.2f}'.format(site_nr, url,
                                                                                           len(cookies_temp),
                                                                                           time.time() - this_url_start,
                                                                                           time.time() - start_time))
                                write_cookies(1, visit_id, cookies_temp, cookies2, short_url, driver_time)
                                # write_cookies(1, visit_id, cookies_temp, cookies2, short_url)
                                visits.append([visit_id, site_nr, short_url, 1, driver.current_url, len(cookies_temp)])
                                # get_redirects(driver, visit_id, redirects, all_requests) # Enkel voor Selenium-wire

                                # Save screenshot
                                if MAKE_SCREENSHOTS:
                                    driver.save_screenshot(
                                        BASE_PATH + "screenshots/" + str(site_nr).zfill(
                                            7) + "°" + short_url + "°" + str(1) + ".png")

                                # print('Added element to elements', end="")
                                # print([site_nr, short_url, 1, 1, element_text, element_css, iframe_element_css])

                                break

                    '''try:
                        if iframe_element_css:
                            print("is this where the error occurs")
                            driver.switch_to.parent_frame()
                    except Exception as err:
                        # print("Error while switching to parent frame")
                        pass'''

                except Exception as err:
                    print(traceback.format_exc())
                    fails.value += 1
                    short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
                    elements.append(
                        [visit_id, site_nr, short_url, 1, 1, short_text])

        except TimeoutError as err:
            print('({}) http://{} Timeout      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                      time.time() - this_url_start,
                                                                                      time.time() - start_time,
                                                                                      type(err)))
            print(traceback.format_exc())
            fails.value += 1
            short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
            elements.append(
                [visit_id, site_nr, short_url, visit_type, 1, short_text])
        except WebDriverException as err:
            print("({}) http://{} WebDriverException     {:.2f}-{:.2f} (Error type {} - Message)".format(site_nr, url,
                                                                                                         time.time() - this_url_start,
                                                                                                         time.time() - start_time,
                                                                                                         type(err),
                                                                                                         err.msg))
            print(traceback.format_exc())
            fails.value += 1
            short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
            elements.append(
                [visit_id, site_nr, short_url, visit_type, 1, short_text])
        except Exception as err:
            print('({}) http://{} Error      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                    time.time() - this_url_start,
                                                                                    time.time() - start_time,
                                                                                    type(err)))
            print(traceback.format_exc())
            # print(err)
            fails.value += 1
            short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
            elements.append(
                [visit_id, site_nr, short_url, visit_type, 1, short_text])

        finally:
            driver.quit()
            killtree(os.getpid())

    if visit_type > 0 and not visit:
        for r in res:
            if r[3] == visit_type and r[4] == 0:
                visit = True
                try:
                    print('visiting site')
                    driver_time = time.time()
                    driver.get("http://" + url)
                    time.sleep(5)

                    visits.append([visit_id, site_nr, short_url, visit_type, driver.current_url, -1])

                    if r[8]:
                        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, r[8]))
                        time.sleep(0.5)

                    css_elements = driver.find_elements(By.CSS_SELECTOR, r[7])
                    # print(css_elements)
                    clicked = False
                    for n, element in enumerate(css_elements):
                        # print(element.text)
                        # print(r[6])
                        if element.text == r[6]:
                            # print('element reached')
                            element.click()
                            time.sleep(5)
                            clicked = True

                            # Save cookies
                            cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                            print('({}) {}: Na {} {} cookies   {:.2f}-{:.2f}'.format(site_nr, url, type_text.lower(),
                                                                                     len(cookies_temp),
                                                                                     time.time() - this_url_start,
                                                                                     time.time() - start_time))
                            elements.append(
                                [visit_id, r[1], r[2], r[3], 1, "Normal visit", r[6], r[7], r[8], r[9],
                                 r[10], r[11], r[12], r[13], r[14], r[15]])
                            write_cookies(visit_type, visit_id, cookies_temp, cookies2, short_url, driver_time)
                            # write_cookies(visit_type, visit_id, cookies_temp, cookies2, short_url)
                            visits.append(
                                [visit_id, site_nr, short_url, visit_type, driver.current_url, len(cookies_temp)])
                            # get_redirects(driver, visit_id, redirects, all_requests) # Enkel voor Selenium-wire

                            # Save screenshot
                            if MAKE_SCREENSHOTS:
                                driver.save_screenshot(
                                    BASE_PATH + "screenshots/" + str(site_nr).zfill(7) + "°" + short_url + "°" + str(
                                        visit_type) + ".png")

                            break

                    '''if r[7]:
                        driver.switch_to.parent_frame()'''

                    if not clicked:
                        elements.append(
                            [visit_id, r[1], r[2], r[3], 1, "# css_element not found", r[6], r[7], r[8], r[9],
                             r[10], r[11], r[12], r[13], r[14], r[15]])
                        print(f"Element not found on site {r[2]}")

                except TimeoutError as err:
                    print('({}) http://{} Timeout      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                              time.time() - this_url_start,
                                                                                              time.time() - start_time,
                                                                                              type(err)))
                    print(traceback.format_exc())
                    fails.value += 1
                    elements.append(
                        [visit_id, site_nr, short_url, visit_type, 1, "° Timeout error during visit", r[6], r[7], r[8],
                         r[9], r[10], r[11], r[12], r[13], r[14], r[15]])
                except WebDriverException as err:
                    print("({}){} WebDriverException     {:.2f}-{:.2f} (Error type {} - Message)".format(site_nr, url,
                                                                                                         time.time() - this_url_start,
                                                                                                         time.time() - start_time,
                                                                                                         type(err),
                                                                                                         err.msg))
                    print(traceback.format_exc())
                    fails.value += 1
                    elements.append(
                        [visit_id, site_nr, short_url, visit_type, 1, "° WebdriverException during visit", r[6], r[7],
                         r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15]])
                except Exception as err:
                    print('({}) http://{} Error      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                            time.time() - this_url_start,
                                                                                            time.time() - start_time,
                                                                                            type(err)))
                    print(traceback.format_exc())
                    # print(err)
                    fails.value += 1
                    elements.append(
                        [visit_id, site_nr, short_url, visit_type, 1, "° Other error during visit", r[6], r[7], r[8],
                         r[9], r[10], r[11], r[12], r[13], r[14], r[15]])

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
    driver.quit()

    if visit:
        print('URL visit finished - ' + short_url)
    else:
        print('URL skipped - ' + short_url)


# i = thread number
def session_checker(lock, thread_nr, runn, stop, pause, now, urls, fails, cookies, cookies2, previously_visited_nrs,
                    visits,
                    do_not_visit, elements, LIMIT_CPU, redirects, all_requests, predictions):
    # lock file, thread_nr,
    print('Starting session ' + str(thread_nr))

    while fails.value < nr_fails and not stop.value:  # keep this running until stop signal
        if pause.value:
            print(f'Pausing thread {thread_nr}')
        while pause.value:
            time.sleep(1)

        with runn:
            j = runn.value
            runn.value += 1

        site_nr = int(urls[j - 1][0])
        short_url = urls[j - 1][1]
        visit_type = int(urls[j - 1][2])

        visit_url = check_response2(short_url)

        visit_id = random.randrange(1, 1000000000000)

        if not visit_url:
            print("({}) http://{} has been skipped because it can't be reached".format(site_nr, short_url))
            # cookies.append(
            #    [visit_id, site_nr, short_url, "error", None, None, None, None, None])
            elements.append(
                [visit_id, site_nr, short_url, 0, 1, "# Skipped because can't be reached", "", "", "", "", "", "", "",
                 "", "", ""])
            visits.append([visit_id, site_nr, short_url, visit_type, "# can't be reached", -1])
        else:
            p = Process(target=session, args=(
                lock, stop, now, short_url, visit_url, visit_type, site_nr, fails, cookies, cookies2, visit_id, visits,
                elements, urls, runn, LIMIT_CPU, redirects, all_requests, thread_nr, predictions))
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
                        # cookies.append(
                        #    [visit_id, site_nr, short_url, "error", None, None, None, None, None])
                        visits.append([visit_id, site_nr, short_url, visit_type, "° Timeout", -1])
                        elements.append([visit_id, site_nr, short_url, visit_type, 1, "° Timeout during session", ""])
                else:
                    p.terminate()
                    p.join()

        if pause.value:
            print(f'Pausing thread {thread_nr}')
        while pause.value:
            time.sleep(1)

        if runn.value > len(urls):
            stop.value = True
            print('Last website reached, finishing threads')

    print('Ending session ' + str(thread_nr))


if __name__ == '__main__':
    freeze_support()  # needed for Windows
    main()
