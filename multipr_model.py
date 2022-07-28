import datetime
import json
import random
import sqlite3
import pprint

from selenium import webdriver
#import seleniumwire.undetected_chromedriver as webdriver
#from seleniumwire import webdriver
#import undetected_chromedriver as uc
#from selenium_stealth import stealth
from selenium.common.exceptions import *
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
import time
import sys
from selenium.webdriver.chrome.service import Service
from multiprocessing import Process, Value, cpu_count, Queue, freeze_support, Lock, Manager, Pool, Value
import os
import shutil
import socket
import psutil
import PySimpleGUI as sg
import logging
import traceback
from PIL import Image
import chromedriver_autoinstaller

from simpletransformers.classification import ClassificationModel
from simpletransformers.config.model_args import ClassificationArgs

from sys import platform

# Laad system variabelen voor run naargelang de OS
if platform == "linux" or platform == "linux2":
    ML_dir_cookie_dialog = "./model_dialog"
    ML_dir_buttons = "./model_buttons"
    BASE_PATH = "./data/"
    PATH_CHROME = "./chromedriver"
elif platform == "darwin":
    # OS X
    pass
elif platform == "win32":
    ML_dir_cookie_dialog = "D:/temp/cookie-notice selector backup/output/"
    ML_dir_buttons = "D:/temp/cookie-notice selector/output 10epochs 2e05 64bs 10 evalbs 64maxsl/"
    BASE_PATH = "d:/temp/Selenium-model/"
    PATH_CHROME = "./chromedriver.exe"

TIMEOUT = 100
BROWSER = "chrome"  # firefox,chrome,edge,safari (enkel Chrome voorlopig)
nr_fails = 100 # How many fails before restarting all processes

button_dict = {"ACCEPT": 1,
               "DECLINE": 2,
               "MODIFY": 3,
               "SAVE": 4
               }

MAKE_SCREENSHOTS = True

user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"]


# Hoofdthread die alle subthreads voorbereidt en start
def main():
    #chromedriver_autoinstaller.install()  # only used for docker run
    LIMIT_CPU = Value('i', 1)

    # Setting up cpu threads volgens de OS
    if platform == "linux" or platform == "linux2":
        LIMIT_CPU.value = 16
        kill_processes()
    elif platform == "win32":
        LIMIT_CPU.value = 1

    # Voorbereiding voor machine learning models, anders toont het te veel data in console
    logging.basicConfig(level=logging.ERROR)
    transformers_logger = logging.getLogger("simpletransformers")
    transformers_logger.setLevel(logging.ERROR)

    # Setting up folders
    if not os.path.exists(BASE_PATH):
        os.mkdir(BASE_PATH)

    if not os.path.exists(BASE_PATH + 'screenshots'):
        os.mkdir(BASE_PATH + 'screenshots')

    if not os.path.exists(BASE_PATH + 'cookies.db'):
        import populate_database # This import runs the populate_database.py file

    # Read in to visit sites from populated database
    print('Reading in database')
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    cursor.execute('SELECT site_nr, sitename, element_type, result FROM elements '
                   'where visited == 0 ORDER BY element_type DESC')
    res = cursor.fetchall()
    conn.close()

    # Initialiseer de lijst van te bezoeken websites met het type
    urls = Manager().list([])
    for r in res:
        urls.append(list(r))
    print("First 100 sites to visit:")
    print(urls[:100])
    print(f"Number of sites left to visit: {len(urls)}")

    # Setting up global variables for database
    cookies = Manager().list([])
    cookies2 = Manager().list([])
    visits = Manager().list([])
    elements = Manager().list([])
    redirects = Manager().list([])
    all_requests = Manager().list([])
    predictions = Manager().list([])
    lock = Lock()

    session_ch = []

    # Setting up global variables
    runn = Value('i', 1)
    stop = Value('b', False)
    pause = Value('b', False)
    fails = Value('i', 0)

    # start processes
    now = time.time()
    while not stop.value and LIMIT_CPU.value > 0:
        print('Starting while loop')
        print("Limit CPU: " + str(LIMIT_CPU.value))

        # Start GUI thread
        n = Process(target=gui_thread, args=(stop, pause, fails, LIMIT_CPU))
        n.start()

        # start writing process
        o = Process(target=writing_thread,
                    args=(lock, urls, stop, pause, fails, cookies, cookies2, visits, elements, redirects, all_requests, predictions))
        o.start()

        fails.value = 0

        # start browser sessions
        for thread_nr in range(LIMIT_CPU.value):
            p = Process(target=session_checker, args=(
                lock, thread_nr, runn, stop, pause, now, urls, fails, cookies, cookies2, visits,
                elements, LIMIT_CPU, redirects, all_requests, predictions))
            session_ch.append(p)
            p.start()
            time.sleep(60 / LIMIT_CPU.value)  # To make sure not all threads start at the same time

        # wait until > nr_fails fails or stop value
        while fails.value < nr_fails and not stop.value:
            if not n.is_alive():
                n.join()
                del n
                n = Process(target=gui_thread, args=(stop, pause, fails, LIMIT_CPU))
                n.start()
            if not o.is_alive():
                o.join()
                del o
                o = Process(target=writing_thread,
                    args=(lock, urls, stop, pause, fails, cookies, cookies2, visits, elements, redirects, all_requests, predictions))
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

        # Cleaning up lingering processes and tmp folder
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
    writing(lock, urls, stop, cookies, cookies2, visits, elements, redirects, all_requests, predictions)

    print('Main thread finished')
    killtree(os.getpid(), including_parent=True)
    kill_processes()
    print("Cleaning temp files")
    for root, dirs, files in os.walk('/tmp/'):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


