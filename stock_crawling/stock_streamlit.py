import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
# AgGrid 관련 모듈 임포트 (JsCode 추가)
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

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
            today = datetime.today().date()
            return today - timedelta(days=30), today
    except Exception as e:
        st.error(f"Error fetching date range: {e}")
        today = datetime.today().date()
        return today - timedelta(days=30), today

# 데이터베이스에서 데이터 가져오는 함수 (stock_code 포함)
@st.cache_data # Cache the data loading based on inputs
def load_data(_conn, start_date_str, end_date_str, input_stock_name):
    """Loads stock report data from the database within a specific date range."""
    try:
        query = f"""
        SELECT
            report_date,
            stock_code, -- <<< stock_code 가져오기
            stock_name,
            report_opinion,
            stock_goal,
            last_close_price,
            close_price,
            max_price,
            CASE
                WHEN last_close_price IS NOT NULL AND last_close_price != 0 THEN ROUND(((stock_goal - last_close_price) / last_close_price) * 100)
                ELSE NULL
            END AS up_per,
            report_comp,
            report_analyst,
            report_analyst_grade,
            aog -- This is the achievement date column
        FROM (
            SELECT
                sr.report_date,
                sr.stock_code, -- <<< stock_code 선택
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
            WHERE sr.report_date >= ? AND sr.report_date <= ?
        
        """
        params = (start_date_str, end_date_str)

        if input_stock_name:
            query += f" AND sl.stock_name LIKE '%{input_stock_name}%')"
        else:
            query += ")"
            
        df = pd.read_sql_query(query, _conn, params=params)

        # 숫자형 컬럼 변환
        for col in ['stock_goal', 'last_close_price', 'close_price', 'max_price', 'up_per']:
             if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# --- HTML 링크 생성 함수 제거 ---
# def make_clickable_link(row): ... (이 함수는 더 이상 필요 없음)

