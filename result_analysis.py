# This file will extract the results from the database file
import pprint
import sqlite3
import matplotlib.pyplot as plt

BASE_PATH = "o:/Crawl data2/data/"
DOMAINS_FILE = "results_09-07-2022.csv"

aerts_country_list = ['fr', 'ie', 'nl', 'co.uk', 'ch', 'lu', 'be', 'at', 'es', 'it', 'se', 'pt', 'mt', 'fi', 'si', 'ro', 'de', 'lt', 'lv', 'gr', 'cz', 'hu', 'hr', 'sk', 'ee', 'no', 'bg', 'pl', 'cy']

def main_results():
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    #cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('SELECT * FROM elements where (result == "Normal visit" OR result == "No cookie dialog found during visit") AND element_type == 0 ORDER BY site_nr ASC')
    res_cookie_dialog = cursor.fetchall()
    conn.close()

    top_500_count = {}
    top_500 = {}
    top_500_count_NOCD = {}
    top_500_count_CD_CSS = {}
    top_500_count_CD_frame = {}
    top_500_percentage_CD_CSS = {}
    top_500_percentage_CD_frame = {}
    top_500_percentage_NOCD = {}
    count_accept = {}
    count_reject = {}
    count_all = {}
    count_modify = {}
    count_save = {}
    for country in aerts_country_list:
        top_500_count[country] = 0
        top_500_count_NOCD[country] = 0
        top_500_count_CD_CSS[country] = 0
        top_500_count_CD_frame[country] = 0
        top_500_percentage_CD_CSS[country] = 0
        top_500_percentage_CD_frame[country] = 0
        top_500_percentage_NOCD[country] = 0
        top_500[country] = []
        count_accept[country] = 0
        count_reject[country] = 0
        count_all[country] = 0
        count_modify[country] = 0
        count_save[country] = 0


    for i, res in enumerate(res_cookie_dialog):
        for country in aerts_country_list:
            if res[2].endswith("." + country):
                top_500_count[country] += 1
                top_500[country].append(i)
                if res[5] == "Normal visit" and res[3] == 0 and res[8]:
                    top_500_count_CD_frame[country] += 1
                elif res[5] == "Normal visit" and res[3] == 0 and not res[8]:
                    top_500_count_CD_CSS[country] += 1
                elif res[5] == "No cookie dialog found during visit" and res[3] == 0:
                    top_500_count_NOCD[country] += 1


    #print(top_500_count)

    count = 0
    to_add = 0
    for country in top_500_count:
        count += top_500_count[country]
        if top_500_count[country] < 500:
            to_add += (500 - top_500_count[country])

    print(f"Visits too little for Koen Aerts: {to_add}")
    print(f"Visits counted: {count}")

    print("Getting percentage of cookie shown")
    print("BE (.be) = 43.6% show cookie dialog, NL (.nl) = 53.7% UK (.co.uk) 68.1% Est (.ee) 29.3% Ire (.ie) 71.2% Swi (.ch) 33.1%")

    for country in aerts_country_list:
        total = top_500_count_NOCD[country] + top_500_count_CD_CSS[country] + top_500_count_CD_frame[country]
        top_500_percentage_NOCD[country] = round(top_500_count_NOCD[country] / total * 100, 1)
        top_500_percentage_CD_CSS[country] = round(top_500_count_CD_CSS[country] / total * 100 , 1)
        top_500_percentage_CD_frame[country] = round(top_500_count_CD_frame[country] / total * 100, 1)

    print("Country;No cookie dialog;Cookie dialog CSS;Cookie dialog frame")
    print(f"The Netherlands (.nl) KA;46,3%;32,8%;21,0%")
    print(f"The Netherlands (.nl) MM;{str(top_500_percentage_NOCD['nl']).replace('.', ',')}%;{str(top_500_percentage_CD_CSS['nl']).replace('.', ',')}%;{str(top_500_percentage_CD_frame['nl']).replace('.', ',')}%")
    print(f"Belgium (.be) KA;45,4%;28,6%;15,0%")
    print(f"Belgium (.be) MM;{str(top_500_percentage_NOCD['be']).replace('.', ',')}%;{str(top_500_percentage_CD_CSS['be']).replace('.', ',')}%;{str(top_500_percentage_CD_frame['be']).replace('.', ',')}%")
    print(f"UK (.co.uk) KA;31,9%;49,9%;18,2%")
    print(f"UK (.co.uk) MM;{str(top_500_percentage_NOCD['co.uk']).replace('.', ',')}%;{str(top_500_percentage_CD_CSS['co.uk']).replace('.', ',')}%;{str(top_500_percentage_CD_frame['co.uk']).replace('.', ',')}%")
    print(f"Estonia (.ee) KA;70,7%;20,1%;9,2%")
    print(f"Estonia (.ee) MM;{str(top_500_percentage_NOCD['ee']).replace('.', ',')}%;{str(top_500_percentage_CD_CSS['ee']).replace('.', ',')}%;{str(top_500_percentage_CD_frame['ee']).replace('.', ',')}%")
    print(f"Ireland (.ie) KA;28,8%;52,0%;19,2%")
    print(f"Ireland (.ie) MM;{str(top_500_percentage_NOCD['ie']).replace('.', ',')}%;{str(top_500_percentage_CD_CSS['ie']).replace('.', ',')}%;{str(top_500_percentage_CD_frame['ie']).replace('.', ',')}%")
    print(f"Switzerland (.ch) KA;66,9%;21,7%;11,4%")
    print(f"Switzerland (.ch) MM;{str(top_500_percentage_NOCD['ch']).replace('.', ',')}%;{str(top_500_percentage_CD_CSS['ch']).replace('.', ',')}%;{str(top_500_percentage_CD_frame['ch']).replace('.', ',')}%")

    for country in aerts_country_list:
        print(f"Country: .{country} - No cookie dialog: {top_500_percentage_NOCD[country]}% - CSS cookie dialog: {top_500_percentage_CD_CSS[country]}% - Frame dialog: {top_500_percentage_CD_frame[country]}%")

    #top_500_percentage = list(top_500_percentage.items())
    #for t in top_500_percentage:
    '''inv_top_500_percentage = {v: k for k, v in top_500_percentage.items()}


    sorted_top_500_percentage = sorted(inv_top_500_percentage.items(), reverse=True)

    print("Gesorteerd volgens %")
    for t in sorted_top_500_percentage:
        print(f"{t[0]}% {t[1]}")
    #pprint.pprint(sorted_top_500_percentage)'''

    # Cookies set before accept/deny nl en be
    print("Getting cookies set before any action")
    print("Koen Aerts (2of meer): BE: 85.2%, NL: 77.4%")
    print("+ Average number of cookies set prior to consent per country")
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    for country in aerts_country_list:
        count_2_or_more = 0
        count_less_than_2 = 0
        max_cookies = 0
        cookies_numbers_list = []
        for res_place in top_500[country]:
            visit_id = res_cookie_dialog[res_place][0]
    
            cursor = conn.cursor()
            # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
            cursor.execute(
                'SELECT * FROM cookies where visit_id == ? AND before_after == 0', (visit_id,))
            res_cookies = cursor.fetchall()
            cookies_numbers_list.append(len(res_cookies))
            if len(res_cookies) >= 2:
                count_2_or_more += 1
            else:
                count_less_than_2 += 1
            if len(res_cookies) > max_cookies:
                max_cookies = len(res_cookies)
        print(f"Found 2 or more: {count_2_or_more} / Found less than 2: {count_less_than_2}")
        print(f"For {country} percentage 2 or more: {round(count_2_or_more / (count_2_or_more+count_less_than_2) *100, 1)}% and max {max_cookies}")
        print(f"Average coookies set for {country}: {round(sum(cookies_numbers_list) / len(cookies_numbers_list), 1)}")
        cookies_numbers_list = sorted(cookies_numbers_list, reverse=True)
    
        # Plotting numbers
        '''x_as = []
        for i in range(len(cookies_numbers_list)):
            x_as.append(i)
        plt.plot(x_as, cookies_numbers_list)
        plt.title(f"Country {country} number of cookies set")
        plt.show()'''
    
    conn.close()

    print("-------------------------------------------------")
    print("Number of consent and reject elements per country")
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    #cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('SELECT * FROM elements ORDER BY site_nr ASC')
    res_elements_accept_reject = cursor.fetchall()
    conn.close()

    #print(res_elements_accept_reject)

    for res in res_elements_accept_reject:
        for country in aerts_country_list:
            if '.' + country in res[2]:
                if res[3] == 0 and res[4] == 1 and res[5] == "Normal visit":
                    count_all[country] += 1
                if res[3] == 1:
                    # Accept button
                    count_accept[country] += 1
                elif res[3] == 2:
                    # Reject button
                    count_reject[country] += 1
                elif res[3] == 3:
                    # Modify button
                    count_modify[country] += 1
                elif res[3] == 4:
                    # Save button
                    count_save[country] += 1

    for country in aerts_country_list:
        if count_accept[country] == 0:
            print(f"For country {country} no results")
        else:
            percentage_accept = round(count_accept[country] / (count_all[country]) * 100, 1)
            percentage_reject = round(count_reject[country] / (count_all[country]) * 100, 1)
            percentage_modify = round(count_modify[country] / (count_all[country]) * 100, 1)
            percentage_save = round(count_save[country] / (count_all[country]) * 100, 1)
            print(f"For country {country}: All dialogs: {count_all[country]} / Accept buttons: {count_accept[country]} / Reject buttons: {count_reject[country]}"
                  f" / Modify buttons: {count_modify[country]} / Save buttons: {count_save[country]}")
            print(f"{percentage_accept}% accept / {percentage_reject}% reject / {percentage_modify}% modify / {percentage_save}% save")

    print('------------------------------')

    for country in aerts_country_list:
        if count_accept[country] == 0:
            print(f"For country {country} no results")
        else:
            print(f"{country};{count_accept[country]};{count_reject[country]}")


