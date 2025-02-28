import sqlite3
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def extract_comp(html_content,html_cnt):
    soup = BeautifulSoup(html_content, 'html.parser')
    span_element = soup.find('span', class_='gpbox')

    if span_element:
        # <br> 태그를 기준으로 텍스트를 분리합니다.
        parts = span_element.get_text(separator='<br>').split('<br>')
        if len(parts) > 1:
            return_name = parts[html_cnt].strip()  # 두 번째 부분이 분석가 이름입니다.
            return return_name
        else:
            if html_cnt == 1:
                return_name = ""
                return return_name
    return None


def extract_analyst_grade(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    img_element = soup.find('img', class_='gp_img')
    
    if img_element:
        if 'best' in img_element.get('class',[]):
            return 'B'
        else:
            return ''
    else :
        return ''

# Playwright를 사용한 크롤링
def run():

    conn = sqlite3.connect('main_db.db')
    c = conn.cursor()

    with sync_playwright() as p:
        # 브라우저 시작 (Chromium 사용)
        browser = p.chromium.launch(headless=True)  # headless=False로 설정하면 브라우저 창을 볼 수 있음
        page = browser.new_page()

        # 크롤링할 URL
        # url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp'
        url = 'C:/backup/make_data/stock_crawling/a.htm'
        page.goto(url)

        # 페이지가 완전히 로드될 때까지 대기 (선택적)
        page.wait_for_load_state('networkidle')

        # GridBody 요소 선택
        grid_body = page.query_selector('#GridBody')
        
        #스크롤
        grid_body.scroll_into_view_if_needed()

        # GridBody 내부의 모든 tr 요소 선택
        elements = grid_body.query_selector_all('tr')
        
        for element in elements:
            report_date = element.query_selector('td').text_content().strip().replace('/','')
            stock_code = element.query_selector('.txt1').text_content().strip()
            report_title = element.query_selector('.txt2').text_content().strip()
            report_opinion = element.query_selector('.c.nopre2 .gpbox').text_content().strip()
            stock_goal = element.query_selector('.r.nopre2 .gpbox').text_content().strip().replace(',','')
            stock_last_value = element.query_selector('.r').text_content().strip().replace(',','')

            # report_comp 요소는 동일한 위치에 있음.
            report_comp_element = element.query_selector('.cle.c.nopre2')
            report_comp_html = report_comp_element.inner_html() if report_comp_element else ""
            report_comp = ""
            report_analyst = ""
            report_analyst_grade = ""

            if report_comp_element:
                report_comp = extract_comp(report_comp_html,0)
                report_analyst = extract_comp(report_comp_html,1)
                report_analyst_grade = extract_analyst_grade(report_comp_html)
            
            c.execute('''
                INSERT OR REPLACE INTO stock_report (report_date,
                                                   stock_code,
                                                   report_comp,
                                                   report_analyst,
                                                   report_opinion,
                                                   stock_goal,
                                                   stock_last_value,
                                                   report_analyst_grade,
                                                   report_title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                        report_date,
                        stock_code,
                        report_comp,
                        report_analyst,
                        report_opinion,
                        stock_goal,
                        stock_last_value,
                        report_analyst_grade,
                        report_title
                     )
            )

        # 브라우저 종료
        browser.close()
    conn.commit()

if __name__ == "__main__":
    run()