# Interceptor voor seleniumwire (deze items worden geblokkeerd) (wordt nu niet gebruikt)
def interceptor(request):
    # Block PNG, JPG, JPEG, GIF, ICO and MP3
    #if request.path.endswith('.png') or request.path.endswith('.jpg') or request.path.endswith('.gif') or request.path.endswith('.jpeg') or request.path.endswith('.ico') or request.path.endswith('.mp3'):
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
    try:
        try: # Check for iframes
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
                if len(chi) == 0:  # List is empty: done
                    last_element = True
                    break
                elif len(chi) == 1: # List contains 1 child: go to child
                    element = chi[0]
                    # print(element)
                    chi = element.find_elements(By.XPATH, "./*")
                else: # List contains 2 children: go to child if the other child is empty
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


# Controleer z-indexen van de de volgende laag
def volgende_laag(element, driver):
    new_candidates = []
    try:
        children = driver.execute_script("return \
                  Array.from(arguments[0].children)\
                    .map((el) => ({zIndex: Number(getComputedStyle(el).zIndex), element: el }))\
                    .filter(({ zIndex }) => !isNaN(zIndex))\
                    .filter(({ zIndex }) => (zIndex > 0))\
                    .sort((r1, r2) => r2.zIndex - r1.zIndex)\
                    .slice(0, 10);\
                  console.table(data);", element)
        if not children:  # Er zijn geen kinderen met een z-index herhaal dan met alle kinderen
            children = all_direct_descendants(element)
            for e in children:
                new_candidates.append(volgende_laag(e, driver))
        else: # Er zijn kinderen controleer de kinderen op validiteit
            for e_dict in children[5]:
                e = e_dict['element']
                if len(e.get_attribute('innerHTML')) > 50 and e.size['width'] > 0 and e.size['height'] > 0:
                    highest_z_score = e_dict['zIndex']
                    highest_element = finetune_element(e)
                    '''print("z-score candidate: " + str(highest_z_score) + "-" + highest_element.tag_name + "-" + str(
                        highest_element.size['width'])) # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
                    new_candidates.append(highest_element)
                else:
                    pass
    except Exception as err:
        print(traceback.format_exc())
        print(err)

    return new_candidates


# Neem de hoogste z-index over het algemeen
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
        if z_indexes: # Als er ten minste 1 z-index is geef dan aan dat de kinderen gedaan moeten worden
            if z_indexes[0]['zIndex'] > 0:
                do_layers = True
        for e_dict in z_indexes:
            element = e_dict['element']
            element = finetune_element(element)
            if (element.size['width'] > 10 or element.size['height'] > 10) and (
                    len(element.get_attribute('innerHTML')) > 50 or element.tag_name == "iframe"):
                '''print("highest z-score candidate: " + str(z_score) + "-" + element.tag_name + "-" + str(
                    element.size['width'])) # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
                new_candidates.append(element)
    except Exception as err:
        print(traceback.format_exc())
        print(err)

    return new_candidates


# Haal het actieve element op van de webpagina
def get_active_element(driver):
    new_candidates = []
    try:
        element = driver.execute_script("return document.activeElement")
        element = finetune_element(element)
        if element.size['width'] > 10 and element.size['height'] > 10 and len(
                element.get_attribute('innerHTML')) > 50:
            '''print("Active element: " + element.tag_name + "-" + str(
                element.size['width']))  # + "-" + highest_element.get_attribute('outerHTML').replace("\n", " "))'''
            new_candidates.append(element)
    except Exception as err:
        print(traceback.format_exc())
        print(err)

    return new_candidates


# Filter out candidates that cannot act like a button or are parent of another element
def candidate_filter(candidates):
    # Filter out elements that cannot act like a button
    try:
        for index, c in reversed(list(enumerate(candidates))):
            text = c.text
            if c.tag_name in ["style", "ul", "il", "a", "svg", "button"]:  # Element that can't be a cookie dialog
                # print('Candidate popped = ' + c.tag_name)
                candidates.pop(index)
            elif c.tag_name == 'iframe':  # iframes soieso meenemen
                pass
            elif len(text) < 50: # Te kleine tekst niet meenemen
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

# Voeg alle iframes toe
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


# Haal status code op van de website (werkt enkel met Seleniuwire)
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


