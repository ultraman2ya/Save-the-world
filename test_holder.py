from bs4 import BeautifulSoup
import requests
import urllib.request

#url ="http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A010130&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"
url = "http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A353200&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"

print(url)
f = urllib.request.urlopen(url).read()
soup=BeautifulSoup(f, 'html.parser')
cells = soup.find_all('table')

aaaa = cells[10].find_all('tr')
row_cnt = 0
title_position1 = 0
title_position2 = 0

for row in aaaa:
    row_cnt = row_cnt +1
    bbb = row.find('div')
    
    if bbb:
        print(bbb.string)
        if (bbb.string) == '자본총계':
            title_position1 = row_cnt
            print(row_cnt)
        
        if (bbb.string) == '자본금':
            title_position2 = row_cnt
            print(row_cnt)
                

if (title_position2 - title_position1)>1:
    xxx = aaaa[title_position1].find_all('td')
else:
    xxx = aaaa[title_position1 - 1 ].find_all('td')

print(xxx)
