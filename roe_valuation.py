
import pandas as pd
import pandas_datareader as pdr

from datetime import datetime

from bs4 import BeautifulSoup
import requests
import urllib.request
#TEST

# 종목 타입에 따라 download url이 다름. 종목코드 뒤에 .KS .KQ등이 입력되어야해서 Download Link 구분 필요

stock_type = {
'kospi': 'stockMkt',
'kosdaq': 'kosdaqMkt'
}

# 회사명으로 주식 종목 코드를 획득할 수 있도록 하는 함수
def get_code(df, name):
    code = df.query("name=='{}'".format(name))['code'].to_string(index=False)
    # 위와같이 code명을 가져오면 앞에 공백이 붙어있는 상황이 발생하여 앞뒤로 sript() 하여 공백 제거
    code = code.strip()
    return code

# download url 조합
def get_download_stock(market_type=None):
    market_type = stock_type[market_type]
    download_link = 'https://kind.krx.co.kr/corpgeneral/corpList.do'
    download_link = download_link + '?method=download'
    download_link = download_link + '&marketType=' + market_type
    download_link = download_link + '&searchType=13'
    df = pd.read_html(download_link, header=0)[0]
    return df

# kospi 종목코드 목록 다운로드
def get_download_kospi():
    df = get_download_stock('kospi')
    df.종목코드 = df.종목코드.map('{:06d}.KS'.format)
    return df

# kosdaq 종목코드 목록 다운로드
def get_download_kosdaq():
    df = get_download_stock('kosdaq')
    df.종목코드 = df.종목코드.map('{:06d}.KQ'.format)
    return df

def get_spread_point():
    url ="https://www.kisrating.com/ratingsStatistics/statics_spread.do"
    sp = urllib.request.urlopen(url).read()
    sp_soup=BeautifulSoup(sp, 'html.parser')
    sp_cells = sp_soup.find('div', {'class': "table_ty1"}).find_all('td')
    return sp_cells[98].string
    

# kospi, kosdaq 종목코드 각각 다운로드
kospi_df = get_download_kospi()
kosdaq_df = get_download_kosdaq()
spread_point = get_spread_point()

# data frame merge
code_df = pd.concat([kospi_df, kosdaq_df])

# data frame정리
code_df = code_df[['회사명', '종목코드']]

# data frame title 변경 '회사명' = name, 종목코드 = 'code'
code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})

code_df = code_df.head(1)

stock_frame = pd.DataFrame(columns = ['code','name','roe','stockholder','all_stock','my_stock'])

for k_code, k_name in zip(code_df['code'],code_df['name']):
    try:
        #ROE줍줍
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=104&stkGb=701"
        #print(url)
        f = urllib.request.urlopen(url).read()
        soup=BeautifulSoup(f, 'html.parser')
        roe_cells = soup.find('tr', {'id': "p_grid1_18"}).find_all('td')
        print(roe_cells[4].string)

        #지배주주 줍줍
        #http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A155660&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701"
        #print(url)
        f = urllib.request.urlopen(url).read()
        soup=BeautifulSoup(f, 'html.parser')
        sh_cells = soup.find('tr', {'id': "p_grid2_10"}).find_all('td')
        
        print((sh_cells[3].string).replace(',',''))

        ##발행주식수 줍줍
        #http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A010130&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"
        print(url)
        f = urllib.request.urlopen(url).read()
        soup=BeautifulSoup(f, 'html.parser')

        cells = soup.find('table', {'class': "us_table_ty1 table-hb thbg_g h_fix zigbg_no"}).find_all('td')
        all_stock_cnt = ((cells[10].string).replace(',','')).split('/')[0]

        cells = soup.find('table', {'class': "us_table_ty1 h_fix zigbg_no notres"}).find_all('td')
        
        print(cells.len())
        
        '''
        if cells.len > 6:
            my_stock_cnt = ((cells[6].string).replace(',','')).split('/')[0]
        else:
            my_stock_cnt=0
        

        stock_frame = stock_frame.append({'code':k_code,
                                          'name':k_name,
                                          'roe':roe_cells[4].string,
                                          'stockholder':(sh_cells[3].string).replace(',',''),
                                          'all_stock':all_stock_cnt,
                                          'my_stock':my_stock_cnt}, 
                                          ignore_index = True)
        #stock_cnt = (all_stock_cnt - my_stock_cnt) / 100000000

        #지배주주지분 + ((지배주주지분 * (예상roe - bbb_roe)/bbb_roe)
        #stock_price = c_stockholder + ((c_stockholder * (roe - spread_point))/spread_point)

        print(stock_frame)
        '''
    except:
        pass

    finally:
        pass

'''
# 삼성전자의 종목코드 획득. data frame에는 이미 XXXXXX.KX 형태로 조합이 되어있음
code = get_code(code_df, '삼성전자')

# get_data_yahoo API를 통해서 yahho finance의 주식 종목 데이터를 가져온다.
df = pdr.get_data_yahoo(code,'2021-01-28')


print(df)
'''