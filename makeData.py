import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import platform
import json
from datetime import datetime, timedelta

# 크롬 드라이버 설정 (파일 경로는 각자에 맞게 조정)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 운영체제 확인 및 ChromeDriver 경로 설정
if platform.system() == "Darwin":  # MacOS
    chrome_driver_path = os.path.join(current_dir, 'selenium', 'chromedriver')
else:  # Windows 또는 기타
    chrome_driver_path = os.path.join(current_dir, 'selenium', 'chromedriver.exe')

service = Service(chrome_driver_path)

# WebDriver 설정
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # 브라우저 화면 표시 없이 실행
driver = webdriver.Chrome(service=service, options=options)

# Baseball Reference 스케줄 페이지로 이동
url = "https://www.baseball-reference.com/leagues/MLB-schedule.shtml"
driver.get(url)

# 페이지 로드 대기
time.sleep(3)

# 페이지 소스 가져오기
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

# 게임 데이터를 담을 리스트
game_list_data = []

# class가 'section_content'인 요소에서 각 날짜에 해당하는 게임 정보 파싱
sections = soup.find_all('div', class_='section_content')

for section in sections:
    divs = section.find_all('div')

    for div in divs:
        h3_tag = div.find('h3')  # 날짜 정보가 있는 h3 태그
        if not h3_tag:
            continue

        date_str = h3_tag.text.strip()  # 날짜 추출

        # 게임 정보가 있는 'p.game' 요소들을 찾아 파싱
        games = []
        p_elements = div.find_all('p', class_='game')

        for p in p_elements:
            # 경기 시간 추출
            game_time_str = p.find('strong').text.strip() if p.find('strong') else ""

            if game_time_str:
                try:
                    # 원래 시간 문자열을 datetime 객체로 변환
                    game_time = datetime.strptime(game_time_str, "%I:%M %p")
                    # 한국 시간으로 변환 (UTC-4를 기준으로 변환, 필요한 경우 조정)
                    game_time_korea = (game_time + timedelta(hours=13)).strftime("%I:%M %p")
                except ValueError:
                    game_time_korea = game_time_str  # 변환 실패 시 원래 시간 문자열 사용
            else:
                game_time_korea = ""

            # 팀 정보 추출 (첫 번째 a 태그가 원정, 두 번째 a 태그가 홈)
            team_tags = p.find_all('a')
            if len(team_tags) >= 2:
                away_team = team_tags[0].text.strip()  # 원정 팀
                away_abbr = team_tags[0]['href'].split('/')[2]  # 원정 팀 약어
                home_team = team_tags[1].text.strip()  # 홈 팀
                home_abbr = team_tags[1]['href'].split('/')[2]  # 홈 팀 약어
            else:
                away_team = away_abbr = home_team = home_abbr = ""

            # Preview 링크 추출 (세 번째 a 태그가 있을 경우)
            preview_link = ""
            em_tag = p.find('em')
            if em_tag and em_tag.find('a'):
                preview_link = "https://www.baseball-reference.com" + em_tag.find('a')['href']

            # 게임 정보를 리스트에 저장
            game_info = {
                "game_time": game_time_korea,
                "home": home_team,
                "home_abbr": home_abbr,
                "away": away_team,
                "away_abbr": away_abbr,
                "home_pitcher": "",
                "away_pitcher": "",
                "home_stats": "",
                "away_stats": "",
                "preview_link": preview_link
            }
            games.append(game_info)

        # 날짜와 함께 게임 정보를 추가
        if games:
            game_list_data.append({date_str: games})

# game_list_data를 JSON 형식으로 schedule_data.py에 저장
schedule_data_file = os.path.join(current_dir, 'schedule_data.py')
with open(schedule_data_file, 'w', encoding='utf-8') as file:
    file.write(f"gameListData = {json.dumps(game_list_data, indent=4)}")

# WebDriver 종료
driver.quit()

print(f"Game data successfully saved to {schedule_data_file}")