def manual_crawl_comp():
    # name, [count_manual, count_crawl, setting_crawl, save_file, cookies_manual, cookies_crawl]
    settings = {"initial": [0, 0, 0, "manual-crawl comparison initial visit.csv", 0, 0],
                "accept_all": [0, 0, 1, "manual-crawl comparison accept_all.csv", 0, 0],
                "deny_basic": [0, 0, 2, "manual-crawl comparison deny_basic.csv", 0, 0],
                "deny_advanced": [0, 0, 99, "manual-crawl comparison deny_advanced.csv", 0, 0],
                "modify": [0, 0, 3, "manual-crawl comparison deny_advanced.csv", 0, 0],
                "save": [0, 0, 4, "manual-crawl comparison deny_advanced.csv", 0, 0]}


    urls_manual_crawl = {}  # manual crawl url list
    with open(BASE_PATH + DOMAINS_FILE) as file:
        lines = file.read()
        lines = lines.splitlines()

    for line in lines:
        line = line.replace('"', '').split(';')
        try:
            urls_manual_crawl[line[0] + "-" + line[4]] = [line[1].replace('www.', ''), int(line[9])]  # url, nr_cookies
            settings[line[3]][0] += 1
        except Exception as err:
            print(err)

    pprint.pprint(urls_manual_crawl)

    print('Loading in database (20s)')

    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    cursor.execute(
        'select count(C.name) AS nr_cookies, E.site_nr, E.sitename, C.before_after from elements as E join cookies as C on E.visit_id == C.visit_id and E.element_type == C.before_after GROUP BY E.visit_id, C.before_after ORDER BY E.site_nr ASC, E.element_type ASC')
    results_nr_cookies = cursor.fetchall()
    conn.close()

    for key in settings:
        with open(BASE_PATH + settings[key][3], "w") as file:
            file.write("site_nr; url; cookies_manual; cookies_crawl\n")

    for res in results_nr_cookies:
        for key in settings:
            if str(res[1]) + "-" + key in urls_manual_crawl and res[3] == settings[key][2]:
                with open(BASE_PATH + settings[key][3], "a") as file:
                    file.write(str(res[1]) + ";" + res[2] + ";" + str(
                        urls_manual_crawl[str(res[1]) + '-' + key][1]) + ";" + str(res[0]) + "\n")
                settings[key][4] += urls_manual_crawl[str(res[1]) + '-' + key][1]
                settings[key][5] += res[0]

        if str(res[1]) + "-" + 'initial' in urls_manual_crawl:
            for key in settings:
                if res[3] == settings[key][2]:
                    settings[key][1] += 1


    #print(f"Final: {count}: Manual avg = {round(sum_manual / count, 2)} Crawl avg = {round(sum_crawl / count, 2)}")

    #print("------Results:")
    for key in settings:
        print('country;Manual_cookies;Crawl_cookies')
        print(f"{key};{settings[key][0]};{settings[key][1]}")
        if not settings[key][1] == 0:
            with open(BASE_PATH + settings[key][3], 'a') as file:
                file.seek(1)
                file.write("\n;;" + str(round(settings[key][4] / settings[key][1], 2)) + ";" + str(round(settings[key][5] / settings[key][1], 2)))


