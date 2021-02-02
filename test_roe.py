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

for row in aaaa:
    row_cnt = row_cnt +1
    bbb = row.find('dt')

    if bbb:
        if (bbb.string)[0:3] == 'ROE':
            roe_position = row_cnt
            print(row_cnt)

xxx = aaaa[roe_position - 1 ].find_all('td')

print(xxx)
