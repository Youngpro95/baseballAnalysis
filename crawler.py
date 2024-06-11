from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import os

# 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))

# ChromeDriver 상대 경로 설정
chrome_driver_path = os.path.join(current_dir, 'selenium', 'chromedriver.exe')

# Chrome 옵션 설정 (옵션은 필요에 따라 추가/제거 가능)
chrome_options = Options()
# chrome_options.add_argument('--headless')  # 브라우저를 화면에 띄우지 않고 실행

# ChromeDriver 서비스 설정
service = Service(chrome_driver_path)

# WebDriver 객체 생성
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # 크롤링할 웹 페이지 URL
    url = 'https://www.baseball-reference.com/leagues/MLB-schedule.shtml'
    driver.get(url)

    # 오늘 날짜 포맷 설정
    today = datetime.now().strftime('%A, %B %d, %Y')
    print(f"Today is: {today}")

    # class="section_content" 요소 찾기
    sections = driver.find_elements(By.CLASS_NAME, 'section_content')

    game_lines = []  # 게임 정보를 모으기 위한 리스트
    preview_links = []  # Preview 링크를 모으기 위한 리스트

    for section in sections:
        # 각 section에서 div 요소들 찾기
        divs = section.find_elements(By.TAG_NAME, 'div')
        for div in divs:
            # 각 div에서 h3 요소 찾기
            h3_elements = div.find_elements(By.TAG_NAME, 'h3')
            for h3 in h3_elements:
                if today in h3.text:
                    # 날짜가 맞는 경우, 해당 div의 p 요소들 찾기
                    p_elements = div.find_elements(By.TAG_NAME, 'p')
                    for p in p_elements:
                        game_info = p.text
                        if 'Preview' in game_info:
                            game_info = game_info.replace('Preview', '').strip()
                            time_part, teams_part = game_info.split(' ', 2)[:2], game_info.split(' ', 2)[2]
                            game_time_str = ' '.join(time_part)

                            # 원래 시간 문자열을 datetime 객체로 변환
                            game_time = datetime.strptime(game_time_str, "%I:%M %p")

                            # 한국 시간으로 변환 (UTC-4를 기준으로 변환, 필요한 경우 조정)
                            game_time_korea = (game_time + timedelta(hours=13)).strftime("%I:%M %p")

                            away, home = teams_part.split(' @ ')
                            game_line = f"{game_time_korea} Home : {home} Away : {away}"
                            game_lines.append(game_line)

                            # Preview 링크 추출
                            try:
                                preview_link = p.find_element(By.LINK_TEXT, 'Preview').get_attribute('href')
                                preview_links.append(preview_link)
                            except:
                                pass  # Preview 링크가 없는 경우 예외 처리

    # 모든 게임 정보를 출력
    print('\n'.join(game_lines))

    # Preview 링크 방문 및 HTML 소스 출력
    for link in preview_links:
        driver.get(link)
        time.sleep(3)  # 페이지 로드 대기 (필요에 따라 조정 가능)

        # 페이지의 HTML 소스를 가져오기
        page_html = driver.page_source



finally:
    # WebDriver 종료
    driver.quit()