def manual_crawl_comp2():
    # name, [count_manual, count_crawl, setting_crawl, save_file, cookies_manual, cookies_crawl]
    settings = {"initial": [0, 0, 0, "manual-crawl comparison initial visit.csv", 0, 0],
                "accept_all": [0, 0, 1, "manual-crawl comparison accept_all.csv", 0, 0],
                "deny_basic": [0, 0, 2, "manual-crawl comparison deny_basic.csv", 0, 0],
                "deny_advanced": [0, 0, 99, "manual-crawl comparison deny_advanced.csv", 0, 0],
                "modify": [0, 0, 3, "manual-crawl comparison modify.csv", 0, 0],
                "save": [0, 0, 4, "manual-crawl comparison save.csv", 0, 0]}

    urls_manual_crawl = []  # manual crawl url list
    tuple_url_nrs = []
    total_results = {}
    with open(BASE_PATH + DOMAINS_FILE) as file:
        lines = file.read()
        lines = lines.splitlines()

    for line in lines:
        line = line.replace('"', '').split(';')
        if True: #if line[8] == "Everything okay":
            try:
                urls_manual_crawl.append([int(line[0]), line[1].replace('www.', ''), settings[line[4]][2], int(line[9]), -1])  # site_nr, url, setting_crawl, cookies_manual, cookies_crawl
                settings[line[4]][0] += 1
                tuple_url_nrs.append(int(line[0]))
                #total_results[int(line[0])] =
            except Exception as err:
                pass

    tuple_url_nrs = sorted(tuple(set(tuple_url_nrs)))

    print(tuple_url_nrs)
    pprint.pprint(urls_manual_crawl)

    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    cursor.execute('select count(C.name) AS nr_cookies, E.site_nr, E.sitename, E.element_type from elements as E LEFT join cookies as C on E.visit_id == C.visit_id '
        'and E.element_type == C.before_after WHERE (E.result == "Normal visit" or E.result == "No cookie dialog found during visit") and E.site_nr IN (' + ','.join(map(str, tuple_url_nrs)) + ') GROUP BY E.visit_id, C.before_after ORDER BY E.site_nr ASC, E.element_type ASC')
    results = cursor.fetchall()
    conn.close()

    results_dict = {}
    for res in results:
        results_dict[str(res[1]) + '-' + str(res[3])] = [res[2], res[0]]  # site_nr-visit_type : url, nr_cookies
        if int(res[3]) == 3 or int(res[3] == 4):
            urls_manual_crawl.append([res[1], res[2], int(res[3]), -1, res[0]])

    from operator import itemgetter
    urls_manual_crawl = sorted(urls_manual_crawl, key=itemgetter(0))

    for url in urls_manual_crawl:
        try:
            url[4] = results_dict[str(url[0]) + '-' + str(url[2])][1]
        except:
            pass

    #pprint.pprint(urls_manual_crawl)

    for key in settings:
        with open(BASE_PATH + settings[key][3], "w") as file:
            file.write("site_nr; url; visit_type; cookies_manual; cookies_crawl\n")

    for url in urls_manual_crawl:
        for key in settings:
            if url[2] == settings[key][2]:
                with open(BASE_PATH + settings[key][3], "a") as file:
                    file.write(str(url[0]) + ";" + url[1] + ";" + str(url[2]) + ";" + str(url[3]) + ";" + str(url[4]) + "\n")


    #Hfor url in urls_manual_crawl:


    '''for url in urls_manual_crawl:
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        cursor.execute(
            'select count(C.name) AS nr_cookies, E.site_nr, E.sitename, C.before_after from elements as E join cookies as C on E.visit_id == C.visit_id '
            'and E.element_type == C.before_after WHERE E.site_nr == ? and C.before_after == ? GROUP BY E.visit_id, C.before_after ORDER BY E.site_nr ASC, E.element_type ASC', (url[0], url[2]))
        res = cursor.fetchall()
        conn.close()
        #print(url)
        #print(res)

        for key in settings:
            if len(res) == 1:
                res = list(res[0])
                #print(res[3])
                #print(settings[key][2])
                if int(res[3]) == settings[key][2]:
                    settings[key][1] += 1
                    settings[key][5] += res[0]
                    url[4] = res[0]
                    with open(BASE_PATH + settings[key][3], "a") as file:
                        file.write(str(res[1]) + ";" + res[2] + ";" + res[3] + ";" + str(url[3]) + ";" + str(res[0]) + "\n")'''

        #print('-----')



