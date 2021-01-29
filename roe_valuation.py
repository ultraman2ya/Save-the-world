
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

#시작일 종료일
start = str(datetime.now())[:10]
end = str(datetime.now())[:10]

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

code_df = code_df.head(10)

stock_frame = pd.DataFrame(columns = ['code','name','roe','roe_avg','stockholder','all_stock','my_stock','price',
                                      'value_fare','price_fare',
                                      'value_10','price_10',
                                      'value_20','price_20',
                                      'value_30','price_30',
                                      'value_50','price_50'
                                     ])



for k_code, k_name in zip(code_df['code'],code_df['name']):
    roe_avg = 0

    try:
        print(k_code, k_name, 'Start-->>')

        #ROE줍줍
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=104&stkGb=701"
        f = urllib.request.urlopen(url).read()
        soup=BeautifulSoup(f, 'html.parser')
        roe_cells = soup.find('tr', {'id': "p_grid1_18"}).find_all('td')
        
        roe_avg = ((float(roe_cells[3].string)*3) + (float(roe_cells[2].string)*2) + (float(roe_cells[1].string)*1))/6
        print('roe_ok')

        #지배주주 줍줍
        #http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A155660&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701"

        f = urllib.request.urlopen(url).read()
        soup=BeautifulSoup(f, 'html.parser')
        sh_cells = soup.find('tr', {'id': "p_grid2_10"}).find_all('td')
        print('holder_ok')

        ##발행주식수 줍줍
        #http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A010130&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"
        
        f = urllib.request.urlopen(url).read()
        soup=BeautifulSoup(f, 'html.parser')

        cells = soup.find('table', {'class': "us_table_ty1 table-hb thbg_g h_fix zigbg_no"}).find_all('td')
        all_stock_cnt = ((cells[10].string).replace(',','')).split('/')[0]

        cells = soup.find('table', {'class': "us_table_ty1 h_fix zigbg_no notres"}).find_all('td')

        if len(cells) > 6:
            my_stock_cnt = ((cells[6].string).replace(',','')).split('/')[0]
        else:
            my_stock_cnt=0
        
        print('stock_ok')
        
        
        #주식 현재가격 줍줍
        price_df = pdr.get_data_yahoo(k_code)
        stock_now_price = price_df.tail(1)
        print('price_ok')

        stock_frame = stock_frame.append({'code':k_code,
                                          'name':k_name,
                                          'roe':roe_cells[4].string,
                                          'roe_avg':roe_avg,
                                          'stockholder':(sh_cells[3].string).replace(',',''),
                                          'all_stock':all_stock_cnt,
                                          'my_stock':my_stock_cnt,
                                          'price':stock_now_price['Close'][0]
                                          }, 
                                          ignore_index = True)

        print(k_code, k_name, '<<<--- succeed')

    except:
        print(k_code, k_name, '데이터 수집 오류.!!!!!!')

    finally:
        pass
'''
stock_frame['value_fare'] = float(stock_frame['stockholder']) + ((float(stock_frame['stockholder'])*(float(stock_frame['roe_avg'])-float(spread_point)))/float(spread_point))
stock_frame['value_10'] = float(stock_frame['stockholder']) + ((float(stock_frame['stockholder'])*(float(stock_frame['roe_avg'])-float(spread_point)))*(0.9/(1+float(spread_point)-0.9)))
stock_frame['value_20'] = float(stock_frame['stockholder']) + ((float(stock_frame['stockholder'])*(float(stock_frame['roe_avg'])-float(spread_point)))*(0.8/(1+float(spread_point)-0.8)))
stock_frame['value_30'] = float(stock_frame['stockholder']) + ((float(stock_frame['stockholder'])*(float(stock_frame['roe_avg'])-float(spread_point)))*(0.7/(1+float(spread_point)-0.7)))
stock_frame['value_50'] = float(stock_frame['stockholder']) + ((float(stock_frame['stockholder'])*(float(stock_frame['roe_avg'])-float(spread_point)))*(0.5/(1+float(spread_point)-0.5)))



stock_frame['price_fare'] = (float(stock_frame['value_fare']) / (float(stock_frame['all_stock'])- float(stock_frame['my_stock'])))*100000000
stock_frame['price_10'] = (float(stock_frame['value_10']) / (float(stock_frame['all_stock'])- float(stock_frame['my_stock'])))*100000000
stock_frame['price_20'] = (float(stock_frame['value_20']) / (float(stock_frame['all_stock'])- float(stock_frame['my_stock'])))*100000000
stock_frame['price_30'] = (float(stock_frame['value_30']) / (float(stock_frame['all_stock'])- float(stock_frame['my_stock'])))*100000000
stock_frame['price_50'] = (float(stock_frame['value_50']) / (float(stock_frame['all_stock'])- float(stock_frame['my_stock'])))*100000000
'''

print(stock_frame)

stock_frame.to_excel('s_rim.xlsx')