# Start GUI thread
# Regelt pause/herstart en geeft aan om de crawler te stoppen
# Regelt de CPU threads als de belasting te hoog wordt (of te laag)
def gui_thread(stop, pause, fails, LIMIT_CPU):
    print('Starting gui thread')
    # Set up layout
    layout = [
        [sg.Button('Pause crawling'), sg.Button('Resume'), sg.Button('Stop crawling')],
        [sg.Text('', key='-TEXT-')],
        [sg.Text(size=(600, 600), key='-CPU-', background_color="black")]
    ]
    window = sg.Window('My Program', layout, size=(400, 400), finalize=True)

    start = time.time()
    count = 0.0 # Houdt de te hoge belasing bij
    count2 = 0 # Houdt de te lage belasting bij
    while fails.value < nr_fails and not stop.value:
        event, values = window.read(1)
        if event == 'Pause crawling':
            pause.value = True
            window['-TEXT-'].update('Pause')
        if event == 'Resume':
            pause.value = False
            window['-TEXT-'].update('')
        if event == 'Stop crawling':
            stop.value = True
            window['-TEXT-'].update('Gracefully shutting down')
        if event == sg.WIN_CLOSED:
            window.close()
            sys.exit()

        # Laadt de variabelen
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

        # Check als belasting te hoog is, houdt telling bij om te kunnen stoppen (1x te hoge belasting is geen probleem)
        if ram > 90: # Te hoge RAM belasting na 3 counts stoppen
            count += 4
        elif cpu > 90: # Te hoge CPU belasting maar stoppen na 10 counts
            count += 1
        elif count > 0: # Telling afbouwen als terug normaal
            count -= 0.5
            count = round(count, 1)

        line += '\n'

        if count > 9: # CPU threads afbouwen bij te lang te hoge belasting en herstarten
            pause.value = False
            LIMIT_CPU.value -= 1
            fails.value = nr_fails
            line += ' CPU or RAM usage too high reducing CPU threads' + '\n'

        if count2 > 30 * 60: # CPU threads opbouwen bij 30min te lage belasting en herstarten
            count2 = 0
            LIMIT_CPU.value += 1
            fails.value = nr_fails
            line += ' raising cpu limit not enough resources used last 30 min' + '\n'

        window['-CPU-'].update(line + window['-CPU-'].get())

        with open(BASE_PATH + "resources.txt", "a") as file:
            file.write(time.ctime() + " " + line)
        
        # Crawler herstarten na 60min om lege threads te herstarten en tmp folder te resetten
        if (time.time() - start > 60*60): # 60s*60m = 1hour
            fails.value = nr_fails

        count2 += 1

        time.sleep(1)

    window.close()


# Hulpthread om database proces periodisch te starten
def writing_thread(lock, urls, stop, pause, fails, cookies, cookies2, visits, elements, redirects, all_requests, predictions):
    print("Starting writing thread")
    while fails.value < nr_fails and not stop.value:
        time_slept = 0
        while fails.value < nr_fails and not stop.value and time_slept < 30:
            while pause.value:
                time.sleep(1)
            time.sleep(1)
            time_slept += 1
        if time_slept == 30: # Na 30s uitschrijven naar database
            writing(lock, urls, stop, cookies, cookies2, visits, elements, redirects, all_requests, predictions)
    print('End writing thread')


