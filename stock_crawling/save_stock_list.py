import sqlite3
import FinanceDataReader as fdr
import pandas as pd


conn = sqlite3.connect('main_db.db')
c = conn.cursor()

#c.execute("Select * From stock_hst")


#read1 = c.fetchone()
#print(read1)

##stock_data = fdr.DataReader()

stocks = fdr.StockListing('KRX')
stocks = stocks[['Code','Name','Market']]

stocks.reset_index(inplace=True)

for index, row in stocks.iterrows():
    c.execute('''
        INSERT OR REPLACE INTO stock_list (stock_code, stock_name, stock_market)
        VALUES (?, ?, ?)
        ''', (row['Code'], row['Name'], row['Market']))


conn.commit()