def accept_vs_decline():
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    #cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('SELECT * FROM elements WHERE element_type == 0 or element_type == 1 or element_type == 2 ORDER BY site_nr ASC, element_type ASC')
    res_elements_accept_reject = cursor.fetchall()
    conn.close()

    count_accept = {}
    count_reject = {}
    count_sites = {}
    for country in aerts_country_list:
        count_accept[country] = 0
        count_reject[country] = 0
        count_sites[country] = 0

    for res in res_elements_accept_reject:
        for country in aerts_country_list:
            if res[2].endswith("." + country) and res[2].replace("."+country, '').count('.') < 1 and not '#' in res[5] and not ':' in res[5] and not '°' in res[5]:
                if count_sites[country] < 500:
                    if res[3] == 0:
                        count_sites[country] += 1
                    if res[3] == 1:
                        count_accept[country] += 1
                    elif res[3] == 2:
                        count_reject[country] += 1

    print("Country;Count_accept;Count_reject;nr_of_sites")
    for country in aerts_country_list:
        print(f"{country};{count_accept[country]};{count_reject[country]};{count_sites[country]}")


def nocd_cd():
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('SELECT * FROM elements WHERE element_type == 0 ORDER BY site_nr ASC')
    res_elements_cd_nocd = cursor.fetchall()
    conn.close()

    count_NOCD = {}
    count_CD_CSS = {}
    count_CD_frame = {}
    count_sites = {}
    for country in aerts_country_list:
        count_NOCD[country] = 0
        count_CD_CSS[country] = 0
        count_CD_frame[country] = 0
        count_sites[country] = 0

    for res in res_elements_cd_nocd:
        for country in aerts_country_list:
            if res[2].endswith("." + country) and res[2].replace("."+country, '').count('.') < 1 and not '#' in res[5] and not ':' in res[5] and not '°' in res[5]:
                if count_sites[country] < 500:
                    count_sites[country] += 1
                    if res[5] == "No cookie dialog found during visit":
                        count_NOCD[country] += 1
                    elif res[5] == "Normal visit":
                        if res[8]:
                            count_CD_frame[country] += 1
                        else:
                            count_CD_CSS[country] += 1

    print("Country;Count_NOCD;Count_CD_CSS;Count_CD_frame;nr_of_sites")
    for country in aerts_country_list:
        print(f"{country};{count_NOCD[country]};{count_CD_CSS[country]};{count_CD_frame[country]};{count_sites[country]}")