# Database process
def writing(lock, urls, stop, cookies, cookies2, visits, elements, redirects, all_requests, predictions):
    # print('Locking cookie data')
    # Globale variabelen ophalen en resetten (met globale lock)
    cookies2_dupl = []
    visits_dupl = []
    elements_dupl = []
    redirects_dupl = []
    all_requests_dupl = []
    predictions_dupl = []
    with lock:
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

        # Schrijf naar cookie tabel in database
        if len(cookies2_dupl) > 0:
            # print('Writing to database file cookies')
            cursor = conn.cursor()
            for c in cookies2_dupl:
                cursor.execute('INSERT INTO cookies VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12], c[13],
                                c[14], c[15], c[16]))
            cursor.execute('COMMIT')
            cursor.close()

        # Schrijf naar visits tabel in database
        if len(visits_dupl) > 0:
            # print('Writing to database file visits')
            cursor = conn.cursor()
            for v in visits_dupl:
                cursor.execute('INSERT INTO visits VALUES(?, ?, ?, ?, ?, ?)',
                               (v[0], v[1], v[2], v[3], v[4], v[5]))
            cursor.execute('COMMIT')
            cursor.close()

        # Schrijf naar elements tabel in database (als lengte 7 of 6 is dan enkel die waarden updaten)
        if len(elements_dupl) > 0:
            # print('Writing to database file elements')
            cursor = conn.cursor()
            for e in elements_dupl:
                #print(e)
                if len(e) == 7:
                    # Insert or ignore om te schrijven ook als er nog geen lijn is met die waarden
                    cursor.execute('INSERT OR IGNORE INTO elements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                   (e[0], e[1], e[2], e[3], e[4], e[5], e[6], "", "", "", "", "", "", "", "", ""))
                    # Update als er al een lijn is met die waarden
                    cursor.execute('UPDATE elements SET visit_id = ?, visited = ?, result = ?, element_text = ? WHERE site_nr = ? and sitename = ? and element_type = ?',
                        (e[0], e[4], e[5], e[6], e[1], e[2], e[3]))
                elif len(e) == 6:
                    cursor.execute('INSERT OR IGNORE INTO elements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                   (e[0], e[1], e[2], e[3], e[4], e[5], "", "", "", "", "", "", "", "", "", ""))
                    cursor.execute('UPDATE elements SET visit_id = ?, visited = ?, result = ? WHERE site_nr = ? and sitename = ? and element_type = ?',
                        (e[0], e[4], e[5], e[1], e[2], e[3]))
                else:
                    cursor.execute('INSERT OR IGNORE INTO elements VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                   (e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], e[12], e[13], e[14], e[15]))
                    cursor.execute('UPDATE elements SET visit_id = ?, visited = ?, result = ?, element_text = ?, element_css = ?, iframe_css = ?, '
                                   'location_x = ?, location_y = ?, text_color = ?, background_color = ?, width = ?, height = ?, '
                                   'font_size = ? WHERE site_nr = ? AND element_type = ?',
                                    (e[0], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], e[12], e[13], e[14], e[14], e[1], e[3]))
            cursor.execute('COMMIT')
            cursor.close()

        # Schrijf naar redirects database (werd enkel gebruikt met Seleniumwire)
        if len(redirects_dupl) > 0:
            # print('Writing to database file visits')
            cursor = conn.cursor()
            for r in redirects_dupl:
                cursor.execute('INSERT INTO redirects VALUES(?, ?, ?, ?, ?, ?)',
                               (r[0], r[1], r[2], r[3], r[4], r[5]))
            cursor.execute('COMMIT')
            cursor.close()

        # Schrijf naar requests database (werd enkel gebruikt met Seleniumwire)
        if len(all_requests_dupl) > 0:
            # print('Writing to database file visits')
            cursor = conn.cursor()
            for a in all_requests_dupl:
                cursor.execute('INSERT INTO all_requests VALUES(?, ?, ?, ?, ?, ?)',
                               (a[0], a[1], a[2], a[3], a[4], a[5]))
            cursor.execute('COMMIT')
            cursor.close()

        # Scjrokf naar predictions database
        if len(predictions_dupl) > 0:
            cursor = conn.cursor()
            for p in predictions_dupl:
                cursor.execute('INSERT INTO predictions VALUES(?,?,?,?,?)',
                               (p[0], p[1], p[2], p[3], p[4]))
            cursor.execute('COMMIT')
            cursor.close()

        conn.close()

    print('Finished writing to cookies files')


# Kill alle processen die nog achter gebleven zijn
def kill_processes():
    global BROWSER
    # kill all chrome instances
    os.system("taskkill /f /im chromedriver.exe")
    os.system("taskkill /f /im operadriver.exe")
    os.system("taskkill /f /im geckodriver.exe")
    os.system("taskkill /f /im IEDriverServer.exe")
    if BROWSER == "chrome":
        os.system("taskkill /f /im Chrome.exe")
    '''if BROWSER == "firefox":
        os.system("taskkill /f /im Firefox.exe")'''


# Kill alle kinderen van dit process, eventueel met de parent erbij
def killtree(pid, including_parent=False):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        print("Killing child: {}".format(child.pid))
        child.kill()

    if including_parent:
        print("Killing parent: {}".format(parent.pid))
        parent.kill()

    
# Check als de website leeft (met en zonder www.) met een simpele request (geeft naam van site terug als antwoordt)
def check_response(url):
    try:
        socket.getaddrinfo(url, 80)
        response = url
    except:
        try:
            socket.getaddrinfo("www." + url, 80)
            response = "www." + url
        except:
            response = False
    return response
    

# Schrijft naar de cookies variabele
def write_cookies(before_after, visit_id, cookies_temp, cookies2, short_url, driver_time):
    list_items = ["visit_id", "before_after", "short_url", "domain", "expires", "httpOnly", "name", "path", "priority",
                  "sameParty", "sameSite",
                  "secure", "session", "size", "sourcePort", "sourceScheme", "value"] # Alle mogelijke velden van de cookies
    # pprint.pprint(cookies_temp)
    for c in cookies_temp:
        list_temp = [visit_id, before_after, short_url, "", 0.0, None, "", "", "", None, "", None, None, 0, 0, "", ""] # Lege variabele waarden voor cookies
        for item in list_items:
            if item in c:
                if item == "expires": # Vertaalt de expiry int naar een tijdseenheid
                    expires = c["expires"]
                    if expires == -1:
                        list_temp[list_items.index(item)] = str(c[item])
                    else:
                        exp = expires - driver_time
                        delta = datetime.timedelta(minutes=round(exp / 60))
                        list_temp[list_items.index(item)] = str(delta)
                else:
                    list_temp[list_items.index(item)] = c[item]
        cookies2.append(list_temp)
        # print(list_temp)

# Haalt alle redirects op (werkt enkel met Seleniumwire)
def get_redirects(driver, visit_id, redirects, all_requests):
    for req in driver.requests:
        #print(req.response.headers)
        if not req.response is None:
            #print(req)
            location = req.response.headers.get("Location") # If redirect then this is the to field
            #result = req.headers.get("Host") # From result
            if not location is None and req.response.headers.get("content-type") is None and req.response.status_code >= 300 and req.response.status_code < 400:
                #print(result)
                #print(req.response.status_code)
                #print(req.date)
                redirects.append([visit_id, req.response.status_code, req.date.strftime("%Y/%m/%d, %H:%M:%S"), req.url, location, req.response.headers.get("content-type")])
            if not req.headers.get("referer") is None:
                if not req.response.status_code == 403 and not req.url.endswith(".woff2") and not req.url.endswith(".woff"): # 403 = blocked and woff is font
                    all_requests.append([visit_id, req.response.status_code, req.date.strftime("%Y/%m/%d, %H:%M:%S"), req.headers.get("referer"), req.url, req.response.headers.get("content-type")])


# Bezoekt de website en voert alle acties uit
def session(lock, stop, start_time, short_url, url, visit_type, site_nr, fails, cookies, cookies2, visit_id, visits,
            elements, urls, runn, LIMIT_CPU, redirects, all_requests, thread_nr, predictions):
    print('')
    #pprint.pprint(list(urls))
    print(str(runn.value) + '-(' + str(site_nr) + '-' + str(visit_type) + ') Thread started ' + url + " - Visit_id: " + str(visit_id) + " - Visit_type: " + str(
        visit_type))
    this_url_start = time.time()

    if BROWSER == "chrome":
        options = webdriver.ChromeOptions()
    '''if BROWSER == "firefox":
        options = webdriver.FirefoxOptions()'''

    # Setting up browser variables
    #options.add_argument('--headless')  # headfull werkt niet in docker, headfull is gemakkelijker detecteerbaar, Seleniumwire en undetected_chromedriver werkt enkel headfull
    #options.add_argument('--disable-gpu')
    #options.add_argument("--incognito")
    '''Incognito does not block third party cookies in combination with headless. Incognito + headfull does block the third party cookies'''

    options.add_argument('--disable-extensions')
    options.add_argument('--disable-cookie-encryption')  # ?
    options.page_load_strategy = 'normal'  # eager -> enkel DOM laden, normal -> alles laden
    options.add_argument(
        "user-agent=" + user_agents[visit_type])
    options.add_argument("--log-level=3")
    options.add_argument("--disable-automation")
    options.add_argument("enable-automation")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--use--fake-ui-for-media-stream")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--dns-prefetch-disable")

    # Make detection of automation less likely
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('--useAutomationExtension=false')
    options.add_argument('--disable-blink-features=AutomationControlled')

    # This works only in headless for blocking images -> niet gebruikt toont dan minder cookies
    '''options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--blink-settings=loadsImagesAutomatically=false')'''

    # Vermindert het tonen van errors
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    capabilities = DesiredCapabilities.CHROME
    capabilities['acceptSslCerts'] = True
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "intl.accept_languages": 'nl, nl-NL'
    }
    options.add_experimental_option("prefs", prefs)

    # Laadt de betekenis van de visit_type
    if visit_type == 1:
        type_text = "ACCEPT"
    elif visit_type == 2:
        type_text = "DECLINE"
    elif visit_type == 3:
        type_text = "MODIFY"
    elif visit_type == 4:
        type_text = "SAVE"

    # Check database if entries for this visit is present
    with lock:
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM elements where site_nr == ? ORDER BY element_type ASC', (site_nr,))
        res = cursor.fetchall()
        conn.close()

    # starting up webdriver
    if BROWSER == "chrome":
        driver = webdriver.Chrome(service=Service(PATH_CHROME), options=options, desired_capabilities=capabilities)
        # Startup for stealth driver
        '''stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win64",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )''' # Results in missing cookies
    '''if BROWSER == "firefox":
        driver = webdriver.Firefox(service=Service(PATH_FIREFOX), options=options, desired_capabilities=capabilities)'''

    driver.set_window_size(1920, 1080)
    driver.set_script_timeout(10)
    #driver.request_interceptor = interceptor # Werd gebruikt voor Selenium-wire
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") # Vermindert detectie als bot

    #############################

    visit = False
    element_css = ""

    # Initiele bezoek van website
    if res[0][3] == 0 and visit_type == 0:
        visit = True
        try:
            driver_time = time.time()
            driver.get("http://" + url)
            time.sleep(5)

            # Count the non ascii characters if more than 30% are non-ascii characters then skip this site (probably chinese)
            html = driver.find_element(By.XPATH, "/*").text
            ascii_count = html.encode("ascii", "ignore") # Haalt alle normale letters uit de html
            if len(html) > 0 and len(ascii_count)/len(html) < 0.7: # Check for empty html because can be iframe
                print(str(site_nr) + "-" + short_url + " - Skipping url because more non-ascii letters than ascii letters (probably chinese website)")
                with open(BASE_PATH + "output.txt", "a") as file:
                    file.write(str(site_nr) + "°" + short_url + " Skipped because unreadable\n")
                short_text = ''.join([x for i, x in enumerate(html.replace('\n', ' ')) if i < 1020])
                cookies.append(
                        [visit_id, site_nr, short_url, "# unraedable", None, None, None, None, None])
                elements.append(
                    [visit_id, site_nr, short_url, 0, 1, "# Skipped unreadable", short_text])
                visits.append([visit_id, site_nr, short_url, visit_type, "# unreadable", -1])

            # Haalt status code op (werkt enkel met Seleniumwire)
            #elif not get_status_code(driver, driver.current_url) == 200:
            #    print(str(site_nr) + "-" + short_url + " - Skipping url because not 200 status code")
            #    with open(BASE_PATH + "output.txt", "a") as file:
            #        file.write(str(site_nr) + "°" + short_url + " Skipped because not 200 status code\n")
            #    cookies.append(
            #        [visit_id, site_nr, short_url, "# no 200 response", None, None, None, None, None])
            #    elements.append(
            #        [visit_id, site_nr, short_url, 0, 1, "# Skipped no 200 response", "", "", "", "", "", "", "", "", "", ""])
            #    visits.append([visit_id, site_nr, short_url, visit_type, "no 200 response", -1])

            # Check als error aanwezig door welke reden dan ook
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
            else: # Normale visit
                # Save cookies
                cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                print('({}) {}: Vooraf {} cookies   {:.2f}-{:.2f}'.format(site_nr, url, len(cookies_temp),
                                                                          time.time() - this_url_start,
                                                                          time.time() - start_time))
                write_cookies(0, visit_id, cookies_temp, cookies2, short_url, driver_time)
                visits.append([visit_id, site_nr, short_url, 0, driver.current_url, len(cookies_temp)])
                #get_redirects(driver, visit_id, redirects, all_requests) # Enkel voor Selenium-wire

                # Save screenshot
                if MAKE_SCREENSHOTS:
                    driver.save_screenshot(
                        BASE_PATH + "screenshots/" + str(site_nr).zfill(7) + "°" + short_url + ".png")

                do_layers = False

                # Haalt alle candidaten op voor de cookie dialoog
                candidates = []
                # print("----{:2f}s-----URL loaded--".format(time.time() - this_url_start))

                # print('Testing highest z_scores')
                candidates.extend(highest_z_index(driver, do_layers))
                print(f"Highest z-indexes: {len(candidates)}")
                # print("----{:2f}s-----Finished highest z-scores--".format(time.time() - this_url_start))

                if do_layers:
                    # print('Testing layers')
                    candidates.extend(volgende_laag(driver.find_element(By.XPATH, "/*"), driver, candidates))  # root element
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

                # Als candidaat gevonden doe voorspelling, anders gewoon stoppen
                cookie_dialog_found = False
                if not candidates:
                    print("No candidates found")
                    pass

                else:
                    print('Processing candidates ' + str(len(candidates)))
                    # Laadt model voor voorspellingen cookie dialoog
                    model_dialog = ClassificationModel("xlmroberta", ML_dir_cookie_dialog, args={"silent": True},
                                                       use_cuda=False)

                    # Alle candidaten overlopen, voorspelling doen en als cookie dialoog gevonden dan stoppen
                    index = 0
                    while not cookie_dialog_found and index < len(candidates):
                        c = candidates[index]
                        index += 1
                        print('Saving cadidate ' + str(index))
                        try:
                            # Test op iframe, dan erin gaan en informatie ervan alvast opslaan
                            iframe_element_css = ""
                            iframe_test = (c.tag_name == 'iframe')
                            if iframe_test:
                                #iframe = c
                                # Setting up CSS info for iframe element (only save when right iframe)
                                iframe_element_class = (c.get_attribute('class') or '')
                                if not iframe_element_class == '':
                                    iframe_element_class = "." + ".".join(
                                        iframe_element_class.split())
                                iframe_element_name = c.tag_name
                                iframe_element_id = (c.get_attribute('id') or '')
                                if not iframe_element_id == '':
                                    iframe_element_id = "#" + iframe_element_id

                                driver.switch_to.frame(c)
                                time.sleep(0.5)
                                c = driver.find_element(By.XPATH, '/*')  # Get first child in iframe
                                c = finetune_element(c, 'iframe')


                            # Bezoek iframe, doe voorspelling en zoek en save buttons
                            CD_text = c.text
                            try:
                                if (c.size['width'] > 10 or c.size['height'] > 10) and CD_text and len(CD_text) >= 20:
                                    # Check for cookie dialog with trained model
                                    with lock:
                                        prediction_CD, raw_outputs = model_dialog.predict(
                                            [CD_text.lower().replace('\n', ' ').replace(';', ',')])

                                    print("Prediction made, result: {} - {}".format(prediction_CD[0], ''.join(
                                        [x for i, x in enumerate(CD_text.replace('\n', ' ')) if i < 124])))
                                    short_text = ''.join(
                                        [x for i, x in enumerate(CD_text.replace('\n', ' ')) if i < 1020])

                                    # Add basic cookie dialog info to database
                                    predictions.append([visit_id, "cookie dialog", c.tag_name, short_text, prediction_CD[0]])

                                    if prediction_CD[0] == "True":
                                        cookie_dialog_found = True
                                        if MAKE_SCREENSHOTS:
                                            try:
                                                with open(BASE_PATH + "screenshots/" + str(site_nr).zfill(7) + "°" + short_url + "°" + str(
                                                          index).zfill(2) + "°" + c.tag_name + "°element.png", "wb") as file:
                                                    # print('Saved screenshot1')
                                                    file.write(c.screenshot_as_png)
                                                    # print('Saved screenshot2')
                                            except:
                                                print("Screenshot unsuccessful")
                                                img = Image.new("RGB", (1, 1), (255, 255, 255))
                                                img.save(BASE_PATH + "screenshots/" + str(site_nr).zfill(7) + "°" + short_url + "°" + str(
                                                          index).zfill(2) + "°" + c.tag_name + "°element.png", "PNG")

                                        # Bereidt alle stijl informatie voor, voor de database
                                        c.get_attribute("style")
                                        text_color = c.value_of_css_property('color')
                                        background_color = c.value_of_css_property('background-color')
                                        width = c.value_of_css_property('width').replace('px','')
                                        if width.isnumeric():
                                            width = int(width)
                                        height = c.value_of_css_property('height').replace('px','')
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

                                        short_text = ''.join([x for i, x in enumerate(text3.replace('\n', ' ')) if i < 1020])

                                        # Add cookie dialog info to database
                                        elements.append([visit_id, site_nr, short_url, visit_type, 1, "Normal visit", short_text, "",
                                                        iframe_element_css, location_x, location_y, text_color, background_color, width, height, font_size])

                                        # Get elements for buttons in CD
                                        cookie_elements = c.find_elements(By.XPATH,
                                                                          ".//button | .//a | .//span | .//svg")
                                        with lock:
                                            all_texts = []
                                            # Laadt model voor button classifier in
                                            model_buttons = ClassificationModel("xlmroberta", ML_dir_buttons,
                                                                                args={"silent": True},
                                                                                use_cuda=False)
                                            for el in cookie_elements:
                                                text = el.text

                                                if len(text) > 0 and text not in all_texts: # Check als nog niet voorgekomen en tekst bevat
                                                    all_texts.append(text)

                                                    # Check elements for buttons with trained model
                                                    prediction_B, raw_outputs2 = model_buttons.predict(
                                                        [text.lower().replace("\n", " ")])
                                                    print("Prediction made, result: {} - {}".format(prediction_B[0],
                                                                ''.join([x for index, x in enumerate(text.replace('\n', ' ')) if index < 124])))
                                                    predictions.append([visit_id, "button", el.tag_name, text, prediction_B[0]])

                                                    # Save all buttons die geen OTHER zijn naar database
                                                    button_type = prediction_B[0]
                                                    if not button_type == "OTHER":
                                                        # Bereidt stijl informatie voor, voor de database
                                                        save_element_class = (el.get_attribute('class') or '')
                                                        if not save_element_class == '':
                                                            save_element_class = "." + ".".join(
                                                                el.get_attribute('class').split())
                                                        save_element_name = el.tag_name
                                                        save_element_text = el.text
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

                                                        # Info to use for ACCEPT visit
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


                                                        # Writing to database all elements without OTHER
                                                        elements.append([0, site_nr, short_url, button_dict[button_type], 0, "",
                                                                         save_element_text, save_element_css,
                                                                         iframe_element_css, location_x, location_y, text_color, background_color, width, height, font_size])

                                                        # Add the new visits for detected buttons to url list. If list is too short to add then add to end of list
                                                        if not button_type == 'ACCEPT':
                                                            try:
                                                                urls.insert(runn.value + button_dict[button_type] * 2 + LIMIT_CPU.value,
                                                                            [site_nr, short_url, button_dict[button_type]])
                                                            except:
                                                                urls.append([site_nr, short_url, button_dict[button_type]])

                                            # Machine learning model ontladen om geheugen vrij te maken
                                            del model_buttons

                            except Exception as err:
                                print(traceback.format_exc())
                                print(err)

                            try:
                                if iframe_test:
                                    driver.switch_to.parent_frame()
                                    time.sleep(0.5)
                            except Exception as err:
                                print("Error while switching to parent frame")
                                pass

                        except Exception as err: # Get error and write to database
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

                # Visit accept button with same session as initial visit with information that was saved
                try:
                    if element_css:
                        if iframe_element_css:
                            element = driver.find_element(By.CSS_SELECTOR, iframe_element_css)
                            driver.switch_to.frame(element)
                            time.sleep(0.5)

                        css_elements = driver.find_elements(By.CSS_SELECTOR, element_css)
                        for element in css_elements:
                            if element.text == element_text:
                                # Bereidt stijl informatie voor, voor de database
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
                                try:
                                    location_x = int(element.location['x'])
                                    location_y = int(element.location['y'])
                                except:
                                    location_x = ""
                                    location_y = ""

                                # Add element to database
                                elements.append(
                                    [visit_id, site_nr, short_url, 1, 1, "Normal visit", element_text, element_css, iframe_element_css, location_x, location_y, text_color,
                                     background_color, width, height, font_size])

                                element.click()
                                time.sleep(5)

                                # Save cookies after clicking
                                cookies_temp = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                                print(
                                    '({}) {}: Na accept {} cookies   {:.2f}-{:.2f}'.format(site_nr, url, len(cookies_temp),
                                                                                           time.time() - this_url_start,
                                                                                           time.time() - start_time))
                                write_cookies(1, visit_id, cookies_temp, cookies2, short_url, driver_time)
                                visits.append([visit_id, site_nr, short_url, 1, driver.current_url, len(cookies_temp)])
                                #get_redirects(driver, visit_id, redirects, all_requests) # Enkel voor Selenium-wire

                                # Save screenshot
                                if MAKE_SCREENSHOTS:
                                    driver.save_screenshot(
                                        BASE_PATH + "screenshots/" + str(site_nr).zfill(7) + "°" + short_url + "°" + str(1) + ".png")

                                break

                except Exception as err: # Get error and write to database
                    print(traceback.format_exc())
                    fails.value += 1
                    short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
                    elements.append(
                        [visit_id, site_nr, short_url, 1, 1, short_text])

        except TimeoutError as err: # Get error and write to database
            print('({}) http://{} Timeout      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                      time.time() - this_url_start,
                                                                                      time.time() - start_time,
                                                                                      type(err)))
            print(traceback.format_exc())
            fails.value += 1
            short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
            elements.append(
                                [visit_id, site_nr, short_url, visit_type, 1, short_text])
        except WebDriverException as err: # Get error and write to database
            print("({}) http://{} WebDriverException     {:.2f}-{:.2f} (Error type {} - Message)".format(site_nr, url,
                                                                                                 time.time() - this_url_start,
                                                                                                 time.time() - start_time,
                                                                                                 type(err), err.msg))
            print(traceback.format_exc())
            fails.value += 1
            short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
            elements.append(
                                [visit_id, site_nr, short_url, visit_type, 1, short_text])
        except Exception as err: # Get error and write to database
            print('({}) http://{} Error      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                    time.time() - this_url_start,
                                                                                    time.time() - start_time,
                                                                                    type(err)))
            print(traceback.format_exc())
            fails.value += 1
            short_text = ''.join([x for i, x in enumerate(str(err).replace('\n', ' ')) if i < 1020])
            elements.append(
                                [visit_id, site_nr, short_url, visit_type, 1, short_text])

        finally: # Kuis driver op, en kill alle kinderen van deze thread
            driver.quit()
            killtree(os.getpid())

    # Voor 2de bezoek met andere button types
    if visit_type > 0 and not visit:
        for r in res:
            if r[3] == visit_type and r[4] == 0:
                visit = True
                try:
                    # Bezoek de pagina
                    print('visiting site')
                    driver_time = time.time()
                    driver.get("http://" + url)
                    time.sleep(5)

                    if r[8]: # Als cookie dialoog in iframe was ga eerst iframe binnen
                        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, r[8]))
                        time.sleep(0.5)

                    # Zoek element in de pagina/iframe
                    css_elements = driver.find_elements(By.CSS_SELECTOR, r[7])
                    clicked = False
                    for n, element in enumerate(css_elements):
                        if element.text == r[6]:
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
                            visits.append([visit_id, site_nr, short_url, visit_type, driver.current_url, len(cookies_temp)])

                            # Save screenshot
                            if MAKE_SCREENSHOTS:
                                driver.save_screenshot(
                                    BASE_PATH + "screenshots/" + str(site_nr).zfill(7) + "°" + short_url + "°" + str(visit_type) + ".png")

                            break
                        
                    if not clicked:
                        elements.append(
                                [visit_id, r[1], r[2], r[3], 1, "# css_element not found", r[6], r[7], r[8], r[9],
                                 r[10], r[11], r[12], r[13], r[14], r[15]])
                        print(f"Element not found on site {r[2]}")

                except TimeoutError as err: # Get error and write to database
                    print('({}) http://{} Timeout      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                              time.time() - this_url_start,
                                                                                              time.time() - start_time, type(err)))
                    print(traceback.format_exc())
                    fails.value += 1
                    elements.append(
                                [visit_id, site_nr, short_url, visit_type, 1, "° Timeout error during visit", r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15]])
                except WebDriverException as err: # Get error and write to database
                    print("({}){} WebDriverException     {:.2f}-{:.2f} (Error type {} - Message)".format(site_nr, url,
                                                                                                         time.time() - this_url_start,
                                                                                                         time.time() - start_time,
                                                                                                         type(err), err.msg))
                    print(traceback.format_exc())
                    fails.value += 1
                    elements.append(
                                [visit_id, site_nr, short_url, visit_type, 1, "° WebdriverException during visit", r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15]])
                except Exception as err: # Get error and write to database
                    print('({}) http://{} Error      {:.2f}-{:.2f}  (Error type {})'.format(site_nr, url,
                                                                                            time.time() - this_url_start,
                                                                                            time.time() - start_time, type(err)))
                    print(traceback.format_exc())
                    #print(err)
                    fails.value += 1
                    elements.append(
                                [visit_id, site_nr, short_url, visit_type, 1, "° Other error during visit", r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15]])

                finally:
                    driver.quit()
                    killtree(os.getpid())

    # driver.close()
    driver.quit()

    if visit:
        print('URL visit finished - ' + short_url)
    else:
        print('URL skipped - ' + short_url)