# 메인 앱 (수정됨)
def main():
    st.title("📈 Find Insight - Stock Report Viewer")

    conn = get_db_connection()

    st.sidebar.header("조회 조건")

    # --- Date Range Selection ---
    min_db_date, max_db_date = get_min_max_report_dates(conn)
    default_start_date = max_db_date

    date_range = st.sidebar.date_input(
        "조회일자",
        value=(default_start_date, max_db_date),
        min_value=min_db_date,
        max_value=max_db_date,
        key="date_selector"
    )

    start_date, end_date = None, None
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
    else:
        st.sidebar.warning("Please select a valid date range (start and end date).")
        st.stop()

    input_stock_name = st.sidebar.text_input("종목명")

    # --- Load Data ---
    df = load_data(conn, start_date_str, end_date_str, input_stock_name)

    if df is not None and not df.empty:
        # --- Rename Columns (stock_code 포함, 원본 종목명 유지) ---
        df.columns = ['일자','종목코드','종목명_원본','의견','목표가','최근종가','분석일종가','최고가','상승률','증권사','분석가','등급','달성일자']

        # --- Sidebar Filters ---
        st.sidebar.subheader("필터")

        # Company Filter
        report_comps = ["All"] + sorted(df["증권사"].astype(str).unique().tolist())
        selected_report_comp = st.sidebar.selectbox("증권사", report_comps, key="comp_selector")
        if selected_report_comp != "All":
            df_filtered = df[df["증권사"] == selected_report_comp].copy()
        else:
            df_filtered = df.copy()

        # Stock Name Filter (원본 이름 기준 필터링)
        stock_names = ["All"] + sorted(df_filtered["종목명_원본"].astype(str).unique().tolist())
        selected_stock_name = st.sidebar.selectbox("종목선택", stock_names, key="stock_selector")
        if selected_stock_name != "All":
            df_filtered = df_filtered[df_filtered["종목명_원본"] == selected_stock_name].copy()

        # Achievement Date Filter Checkbox
        show_achieved_only = st.sidebar.checkbox("목표 달성 건만 보기", key="achieved_only_checkbox")
        if show_achieved_only:
            df_filtered = df_filtered[pd.notna(df_filtered['달성일자'])].copy()

        # --- HTML 링크 컬럼 생성 제거 ---
        # if not df_filtered.empty: ... df_filtered['종목명_링크'] = ... (제거)

        # --- Prepare DataFrame for AgGrid Display ---
        # 표시할 컬럼 선택 및 순서 지정 (원본 종목명 사용, 종목코드는 포함하되 숨김 처리 가능)
        display_columns_order = ['일자', '종목명_원본', '종목코드', '의견', '목표가', '최근종가', '분석일종가', '최고가', '상승률', '증권사', '분석가', '등급', '달성일자']
        # 존재하는 컬럼만 선택
        df_display = df_filtered[[col for col in display_columns_order if col in df_filtered.columns]].copy()

        # --- Define JavaScript for Double Click Popup ---
        # JsCode를 사용하여 JavaScript 함수 정의
        js_code_popup = JsCode("""
            function onStockNameDoubleClick(params) {
                // 더블 클릭된 컬럼이 '종목명_원본'인지 확인 (GridOptionsBuilder에서 설정한 field 이름과 일치해야 함)
                if (params.colDef.field === '종목명_원본') {
                    // 해당 행의 데이터에서 '종목코드' 가져오기
                    const stockCode = params.data.종목코드;
                    if (stockCode) {
                        const url = `https://finance.naver.com/item/main.naver?code=${stockCode}`;
                        // 새 창(팝업)으로 열기 (너비, 높이 등 옵션 지정 가능)
                        window.open(url, '_blank', 'noopener,noreferrer,width=1000,height=700');
                    } else {
                        console.error("Stock code not found in row data:", params.data);
                        alert("종목 코드를 찾을 수 없습니다."); // 사용자에게 알림
                    }
                }
            }
        """)

        # --- Configure AgGrid ---
        gb = GridOptionsBuilder.from_dataframe(df_display)

        # '종목명_원본' 컬럼 설정: 헤더 이름 변경, HTML 렌더링 제거
        gb.configure_column("종목명_원본", header_name="종목명", width=180) # unsafe_allow_html 제거

        # '종목코드' 컬럼 설정: JavaScript에서 사용하기 위해 필요하지만, 화면에는 숨김
        gb.configure_column("종목코드", hide=True)

        # 다른 컬럼 설정 (기존과 동일)
        gb.configure_column("일자", header_name="일자", width=100, sortable=True, filter=True)
        gb.configure_column("의견", header_name="의견", width=80, sortable=True, filter=True)
        gb.configure_column("목표가", header_name="목표가", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=0, width=100, sortable=True, filter=True)
        gb.configure_column("최근종가", header_name="최근종가", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=0, width=100, sortable=True, filter=True)
        gb.configure_column("분석일종가", hide=True, header_name="분석일종가", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=0, width=110, sortable=True, filter=True)
        gb.configure_column("최고가", hide=True, header_name="최고가", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=0, width=100, sortable=True, filter=True)
        gb.configure_column("상승률", header_name="상승률(%)", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=1, width=100, sortable=True, filter=True)
        gb.configure_column("증권사", header_name="증권사", width=120, sortable=True, filter=True)
        gb.configure_column("분석가", header_name="분석가", width=100, sortable=True, filter=True)
        gb.configure_column("등급", header_name="등급", width=70, sortable=True, filter=True)
        gb.configure_column("달성일자", header_name="달성일자", width=100, sortable=True, filter=True)

        # 기본 컬럼 설정
        gb.configure_default_column(editable=False, filter=True, sortable=True, resizable=True)

        # 페이지네이션 활성화
        gb.configure_pagination(paginationAutoPageSize=True)

        # *** GridOptions에 더블 클릭 이벤트 핸들러 추가 ***
        gb.configure_grid_options(
            domLayout='normal',
            onCellDoubleClicked=js_code_popup # 정의된 JavaScript 함수 연결
        )

        # GridOptions 빌드
        gridOptions = gb.build()

        # --- Display Filtered Data Header ---
        st.subheader(f"Stock Reports from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        active_filters_str = []
        if selected_report_comp != "All":
            active_filters_str.append(f"**증권사:** {selected_report_comp}")
        if selected_stock_name != "All":
            active_filters_str.append(f"**종목명:** {selected_stock_name}")
        if show_achieved_only:
             active_filters_str.append(f"**필터:** 달성 완료")
        if active_filters_str:
            st.write(" / ".join(active_filters_str))

        # --- Display AgGrid Table ---
        if not df_display.empty:
            AgGrid(
                df_display,
                gridOptions=gridOptions,
                data_return_mode=DataReturnMode.AS_INPUT,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                fit_columns_on_grid_load=False,
                enable_enterprise_modules=False,
                height=600,
                width='100%',
                reload_data=True,
                # *** JsCode 사용 시 이 옵션을 True로 설정해야 합니다 ***
                allow_unsafe_jscode=True,
                theme="streamlit"
            )
            st.info(f"Displaying {len(df_display)} records.")
        else:
             st.warning("선택한 조건에 맞는 데이터가 없습니다.")

    elif df is not None and df.empty:
        st.warning(f"No stock report data found between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}.")
    else:
        st.error("Failed to load data. Please check the logs or database connection.")

if __name__ == "__main__":
    main()