def dialogs_buckets(buckets_type):
    # Shows cookie dialogs (with tech) or no cookie dialog showed for each bucket
    # Shows if cookie dialog then accept or reject button showed

    if buckets_type:
        buckets = [[0,5000], [5000,25000], [25000,100000], [100000,1000000]]

    else:
        # Divide whole list of normal visits into buckets of 5000 sites
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
        cursor.execute('SELECT site_nr FROM elements WHERE element_type == 0 and (result == "No cookie dialog found during visit" or result == "Normal visit") ORDER BY site_nr ASC')
        res_new_buckets = cursor.fetchall()
        conn.close()

        buckets = []
        count1 = 0
        count2 = 0
        index = 0
        for res in res_new_buckets:
            if count1 == count2:
                first_site_nr = res[0]
            count2 += 1
            if count2 - count1 > 5000:
                buckets.append([first_site_nr, res[0]])
                count1 = count2
        buckets.append([first_site_nr, res[0]])

    print(buckets)

    # Fill in empty values for buckets
    count_NOCD = []
    count_CD_CSS = []
    count_CD_frame = []
    count_accept_button = []
    count_reject_button = []
    count_modify_button = []
    count_save_button = []
    count_success_sites = []
    count_error_sites = []

    for index, bucket in enumerate(buckets):
        count_NOCD.extend([0])
        count_CD_CSS.extend([0])
        count_CD_frame.extend([0])
        count_accept_button.extend([0])
        count_reject_button.extend([0])
        count_modify_button.extend([0])
        count_save_button.extend([0])
        count_success_sites.extend([0])
        count_error_sites.extend([0])

    print(f'bucket;count_NOCD;count_CD_CSS;count_CD_frame; count_success_sites;count_error_sites;count_accept_button;count_reject_button;count_modify_button;count_save_button')

    for index, bucket in enumerate(buckets):
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
        cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ? and element_type == 0', (bucket[0], bucket[1]))
        res_buckets = cursor.fetchall()
        conn.close()

        for res in res_buckets:
            if not '#' in res[5] and not ':' in res[5] and not '°' in res[5]:  # no error in visit
                count_success_sites[index] += 1
            else:
                count_error_sites[index] += 1
            if res[5] == "Normal visit":
                # Check the buttons
                conn = sqlite3.connect(BASE_PATH + 'cookies.db')
                cursor = conn.cursor()
                # Accept button
                cursor.execute('SELECT * FROM elements WHERE site_nr == ? and element_type == 1', (res[1], ))
                if len(cursor.fetchall()) > 0:
                    count_accept_button[index] += 1
                # Reject button
                cursor.execute('SELECT * FROM elements WHERE site_nr == ? and element_type == 2', (res[1], ))
                if len(cursor.fetchall()) > 0:
                    count_reject_button[index] += 1
                # Modify button
                cursor.execute('SELECT * FROM elements WHERE site_nr == ? and element_type == 3', (res[1], ))
                if len(cursor.fetchall()) > 0:
                    count_modify_button[index] += 1
                # Save button
                cursor.execute('SELECT * FROM elements WHERE site_nr == ? and element_type == 4', (res[1], ))
                if len(cursor.fetchall()) > 0:
                    count_save_button[index] += 1
                conn.close()

                # check the CD with tech
                if not res[8]:  # CD + CSS
                    count_CD_CSS[index] += 1
                if res[8]:  # CD + frame
                    count_CD_frame[index] += 1
            if res[5] == "No cookie dialog found during visit":  # NOCD
                count_NOCD[index] += 1

        print(f'{bucket};{count_NOCD[index]};{count_CD_CSS[index]};{count_CD_frame[index]};{count_success_sites[index]};{count_error_sites[index]};{count_accept_button[index]};{count_reject_button[index]};{count_modify_button[index]};{count_save_button[index]}')

def set_buckets(buckets_type):
    if buckets_type:
        buckets = [[0, 5000], [5000, 25000], [25000, 100000], [100000, 1000000]]

    else:
        # Divide whole list of normal visits into buckets of 5000 sites
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
        cursor.execute(
            'SELECT site_nr FROM elements WHERE element_type == 0 and (result == "No cookie dialog found during visit" or result == "Normal visit") ORDER BY site_nr ASC')
        res_new_buckets = cursor.fetchall()
        conn.close()

        buckets = []
        count1 = 0
        count2 = 0
        index = 0
        for res in res_new_buckets:
            if count1 == count2:
                first_site_nr = res[0]
            count2 += 1
            if count2 - count1 > 5000:
                buckets.append([first_site_nr, res[0]])
                count1 = count2
        buckets.append([first_site_nr, res[0]])

    print(buckets)
    return buckets


def cookies_buckets(buckets_type, visit_type):
    # Shows cookies for each bucket and visit_type
    buckets = set_buckets(buckets_type)

    results_buckets = {-2: [], # error with type 0
                       -1: [], # No CD with type 0
                       0: [], # CD with type 0
                       1: [],
                       2: [],
                       3: [],
                       4: []}

    for index, bucket in enumerate(buckets):
        #print(bucket)
        for key in results_buckets:
            results_buckets[key].append([0, 0, 0])
        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
        cursor.execute('select E.site_nr, E.sitename, E.element_type, count(E.site_nr), E.result '
                       'from elements as E left join cookies as C on E.visit_id == C.visit_id and E.element_type == C.before_after '
                       'WHERE E.site_nr > ? and site_nr <= ? and (E.element_type > 0  or (E.result == "Normal visit" or E.result == "No cookie dialog found during visit"))'
                       'group by E.sitename, E.element_type '
                       'order by E.site_nr, E.element_type', (bucket[0], bucket[1]))
        #cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ?', (bucket[0], bucket[1]))
        res_buckets = cursor.fetchall()
        conn.close()

        for res in res_buckets:
            element_type = int(res[2])
            cookie_count = int(res[3])
            result_text = res[4]
            key = -2
            if element_type == 0:
                if result_text == "Normal visit":
                    key = 0
                elif result_text == "No cookie dialog found during visit":
                    key = -1
            elif not '#' in result_text and not ':' in result_text and not '°' in result_text:  # no error in visit
                key = element_type

            results_buckets[key][index][0] += 1
            results_buckets[key][index][1] += cookie_count
            if cookie_count > results_buckets[key][index][2]:
                results_buckets[key][index][2] = cookie_count

        #print(results_buckets)

    for key in results_buckets:
        print(f';bucket;total_sites;total_cookies;max_cookies')
        for index, bucket in enumerate(buckets):
            print(f'{key};{bucket};{results_buckets[key][index][0]};{results_buckets[key][index][1]};{results_buckets[key][index][2]}')


