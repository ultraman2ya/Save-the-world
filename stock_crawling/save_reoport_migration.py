import sqlite3
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import os    

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

def get_next_sibling_text(element):
    try:
        # Playwright의 query_selector 메서드를 사용하여 다음 형제 요소를 찾습니다.
        next_sibling = element.query_selector("xpath=following-sibling::td[1]")
        if next_sibling:
            return next_sibling.text_content().strip()
        else:
            return ""
    except Exception as e:
        print(f"Error getting next sibling: {e}")
        return ""

# Playwright를 사용한 크롤링
def run():

    conn = sqlite3.connect('main_db.db')
    c = conn.cursor()
    
    # 상대경로로 변경했습니다.
    file_path = '202504.txt'  # HTML 내용을 담고 있는 텍스트 파일의 경로로 바꿔주세요.

    # 현재 작업 디렉토리를 가져옵니다.
    current_dir = os.getcwd()

    # 작업 디렉토리에 `a.htm` 파일이 있는지 확인합니다.
    if not os.path.exists(file_path):
        print(f"Error: File not found at {os.path.join(current_dir, file_path)}")
        return
    
    with sync_playwright() as p:
        # 브라우저 시작 (Chromium 사용)
        browser = p.chromium.launch(headless=True)  # headless=False로 설정하면 브라우저 창을 볼 수 있음
        page = browser.new_page()

        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
            page.set_content(html_content)

        # 모든 요소가 로드 될때까지 기다립니다.
        page.wait_for_load_state("domcontentloaded")

        grid_body = page.query_selector('#GridBody')
        
        # 스크롤을 playwright로 변경합니다.
        if grid_body:
             grid_body.scroll_into_view_if_needed()
             print('grid body get')
        else:
            print('grid body가 없습니다.')
            browser.close()
            conn.close()
            return

        # GridBody 내부의 모든 tr 요소 선택
        elements = page.query_selector_all('#GridBody tr') # 변경된 부분입니다.
        
        for element in elements:
            report_date_element = element.query_selector('td')
            report_code_element = element.query_selector('.txt1')
            report_title_element = element.query_selector('.txt2')
            report_opinion_element = element.query_selector('.c.nopre2 .gpbox')
            stock_goal_element = element.query_selector('.r.nopre2 .gpbox')
            stock_last_value_element = element.query_selector('.r.nopre2')
            stock_last_value = get_next_sibling_text(stock_last_value_element) if stock_last_value_element else ""
            report_comp_element = element.query_selector('.cle.c.nopre2')
            
            stock_goal = stock_goal_element.text_content().strip().replace(',','') if stock_goal_element else ""
            if stock_goal == "":
                continue

            report_date = report_date_element.text_content().strip().replace('/','') if report_date_element else ""
            stock_code = report_code_element.text_content().strip() if report_code_element else ""
            report_title = report_title_element.text_content().strip() if report_title_element else ""
            report_opinion = report_opinion_element.text_content().strip().replace('매수','BUY').replace('보유','HOLD') if report_opinion_element else "" # '를 공백으로 치환
            #stock_goal = stock_goal_element.text_content().strip().replace(',','') if stock_goal_element else ""
            stock_last_value = stock_last_value.replace(',','')



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
            
            print(report_date, stock_code, report_title,stock_goal, stock_last_value )
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
                        stock_code[1:len(stock_code)],
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
    conn.close()

if __name__ == "__main__":
    run()

