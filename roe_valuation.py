
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
    

print("Kospi & Kosdaq All Stock S-Rim Data Calculation Start --- !!!")

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
                                      'value_fare','price_fare'
                                     ])

for k_code, k_name in zip(code_df['code'],code_df['name']):
    roe_avg = 0
    error_title = ""

    try:
        #ROE줍줍
        error_title = 'ROE'
        
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701"
        
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
        else:
            roe_avg = 0

        print(roe_avg)
        

        #지배주주 줍줍
        error_title = 'StockHolder'
        #http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A155660&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701
        url ="http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A" + k_code[:-3] + "&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701"

        f = urllib.request.urlopen(url).read()
        soup=BeautifulSoup(f, 'html.parser')
        #sh_cells = soup.find('tr', {'id': "p_grid2_10"}).find_all('td')
        sh_temp_cells = soup.find('tr', {'id': "p_grid2_10"})

        if sh_temp_cells:
            sh_cells = soup.find('tr', {'id': "p_grid2_10"}).find_all('td')
            stock_holders = sh_cells[3].string
        else:
            sh_cells = soup.find('div', {'id': "divDaechaY"}).find_all('td')
            stock_holders = sh_cells[231].string

        ##발행주식수 줍줍
        error_title = 'Stock All Count'
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
        
       
        #주식 현재가격 줍줍
        error_title = 'Stock Price'
        price_df = pdr.get_data_yahoo(k_code)
        stock_now_price = price_df.tail(1)

        stock_frame = stock_frame.append({'code':k_code,
                                          'name':k_name,
                                          'roe':roe_cells[4].string,
                                          'roe_avg':roe_avg,
                                          'stockholder':stock_holders.replace(',',''),
                                          'all_stock':all_stock_cnt,
                                          'my_stock':my_stock_cnt,
                                          'price':stock_now_price['Close'][0]
                                          }, 
                                          ignore_index = True)
        '''
        print('succeed -------- >>>',k_code, k_name)

    except:
        print(k_code, k_name, error_title + '데이터 수집 오류.!!!!!!')

    finally:
        pass

'''
for i in stock_frame.index:

    value_stockholder = float(stock_frame.at[i,'stockholder'])
    value_roe_avg = float(stock_frame.at[i,'roe_avg'])
    value_all_stock = float(stock_frame.at[i,'all_stock'])
    value_my_stock = float(stock_frame.at[i,'my_stock'])

    stock_frame.at[i,'value_fare'] = (value_stockholder + ((value_stockholder)*(value_roe_avg-float(spread_point)))/float(spread_point))

    value_vfare = float(stock_frame.at[i,'value_fare'])

    stock_frame.at[i,'price_fare'] = ((value_vfare / (value_all_stock- value_my_stock))*10000000)

stock_frame.to_excel('s_rim.xlsx')

print("Kospi & Kosdaq All Stock S-Rim Data Calculation End --- !!!")