def cookies_sites_accept_decline():
    # Shows cookies for all sites before-after accepting

    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('select E.site_nr, E.sitename, E.element_type, count(E.site_nr), E.result '
                   'from elements as E left join cookies as C on E.visit_id == C.visit_id and E.element_type == C.before_after '
                   'WHERE (E.element_type > 0  or (E.result == "Normal visit" or E.result == "No cookie dialog found during visit"))'
                   'group by E.sitename, E.element_type '
                   'order by E.site_nr, E.element_type')
    #cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ?', (bucket[0], bucket[1]))
    res_buckets = cursor.fetchall()
    conn.close()

    results_sites = {}

    for res in res_buckets:
        site_nr = int(res[0])
        element_type = int(res[2])
        cookie_count = int(res[3])
        result_text = res[4]

        if element_type == 0 and result_text == "Normal visit":
            if site_nr in results_sites:
                results_sites[site_nr][0] = cookie_count
            else:
                results_sites[site_nr] = [cookie_count, -1, -1]
        elif element_type in [1,2] and not '#' in result_text and not ':' in result_text and not '°' in result_text:  # no error in visit
            if site_nr in results_sites:
                results_sites[site_nr][element_type] = cookie_count
            else:
                results_sites[site_nr] = [-1, -1, -1]
                results_sites[site_nr][element_type] = cookie_count

    #print(results_buckets)


    print(f'site_nr;cookies_init;cookies_accept;cookies_decline')
    for key in results_sites:
        if results_sites[key][0] == -1 or results_sites[key][1] == -1 or results_sites[key][2] == -1:
            pass
        else:
            print(f'{key};{results_sites[key][0]};{results_sites[key][1]};{results_sites[key][2]}')

def first_third_party_cookies():
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('select E.site_nr, E.sitename, E.element_type, count(E.site_nr), E.result, C.domain, V.site_url '
                   'from elements as E left join cookies as C on E.visit_id == C.visit_id and E.element_type == C.before_after '
                   'join visits as V on V.visit_id == E.visit_id and C.before_after == V.visit_type '
                   'WHERE (E.element_type > 0  or (E.result == "Normal visit" or E.result == "No cookie dialog found during visit"))'
                   'group by E.sitename, E.element_type, C.domain '
                   'order by E.site_nr, E.element_type')
    #cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ?', (bucket[0], bucket[1]))
    res_buckets = cursor.fetchall()
    conn.close()

    results_sites = {}  # site_nr,element_type : [short_url, first_party, third_party, CD? 1=yes]

    for res in res_buckets:
        site_nr = int(res[0])
        sitename = res[1]
        element_type = int(res[2])
        cookie_count = int(res[3])
        result_text = res[4]
        domain = res[5]
        site_url = res[6]
        site_url = site_url.replace('http://', '').replace('https://', '').replace('www.', '')
        site_url = site_url[:site_url.find("/")]
        if sitename in site_url:
            pass
        else:
            sitename = site_url

        if element_type == 0 and result_text == "Normal visit":
            if site_nr + element_type/10 not in results_sites:
                results_sites[site_nr + element_type / 10] = [sitename, 0, 0, 1]
            if domain is not None:
                if sitename in domain:
                    results_sites[site_nr + element_type / 10][1] += cookie_count
                else:
                    results_sites[site_nr + element_type / 10][2] += cookie_count
        elif element_type == 0 and result_text == "No cookie dialog found during visit":
            if site_nr + element_type/10 not in results_sites:
                results_sites[site_nr + element_type / 10] = [sitename, 0, 0, 0]
            if domain is not None:
                if sitename in domain:
                    results_sites[site_nr + element_type / 10][1] += cookie_count
                else:
                    results_sites[site_nr + element_type / 10][2] += cookie_count

        elif element_type in [1,2] and not '#' in result_text and not ':' in result_text and not '°' in result_text:  # no error in visit
            if site_nr + element_type/10 not in results_sites:
                results_sites[site_nr + element_type / 10] = [sitename, 0, 0, -1]
            if domain is not None:
                if sitename in domain:
                    results_sites[site_nr + element_type / 10][1] += cookie_count
                else:
                    results_sites[site_nr + element_type / 10][2] += cookie_count

    #print(results_buckets)


    print(f'site_nr;element_type;sitename;first_party;third_party;CD?')
    with open("d:/temp/first_third_party0.csv", "a") as file:
        file.write('site_nr;element_type;sitename;first_party;third_party;CD?\n')
    for key in results_sites:
        if int(key*10%10) == 0:
            print(f'{int(key)};{int(key*10%10)};{results_sites[key][0]};{results_sites[key][1]};{results_sites[key][2]};{results_sites[key][3]}')
            with open("d:/temp/first_third_party0.csv", "a") as file:
                file.write(f'{int(key)};{int(key*10%10)};{results_sites[key][0]};{results_sites[key][1]};{results_sites[key][2]};{results_sites[key][3]}\n')

    #input('----------------')

    print(f'site_nr;element_type;sitename;first_party;third_party;CD?')
    with open("d:/temp/first_third_party1.csv", "a") as file:
        file.write('site_nr;element_type;sitename;first_party;third_party;CD?\n')
    for key in results_sites:
        if int(key * 10 % 10) == 1:
            print(
                f'{int(key)};{int(key * 10 % 10)};{results_sites[key][0]};{results_sites[key][1]};{results_sites[key][2]};{results_sites[key][3]}')
            with open("d:/temp/first_third_party1.csv", "a") as file:
                file.write(
                    f'{int(key)};{int(key * 10 % 10)};{results_sites[key][0]};{results_sites[key][1]};{results_sites[key][2]};{results_sites[key][3]}\n')

    #input('----------------')

    print(f'site_nr;element_type;sitename;first_party;third_party;CD?')
    with open("d:/temp/first_third_party2.csv", "a") as file:
        file.write('site_nr;element_type;sitename;first_party;third_party;CD?\n')
    for key in results_sites:
        if int(key * 10 % 10) == 2:
            print(
                f'{int(key)};{int(key * 10 % 10)};{results_sites[key][0]};{results_sites[key][1]};{results_sites[key][2]};{results_sites[key][3]}')
            with open("d:/temp/first_third_party2.csv", "a") as file:
                file.write(
                    f'{int(key)};{int(key * 10 % 10)};{results_sites[key][0]};{results_sites[key][1]};{results_sites[key][2]};{results_sites[key][3]}\n')

