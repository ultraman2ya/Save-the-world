import sqlite3
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

def fetch_and_save_stock_prices(conn):
    c = conn.cursor()

    # 주식 목록 가져오기 (KRX, KOSPI, KOSDAQ)
    stock_list = fdr.StockListing("KRX")  # KRX (유가증권 + 코스닥)
    stock_list = stock_list[['Code', 'Name']]
    stock_list.reset_index(drop=True,inplace=True)

    # 이전 데이터 유무를 확인하기 위해 최근 날짜를 가져옵니다.
    c.execute("SELECT MAX(stock_date) FROM stock_hst")
    last_date_record = c.fetchone()[0]
    
    if last_date_record:
        # start_date = datetime.strptime(last_date_record, "%Y-%m-%d").date() + timedelta(days=1)  # 마지막 날짜 다음날 부터
        start_date = last_date_record
    else:
        start_date = '2024-09-01'
        
    end_date = datetime.today().date()

    # 데이터를 가져오고 저장
    for index, row in stock_list.iterrows():
        stock_code = row['Code']
        stock_name = row['Name']
        print(f"Processing: {stock_code} - {stock_name}")
        
        try:
            # 주가 데이터 가져오기
            stock_data = fdr.DataReader(stock_code, start=start_date, end=end_date)
            stock_data.reset_index(inplace=True)

            for index, data_row in stock_data.iterrows():
                c.execute('''
                    INSERT OR REPLACE INTO stock_hst (stock_date, stock_code, stock_price, stock_max_price)
                    VALUES (?, ?, ?, ?)
                    ''', (
                        data_row['Date'].strftime('%Y%m%d'),
                        stock_code,
                        data_row['Close'],
                        data_row['High']
                    ))
                
            
            conn.commit()
            print(f"{stock_code} - {stock_name} data saved.")
        except Exception as e:
            print(f"Error processing {stock_code} - {stock_name}: {e}")

if __name__ == "__main__":
    conn = sqlite3.connect('main_db.db')
    fetch_and_save_stock_prices(conn)
    conn.close()