# Parent thread voor de website bezoeken, bereidt de te bezoekn site voor en houdt bij als er geen timeout is
# Zorgt dat de bezoeken gepauzeert worden en schrijf naar database bij errors
# i = thread number
def session_checker(lock, thread_nr, runn, stop, pause, now, urls, fails, cookies, cookies2, visits,
                    elements, LIMIT_CPU, redirects, all_requests, predictions):
    print('Starting session ' + str(thread_nr))

    while fails.value < nr_fails and not stop.value:  # Keep this thread running until stop signal
        # Pauzeer de thread
        if pause.value:
            print(f'Pausing thread {thread_nr}')
        while pause.value:
            time.sleep(1)

        # Laadt de te zoeken website nummer in de lijst in en zet klaar voor volgende thread
        with runn:
            j = runn.value
            runn.value += 1

        # Variabelen inladen
        site_nr = int(urls[j - 1][0])
        short_url = urls[j - 1][1]
        visit_type = int(urls[j - 1][2])
        visit_id = random.randrange(1, 1000000000000)

        # Laadt de te bezoeken website in
        visit_url = check_response(short_url)

        if not visit_url:
            print("({}) http://{} has been skipped because it can't be reached".format(site_nr, short_url))
            elements.append(
                [visit_id, site_nr, short_url, 0, 1, "# Skipped because can't be reached", "", "", "", "", "", "", "", "", "", ""])
            visits.append([visit_id, site_nr, short_url, visit_type, "# can't be reached", -1])
        else:
            # Start de browser sessie
            p = Process(target=session, args=(
                lock, stop, now, short_url, visit_url, visit_type, site_nr, fails, cookies, cookies2, visit_id, visits,
                elements, urls, runn, LIMIT_CPU, redirects, all_requests, thread_nr, predictions))
            p.start()

            # Check voor timeout
            start = time.time()
            while time.time() - start <= TIMEOUT:
                if not p.is_alive():
                    p.terminate()
                    p.join()
                    # The process are done, break now.
                    break
                time.sleep(1)  # Just to avoid hogging the CPU

            else:
                # We only enter this if we didn't 'break' above.
                if p.is_alive():
                    print("({}) http://{} Session timed out after {:.2f} seconds".format(site_nr, short_url,
                                                                                         time.time() - start))
                    fails.value += 1
                    with lock:
                        # killing all children of this thread
                        killtree(os.getpid())

                        # Sla op in database
                        visits.append([visit_id, site_nr, short_url, visit_type, "° Timeout", -1])
                        elements.append([visit_id, site_nr, short_url, visit_type, 1, "° Timeout during session", ""])
                else:
                    p.terminate()
                    p.join()

        # Pauseert de thread (2de keer anders kan het wat langer duren om te pauseren)
        if pause.value:
            print(f'Pausing thread {thread_nr}')
        while pause.value:
            time.sleep(1)

        if runn.value > len(urls):
            stop.value = True
            print('Last website reached, finishing threads')

    print('Ending session ' + str(thread_nr))


# Hoofd thread
if __name__ == '__main__':
    freeze_support()  # needed for Windows for multiprocessing
    main()