def https_redirects():
    buckets = set_buckets(False)
    results_buckets = []

    for index, bucket in enumerate(buckets):
        # print(bucket)
        results_buckets.append([bucket, [0, 0, 0]]) # count, count_http, count_https

        conn = sqlite3.connect(BASE_PATH + 'cookies.db')
        cursor = conn.cursor()
        # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
        cursor.execute('select E.site_nr, E.sitename, E.element_type, E.result, V.site_url '
                       'from elements as E '
                       'join visits as V on V.visit_id == E.visit_id and E.element_type == V.visit_type '
                       'WHERE E.element_type == 0 and E.site_nr > ? and E.site_nr <= ? and (E.result == "Normal visit" or E.result == "No cookie dialog found during visit")'
                       'group by E.sitename, E.element_type '
                       'order by E.site_nr, E.element_type', (bucket[0], bucket[1]))
        #cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ?', (bucket[0], bucket[1]))
        res_buckets = cursor.fetchall()
        conn.close()

        count = 0
        count_http = 0
        count_https = 0
        for res in res_buckets:
            site_nr = int(res[0])
            sitename = res[1]
            element_type = int(res[2])
            result_text = res[3]
            site_url = res[4]

            results_buckets[index][1][0] += 1
            if site_url.startswith("http://"):
                results_buckets[index][1][1] += 1
            if site_url.startswith("https://"):
                results_buckets[index][1][2] += 1


    print('key;count_http;count_https;count')
    for bucket in results_buckets:
        print(f'{bucket[0]};{bucket[1][1]};{bucket[1][2]};{bucket[1][0]}')


def most_used_domain_third_party(visit_type):
    results = {}
    results2 = {}

    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('select count(C.domain), C.domain, V.site_url, V.sitename from cookies as C '
                   'join visits as V on C.visit_id == V.visit_id and C.before_after == V.visit_type '
                   'where C.before_after == ? group by C.domain, V.site_url order by count(C.domain) DESC', (visit_type, ))
    #cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ?', (bucket[0], bucket[1]))
    res_domains = cursor.fetchall()
    conn.close()

    total_cookies = 0
    total_sites = 0

    for res in res_domains:
        count = res[0]
        domain = res[1].replace('www.', '')
        if domain.startswith('.'):
            domain = domain[1:]
        if domain.startswith('c.'):
            domain = domain[2:]
        if domain.startswith('ads.'):
            domain = domain[4:]
        if domain.startswith('dpm.'):
            domain = domain[4:]
        if domain.startswith('analytics.'):
            domain = domain[10:]

        total_cookies += count
        total_sites += 1

        site_url = res[2]
        sitename = res[3]

        site_url = site_url.replace('http://', '').replace('https://', '').replace('www.', '')
        site_url = site_url[:site_url.find("/")]
        if sitename in site_url:
            pass
        else:
            sitename = site_url

        if domain not in results:
            results[domain] = count
            results2[domain] = 1
        else:
            results[domain] += count
            results2[domain] += 1

    print(f'Total cookies;{total_cookies}')
    print(f'Total visits;{total_sites}')

    count = 0
    for w in sorted(results, key=results.get, reverse=True):
        print(f"{w};{results[w]}")
        count += 1
        if count > 100:
            break

    print('---------------')

    count = 0
    for w in sorted(results2, key=results2.get, reverse=True):
        print(f"{w};{results2[w]}")
        count += 1
        if count > 100:
            break


