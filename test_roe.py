from bs4 import BeautifulSoup
import requests
import urllib.request

#url ="http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A010130&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"
url = "http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A001250&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"

print(url)
f = urllib.request.urlopen(url).read()
soup=BeautifulSoup(f, 'html.parser')
roe_table = soup.find_all('table')

roe_tr = roe_table[10].find_all('tr')
row_cnt = 0

for row in roe_tr:
    row_cnt = row_cnt +1
    roe_dt = row.find('dt')

    if roe_dt:
        if (roe_dt.string)[0:3] == 'ROE':
            roe_position = row_cnt

roe_cells = roe_tr[roe_position - 1 ].find_all('td')

roe_cnt = 0

if len(roe_cells) > 7:
    for i in range(0,3):
        temp_len = len(roe_cells[i].string)
        if int(temp_len) > 1:
            roe_cnt = roe_cnt + 1

    if roe_cnt > 2:
        roe_avg = str(round((((float(roe_cells[2].string)*3) + (float(roe_cells[1].string)*2) + (float(roe_cells[0].string)*1))/6),2))
    elif roe_cnt > 1:
        roe_avg = str(round(((float(roe_cells[2].string)*2) + (float(roe_cells[1].string)*2) / 3),2))
    else:
        roe_avg = str(roe_cells[2].string)

    roe_now = '0'
    for i in range(4,7):
        temp_len = len(roe_cells[i].string)
        if int(temp_len) > 1:
            roe_now = roe_cells[i].string

        print(roe_now)

    print(roe_avg, roe_now)
