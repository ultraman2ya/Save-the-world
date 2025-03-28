import streamlit as st
import sqlite3
import pandas as pd

# Streamlit 앱 설정
st.set_page_config(
    page_title="Find Insight",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect("main_db.db")
    return conn

# 데이터베이스에서 데이터 가져오는 함수
def load_data(table_name, conn):
    try:
        query = f"""
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
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error loading data from {table_name}: {e}")
        return None

# 메인 앱
def main():
    st.title("Stock Data Viewer")

    conn = get_db_connection()

    # 사이드바에서 테이블 선택
    st.sidebar.header("Table Selection")
    table_options = ["stock_hst", "stock_report", "stock_analyst_rate"]
    selected_table = st.sidebar.selectbox("Select a table:", table_options)

    # 선택된 테이블 데이터 로드
    df = load_data(selected_table, conn)

    if df is not None:
        # 데이터 표시
        st.subheader(f"Data from {selected_table}")
        st.dataframe(df, use_container_width=True)

        # 데이터 요약
        st.subheader("Data Summary")
        st.write(df.describe())

        # 데이터 필터링
        st.sidebar.header("Data Filtering")
        if selected_table == "stock_hst":
            # stock_hst 테이블 필터링
            stock_codes = df["stock_code"].unique().tolist()
            selected_stock_code = st.sidebar.selectbox("Select Stock Code", ["All"] + stock_codes)
            if selected_stock_code != "All":
                df = df[df["stock_code"] == selected_stock_code]

            date_range = st.sidebar.date_input("Select Date Range", [df["stock_date"].min(), df["stock_date"].max()])
            if len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df["stock_date"] >= start_date.strftime('%Y%m%d')) & (df["stock_date"] <= end_date.strftime('%Y%m%d'))]

        elif selected_table == "stock_report":
            # stock_report 테이블 필터링
            report_comps = df["report_comp"].unique().tolist()
            selected_report_comp = st.sidebar.selectbox("Select Report Company", ["All"] + report_comps)
            if selected_report_comp != "All":
                df = df[df["report_comp"] == selected_report_comp]

            stock_codes = df["stock_code"].unique().tolist()
            selected_stock_code = st.sidebar.selectbox("Select Stock Code", ["All"] + stock_codes)
            if selected_stock_code != "All":
                df = df[df["stock_code"] == selected_stock_code]

            date_range = st.sidebar.date_input("Select Date Range", [pd.to_datetime(df["report_date"], format='%Y%m%d').min(), pd.to_datetime(df["report_date"], format='%Y%m%d').max()])
            if len(date_range) == 2:
                start_date, end_date = date_range
                df['report_date'] = pd.to_datetime(df['report_date'], format='%Y%m%d')
                df = df[(df["report_date"] >= start_date) & (df["report_date"] <= end_date)]
                df['report_date'] = df['report_date'].dt.strftime('%Y%m%d')

        elif selected_table == "stock_analyst_rate":
            # stock_analyst_rate 테이블 필터링
            report_comps = df["report_comp"].unique().tolist()
            selected_report_comp = st.sidebar.selectbox("Select Report Company", ["All"] + report_comps)
            if selected_report_comp != "All":
                df = df[df["report_comp"] == selected_report_comp]

            report_analysts = df["report_analyst"].unique().tolist()
            selected_report_analyst = st.sidebar.selectbox("Select Report Analyst", ["All"] + report_analysts)
            if selected_report_analyst != "All":
                df = df[df["report_analyst"] == selected_report_analyst]

        # 필터링된 데이터 표시
        st.subheader("Filtered Data")
        st.dataframe(df, use_container_width=True)

        # 필터링된 데이터 요약
        st.subheader("Filtered Data Summary")
        st.write(df.describe())

    conn.close()

if __name__ == "__main__":
    main()
