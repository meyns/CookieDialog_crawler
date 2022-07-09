# This file will extract the results from the database file
import pprint
import sqlite3
import matplotlib.pyplot as plt

BASE_PATH = "d:/temp/Selenium-model/"
DOMAINS_FILE = "results manual crawl final.csv"

aerts_country_list = ['fr', 'ie', 'nl', 'co.uk', 'ch', 'lu', 'be', 'es', 'it', 'tr', 'se', 'pt', 'mt', 'fi', 'si', 'ro', 'de', 'lt', 'lv', 'gr', 'cz', 'hu', 'hr', 'sk', 'ee', 'no', 'bg', 'pl']




def main_results():
    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    #cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
    cursor.execute('SELECT * FROM elements where (result == "Normal visit" OR result == "No cookie dialog found during visit") AND element_type == 0 ORDER BY site_nr ASC')
    res_cookie_dialog = cursor.fetchall()
    cursor.execute(
        'SELECT * FROM elements where element_type == 1 ORDER BY site_nr ASC')
    res_cookie_dialog_1 = cursor.fetchall()
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
                if res[5] == "Normal visit":
                    for res_1 in res_cookie_dialog_1:
                        if res_1[1] == res[1] and res_1[8]:
                            top_500_count_CD_frame[country] += 1
                        elif res_1[1] == res[1]:
                            top_500_count_CD_CSS[country] += 1
                else:
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
    print(f"Switzerland (.ch) MM;66,9%;21,7%;11,4%")
    print(f"Switzerland (.ch) KA;{str(top_500_percentage_NOCD['ch']).replace('.', ',')}%;{str(top_500_percentage_CD_CSS['ch']).replace('.', ',')}%;{str(top_500_percentage_CD_frame['ch']).replace('.', ',')}%")

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


def domains_file():
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

    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM elements WHERE result == "Normal visit" OR result == "No cookie dialog found during visit" ORDER BY site_nr ASC')
    results = cursor.fetchall()
    conn.close()

    for key in settings:
        with open(BASE_PATH + settings[key][3], "w") as file:
            file.write("site_nr; url; cookies_manual; cookies_crawl\n")


    conn = sqlite3.connect(BASE_PATH + 'cookies.db')
    cursor = conn.cursor()
    for res in results:
        for key in settings:
            if str(res[1]) + "-" + key in urls_manual_crawl and res[3] == settings[key][2]:
                cursor.execute(
                    'SELECT * FROM cookies WHERE visit_id == ? AND before_after == ?', (res[0], settings[key][2]))
                results_cookies = cursor.fetchall()
                print(f"{res[1]}-{res[2]}-{key}: {urls_manual_crawl[str(res[1]) + '-' + key][1]} - {len(results_cookies)}")
                with open(BASE_PATH + settings[key][3], "a") as file:
                    file.write(str(res[1]) + ";" + res[2] + ";" + str(urls_manual_crawl[str(res[1]) + '-' + key][1]) + ";" + str(len(results_cookies)) + "\n")
                settings[key][4] += urls_manual_crawl[str(res[1]) + '-' + key][1]
                settings[key][5] += len(results_cookies)

        if str(res[1]) + "-" + 'initial' in urls_manual_crawl:
            for key in settings:
                if res[3] == settings[key][2]:
                    settings[key][1] += 1


    conn.close()

    #print(f"Final: {count}: Manual avg = {round(sum_manual / count, 2)} Crawl avg = {round(sum_crawl / count, 2)}")

    print("------Results:")
    for key in settings:
        print(f"{key}: Manual: {settings[key][0]} - Crawl: {settings[key][1]}")
        if not settings[key][1] == 0:
            with open(BASE_PATH + settings[key][3], 'a') as file:
                file.seek(1)
                file.write("\n;;" + str(round(settings[key][4] / settings[key][1], 2)) + ";" + str(round(settings[key][5] / settings[key][1], 2)))


if __name__ == '__main__':
    print('-----------Vergelijking met de manuele crawl van Koen')
    domains_file()

    print('-----------Vergelijking met Koen Aerts')
    main_results()