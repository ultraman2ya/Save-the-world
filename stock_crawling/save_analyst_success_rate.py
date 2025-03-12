import sqlite3
import pandas as pd

def get_analyst_and_company_data(conn):

    cursor = conn.cursor()

    # 모든 고유한 (작성자 회사명, 작성자) 조합 목록 가져오기
    cursor.execute(
        "SELECT DISTINCT report_comp, report_analyst FROM stock_report WHERE report_analyst <> '' AND report_analyst IS NOT NULL AND report_comp <> '' AND report_comp IS NOT NULL"
    )
    analyst_company_rows = cursor.fetchall()
    analyst_company_list = [(row[0], row[1]) for row in analyst_company_rows]  # (회사명, 분석가) 튜플 리스트

    analyst_company_data = {}
    for company, analyst in analyst_company_list:
        # 각 작성자-회사 조합에 대한 데이터 조회
        cursor.execute(
                       """select report_comp,
                                 report_analyst,
                                 count(report_analyst) aname,
                                 count(aog) aog
                            from (
                                    select sr.report_date,
                                        sr.stock_code,
                                        sl.stock_name,
                                        sr.report_opinion,
                                        cast(sr.stock_goal as float) stock_goal,
                                        cast((select stock_price from stock_hst where stock_code = sr.stock_code and stock_Date = sr.report_date) as float) close_price,
                                        cast((select stock_price from stock_hst where stock_code = sr.stock_code and stock_date = (select max(stock_date) from stock_hst where stock_code = sr.stock_code)) as flost) last_close_price,
                                        sr.report_analyst_grade,
                                        sr.report_comp,
                                        sr.report_analyst,
                                        (select min(stock_date) from stock_hst where stock_code = sr.stock_code and stock_date >= sr.report_date and cast(stock_max_price as integer) >= cast(sr.stock_goal as integer)) aog
                                    from stock_report sr, stock_list sl
                                    where sr.stock_code = sl.stock_code
                                    and sr.report_comp = ?
                                    and sr.report_analyst = ?
                                ) group by report_comp, report_analyst """,
            (company, analyst),
        )

        rows = cursor.fetchone() #리스트로 여러개 받는것이 아닌 1개의 결과만 받도록 수정합니다.
        if rows:
          report_comp, report_analyst, aname, aog = rows
          if aname !=0 : # 0으로 나누는경우를 제외합니다.
            success_rate = aog / aname if aname else 0 # aname이 0인경우 제외
          else :
            success_rate = 0 
          
          print(f"report_comp:{report_comp}, report_analyst:{report_analyst}, aname:{aname}, aog:{aog}, rate:{success_rate}")
          
          # 데이터베이스에 저장
          cursor.execute('''
              INSERT OR REPLACE INTO stock_analyst_rate 
                  (report_comp, report_analyst, report_count, report_success_count, analyst_success_rate)
              VALUES (?, ?, ?, ?, ?)
          ''', (report_comp, report_analyst, aname, aog, success_rate))

    conn.commit()






if __name__ == "__main__":
    conn = sqlite3.connect("main_db.db")

    get_analyst_and_company_data(conn)

    conn.close()