def most_used_domain_third_party2():
    results = {}
    results2 = {}
    sites_list = []

    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('select count(C.domain), C.domain, V.site_url, V.sitename, V.site_nr from cookies as C '
                   'join visits as V on C.visit_id == V.visit_id and C.before_after == V.visit_type '
                   'where C.before_after == 1 group by C.domain, V.site_url order by count(C.domain) DESC')
    #cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ?', (bucket[0], bucket[1]))
    res_domains = cursor.fetchall()
    conn.close()

    total_cookies = 0
    total_sites = 0

    for res in res_domains:
        count = res[0]
        domain = res[1].replace('www.', '')
        if domain.startswith('.'):
            domain = domain[1:]
        if domain.startswith('c.'):
            domain = domain[2:]
        if domain.startswith('d.'):
            domain = domain[2:]
        if domain.startswith('ads.'):
            domain = domain[4:]
        if domain.startswith('dpm.'):
            domain = domain[4:]
        if domain.startswith('analytics.'):
            domain = domain[10:]

        total_cookies += count
        total_sites += 1

        site_url = res[2]
        sitename = res[3]

        site_nr = int(res[4])
        sites_list.append(site_nr)

        site_url = site_url.replace('http://', '').replace('https://', '').replace('www.', '')
        site_url = site_url[:site_url.find("/")]
        if sitename in site_url:
            pass
        else:
            sitename = site_url

        if domain not in results:
            results[domain] = count
            results2[domain] = 1
        else:
            results[domain] += count
            results2[domain] += 1

    print(f'Total cookies;{total_cookies}')
    print(f'Total visits;{total_sites}')

    count = 0
    for w in sorted(results, key=results.get, reverse=True):
        print(f"{w};{results[w]}")
        count += 1
        if count > 100:
            break

    print('------------------------------')

    count = 0
    for w in sorted(results2, key=results2.get, reverse=True):
        print(f"{w};{results2[w]}")
        count += 1
        if count > 100:
            break

    tuple_url_nrs = tuple(sites_list)

    print('°°°°°°°°°°°°°°°°°°°°°°°°°°°°°')

    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    # cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('select count(C.domain), C.domain, V.site_url, V.sitename, V.site_nr from cookies as C '
                   'join visits as V on C.visit_id == V.visit_id and C.before_after == V.visit_type '
                   'where C.before_after == 0 and V.site_nr IN (' + ','.join(map(str, tuple_url_nrs)) + ') group by C.domain, V.site_url order by count(C.domain) DESC')
    # cursor.execute('SELECT * FROM elements WHERE site_nr > ? and site_nr <= ?', (bucket[0], bucket[1]))
    res_domains = cursor.fetchall()
    conn.close()

    results = {}
    results2 = {}
    total_cookies = 0
    total_sites = 0

    for res in res_domains:
        count = res[0]
        domain = res[1].replace('www.', '')
        if domain.startswith('.'):
            domain = domain[1:]
        if domain.startswith('c.'):
            domain = domain[2:]
        if domain.startswith('d.'):
            domain = domain[2:]
        if domain.startswith('ads.'):
            domain = domain[4:]
        if domain.startswith('dpm.'):
            domain = domain[4:]
        if domain.startswith('analytics.'):
            domain = domain[10:]

        total_cookies += count
        total_sites += 1

        site_url = res[2]
        sitename = res[3]

        site_nr = int(res[4])
        sites_list.append(site_nr)

        site_url = site_url.replace('http://', '').replace('https://', '').replace('www.', '')
        site_url = site_url[:site_url.find("/")]
        if sitename in site_url:
            pass
        else:
            sitename = site_url

        if domain not in results:
            results[domain] = count
            results2[domain] = 1
        else:
            results[domain] += count
            results2[domain] += 1

    print(f'Total cookies;{total_cookies}')
    print(f'Total visits;{total_sites}')

    count = 0
    for w in sorted(results, key=results.get, reverse=True):
        print(f"{w};{results[w]}")
        count += 1
        if count > 100:
            break

    print('------------------------------------')

    count = 0
    for w in sorted(results2, key=results2.get, reverse=True):
        print(f"{w};{results2[w]}")
        count += 1
        if count > 100:
            break


if __name__ == '__main__':
    print('1 = verg manuele crawl Koen')
    print('2 = verg met Koen Aerts')
    print('3 = accept vs decline EU countries')
    print('4 = NOCD-CDcssframe Koen Aerts comp EU countries')
    print('5 = cookie dialogs/bucket normal and modified')
    print('6 = cookies/bucket normal and modified')
    print('7 = cookies all sites')
    print('8 = first/third party cookies')
    print('9 = https redirects')
    print('10 = cookie domains')
    choice = int(input('Which comparison would you like to show? '))

    if choice == 1:
        print('-----------Vergelijking met de manuele crawl van Koen')
        manual_crawl_comp2()

    if choice == 2:
        print('-----------Vergelijking met Koen Aerts')
        main_results()

    if choice == 3:
        print('-----------Accept vs decline')
        accept_vs_decline()

    if choice == 4:
        print('-----------NOCD-CDcssframe---KA')
        nocd_cd()

    if choice == 5:
        print('-----------# Cookie dialogs/bucket')
        dialogs_buckets(True)

        print('-----------# Cookie dialogs/modified bucket')
        dialogs_buckets(False)

    if choice == 6:
        print('-----------Cookies per bucket modified')
        cookies_buckets(False, 0)

        print('-----------Cookies per bucket normal')
        cookies_buckets(True, 0)

    if choice == 7:
        print('-----------Cookie before-after accept')
        cookies_sites_accept_decline()

    if choice == 8:
        print('-----------First/third party cookies')
        first_third_party_cookies()

    if choice == 9:
        print('-----------https redirects')
        https_redirects()

    if choice == 10:
        print('-----------most used cookie domain for third party cookies')
        most_used_domain_third_party2()