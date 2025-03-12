from flask import Flask, render_template, jsonify
import pandas as pd
import sqlite3

app = Flask(__name__)

def get_stock_report_data():
    """Fetches data from the stock_report table and returns it as a list of dictionaries."""
    conn = sqlite3.connect('main_db.db')
    cursor = conn.cursor()

    cursor.execute("""
        select 
            report_date,
            stock_code,
            stock_name,
            report_opinion,
            stock_goal,
            close_price,
            max_price,
            last_close_price,
            round(((stock_goal - last_close_price)/last_close_price)*100) up_per,
            report_analyst_grade,
            report_comp,
            report_analyst,
            aog
        from (
                select sr.report_date,
                    sr.stock_code,
                    sl.stock_name,
                    sr.report_opinion,
                    cast(sr.stock_goal as float) stock_goal,
                    cast((select stock_price from stock_hst where stock_code = sr.stock_code and stock_Date = sr.report_date) as float) close_price,
                    cast((select stock_price from stock_hst where stock_code = sr.stock_code and stock_date = (select max(stock_date) from stock_hst where stock_code = sr.stock_code)) as flost) last_close_price,
                    cast((select max(stock_max_price) from stock_hst where stock_code = sr.stock_code and stock_date >= sr.report_date) as flost) max_price,
                    sr.report_analyst_grade,
                    sr.report_comp,
                    sr.report_analyst,
                    (select min(stock_date) from stock_hst where stock_code = sr.stock_code and stock_date >= sr.report_date and cast(stock_max_price as integer) >= cast(sr.stock_goal as integer)) aog
                from stock_report sr, stock_list sl
                where sr.stock_code = sl.stock_code
                and sr.report_date >= ((select max(report_date) from stock_report) - 7)
        ) order by report_date desc
    """)

    rows = cursor.fetchall()
    conn.close()

    # Convert rows to a list of dictionaries
    data = []
    for row in rows:
        data.append({
            '발행일자' : row[0],
            '종목코드' : row[1],
            '종목명' : row[2],
            '투자의견' : row[3],
            '목표가' : row[4],
            '종가' : row[5],
            '최고가' : row[6],
            '최신종가' : row[7],
            '상승률' : row[8],
            '등급' : row[9],
            '회사명' : row[10],
            '분석자' : row[11],
            '목표달성여부': row[12],
        })
    return data
            

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stock_reports')
def stock_reports():
    data = get_stock_report_data()
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
