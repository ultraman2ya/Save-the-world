import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta # Import timedelta

# Streamlit 앱 설정
st.set_page_config(
    page_title="Find Insight",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 데이터베이스 연결 함수
@st.cache_resource # Cache the connection
def get_db_connection():
    conn = sqlite3.connect("main_db.db", check_same_thread=False) # Allow multithreading for Streamlit
    return conn

# --- Helper function to get min/max dates ---
@st.cache_data # Cache the result of this function
def get_min_max_report_dates(_conn):
    """Fetches the minimum and maximum report dates from the database."""
    try:
        min_date_str = pd.read_sql_query("SELECT MIN(report_date) FROM stock_report", _conn).iloc[0, 0]
        max_date_str = pd.read_sql_query("SELECT MAX(report_date) FROM stock_report", _conn).iloc[0, 0]
        if min_date_str and max_date_str:
            min_date = pd.to_datetime(min_date_str, format='%Y%m%d').date()
            max_date = pd.to_datetime(max_date_str, format='%Y%m%d').date()
            return min_date, max_date
        else:
            # Provide a default range if table is empty or dates are null
            today = datetime.today().date()
            return today - timedelta(days=30), today
    except Exception as e:
        st.error(f"Error fetching date range: {e}")
        today = datetime.today().date()
        return today - timedelta(days=30), today

# 데이터베이스에서 데이터 가져오는 함수 (수정됨)
@st.cache_data # Cache the data loading based on inputs
def load_data(_conn, start_date_str, end_date_str):
    """Loads stock report data from the database within a specific date range."""
    try:
        # Base query structure remains the same
        query = f"""
        SELECT
            report_date,
            --stock_code, -- 주석 처리 유지 (이전 요청 반영)
            stock_name,
            report_opinion,
            stock_goal,
            last_close_price,
            close_price,
            max_price,
            CASE
                WHEN last_close_price IS NOT NULL AND last_close_price != 0 THEN ROUND(((stock_goal - last_close_price) / last_close_price) * 100)
                ELSE NULL -- Or 0, depending on how you want to handle division by zero or null
            END AS up_per,
            report_comp,
            report_analyst,
            report_analyst_grade,
            aog -- This is the achievement date column
        FROM (
            SELECT
                sr.report_date,
                sr.stock_code,
                sl.stock_name,
                sr.report_opinion,
                CAST(sr.stock_goal AS FLOAT) AS stock_goal,
                CAST((SELECT stock_price FROM stock_hst WHERE stock_code = sr.stock_code AND stock_Date = sr.report_date) AS FLOAT) AS close_price,
                CAST((SELECT stock_price FROM stock_hst WHERE stock_code = sr.stock_code AND stock_date = (SELECT MAX(stock_date) FROM stock_hst WHERE stock_code = sr.stock_code)) AS FLOAT) AS last_close_price,
                CAST((SELECT MAX(stock_max_price) FROM stock_hst WHERE stock_code = sr.stock_code AND stock_date >= sr.report_date) AS FLOAT) AS max_price,
                sr.report_analyst_grade,
                sr.report_comp,
                sr.report_analyst,
                (SELECT MIN(stock_date) FROM stock_hst WHERE stock_code = sr.stock_code AND stock_date >= sr.report_date AND CAST(stock_max_price AS INTEGER) >= CAST(sr.stock_goal AS INTEGER)) AS aog
            FROM stock_report sr
            JOIN stock_list sl ON sr.stock_code = sl.stock_code
            -- Apply date filtering within the subquery or outer query
            WHERE sr.report_date >= ? AND sr.report_date <= ?
        )
        ORDER BY report_date DESC
        """
        # Use parameterized query to prevent SQL injection
        params = (start_date_str, end_date_str)
        df = pd.read_sql_query(query, _conn, params=params)

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

# 메인 앱 (수정됨)
def main():
    st.title("📈 Find Insight - Stock Report Viewer")

    conn = get_db_connection()

    st.sidebar.header("조회 조건")

    # --- Date Range Selection ---
    min_db_date, max_db_date = get_min_max_report_dates(conn)
    default_start_date = max(min_db_date, max_db_date - timedelta(days=0))

    date_range = st.sidebar.date_input(
        "조회일자",
        value=(default_start_date, max_db_date), # Default value tuple (start, end)
        min_value=min_db_date,
        max_value=max_db_date,
        key="date_selector" # Add a key for stability
    )

    start_date = None
    end_date = None
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
    else:
        st.sidebar.warning("Please select a valid date range (start and end date).")
        st.stop() # Stop execution if date range is not valid

    # --- Load Data Based on Selected Date Range ---
    df = load_data(conn, start_date_str, end_date_str)

    if df is not None and not df.empty:
        # --- Rename Columns ---
        # Ensure the column name for achievement date ('aog' from query) is '달성일자'
        df.columns = ['일자','종목명','의견','목표가','최근종가','분석일종가','최고가','상승률','증권사','분석가','등급','달성일자']

        # --- Sidebar Filters ---

        # Company Filter
        report_comps = ["All"] + sorted(df["증권사"].astype(str).unique().tolist())
        selected_report_comp = st.sidebar.selectbox("증권사", report_comps, key="comp_selector")
        if selected_report_comp != "All":
            df_filtered = df[df["증권사"] == selected_report_comp].copy()
        else:
            df_filtered = df.copy()

        # Stock Name Filter (applied to potentially company-filtered data)
        stock_names = ["All"] + sorted(df_filtered["종목명"].astype(str).unique().tolist())
        selected_stock_name = st.sidebar.selectbox("종목선택", stock_names, key="stock_selector")
        if selected_stock_name != "All":
            # Apply filter to the already filtered dataframe
            df_filtered = df_filtered[df_filtered["종목명"] == selected_stock_name].copy()

        st.sidebar.header("", divider=True)

        # --- NEW: Achievement Date Filter Checkbox ---
        show_achieved_only = st.sidebar.checkbox("목표 달성 건만 보기", key="achieved_only_checkbox")
        if show_achieved_only:
            # Filter rows where '달성일자' is not null/NaN
            # pd.notna() correctly handles None, NaN, NaT (Not a Time)
            df_filtered = df_filtered[pd.notna(df_filtered['달성일자'])].copy()

        # --- Display Filtered Data ---
        st.subheader(f"Stock Reports from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        # Display active filters
        if selected_report_comp != "All":
            st.write(f"**증권사:** {selected_report_comp}")
        if selected_stock_name != "All":
            st.write(f"**종목명:** {selected_stock_name}")
        if show_achieved_only: # Show if the checkbox filter is active
             st.write(f"**필터:** 달성 완료")

        # Display the final filtered DataFrame
        # If you want the clickable rows and popup from the previous step,
        # you would replace st.dataframe with the AgGrid implementation here.
        # For now, keeping st.dataframe as per the current file structure.
        st.dataframe(df_filtered, use_container_width=True)

        st.info(f"Displaying {len(df_filtered)} records.")

    elif df is not None and df.empty:
        st.warning(f"No stock report data found between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}.")
    else:
        # Error handled in load_data
        st.error("Failed to load data. Please check the logs or database connection.")

if __name__ == "__main__":
    main()
