# This file will extract the results from the database file
import pprint
import sqlite3
import matplotlib.pyplot as plt

BASE_PATH = "d:/temp/Selenium-model/"

aerts_country_list = ['fr', 'ir', 'nl', 'co.uk', 'ch', 'lu', 'be', 'es', 'it', 'tr', 'se', 'pt', 'mt', 'fi', 'si', 'ro', 'de', 'lt', 'lv', 'gr', 'cz', 'hu', 'hr', 'sk', 'ee', 'no', 'bg', 'pl']

conn = sqlite3.connect(BASE_PATH + 'cookies.db')
cursor = conn.cursor()
#cursor.execute('SELECT * FROM elements where result == "Normal visit" AND element_type == 0 ORDER BY site_nr ASC', (site_nr,))
cursor.execute('SELECT * FROM elements where (result == "Normal visit" OR result == "No cookie dialog found during visit") AND element_type == 0 ORDER BY site_nr ASC')
res_cookie_dialog = cursor.fetchall()
conn.close()

top_500_count = {}
top_500 = {}
top_500_count_CD = {}
top_500_count_NOCD = {}
top_500_percentage = {}
count_accept = {}
count_reject = {}
count_all = {}
count_modify = {}
count_save = {}
for country in aerts_country_list:
    top_500_count[country] = 0
    top_500_count_CD[country] = 0
    top_500_count_NOCD[country] = 0
    top_500_percentage[country] = 0
    top_500[country] = []
    count_accept[country] = 0
    count_reject[country] = 0
    count_all[country] = 0
    count_modify[country] = 0
    count_save[country] = 0


for i, res in enumerate(res_cookie_dialog):
    for country in aerts_country_list:
        if "." + country in res[2]:
            top_500_count[country] += 1
            top_500[country].append(i)
            if res[5] == "Normal visit":
                top_500_count_CD[country] += 1
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
print("BE = 43.6% show cookie dialog, NL = 53.7% UK 68.1% Est 29.3% Ire 71.2% Swi 33.1%")

for country in aerts_country_list:
    top_500_percentage[country] = round(top_500_count_CD[country] / (top_500_count_CD[country] + top_500_count_NOCD[country]) *100, 1)

for country in aerts_country_list:
    print(f"Country: {country} - {top_500_percentage[country]}%")

#top_500_percentage = list(top_500_percentage.items())
#for t in top_500_percentage:
inv_top_500_percentage = {v: k for k, v in top_500_percentage.items()}


sorted_top_500_percentage = sorted(inv_top_500_percentage.items(), reverse=True)

print("Gesorteerd volgens %")
for t in sorted_top_500_percentage:
    print(f"{t[0]}% {t[1]}")
#pprint.pprint(sorted_top_500_percentage)

# Cookies set before accept/deny nl en be
'''print("Getting cookies set before any action")
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
    x_as = []
    for i in range(len(cookies_numbers_list)):
        x_as.append(i)
    plt.plot(x_as, cookies_numbers_list)
    plt.title(f"Country {country} number of cookies set")
    plt.show()

conn.close()'''

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

