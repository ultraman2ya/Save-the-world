from bs4 import BeautifulSoup
import requests
import urllib.request

url ="http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A010130&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"
#url = "http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A353200&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"

print(url)
f = urllib.request.urlopen(url).read()
soup=BeautifulSoup(f, 'html.parser')
roe_table = soup.find_all('table')

roe_tr = roe_table[10].find_all('tr')
row_cnt = 0
title_position1 = 0
title_position2 = 0

for row in roe_tr:
    row_cnt = row_cnt +1
    bbb = row.find('div')
    
    if bbb:
        if (bbb.string) == '자본총계':
            title_position1 = row_cnt
        
        if (bbb.string) == '자본금':
            title_position2 = row_cnt
                

if (title_position2 - title_position1)>1:
    sholder_cells = roe_tr[title_position1].find_all('td')
else:
    sholder_cells = roe_tr[title_position1 - 1 ].find_all('td')

sholder_cnt = 0

if len(sholder_cells) > 7:
    for i in range(0,4):
        temp_len = len(sholder_cells[i].string)
        if int(temp_len) > 1:
            sholder_cnt = sholder_cnt + 1
    print(sholder_cnt)
    if sholder_cnt > 3:
        stock_holders = str(sholder_cells[3].string)
    elif sholder_cnt > 2:
        stock_holders = str(sholder_cells[2].string)
    else:
        stock_holders = '0'

print(stock_holders)
