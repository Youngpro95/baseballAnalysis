from abbr_data import team_abbr
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import os
from bs4 import BeautifulSoup
import platform  # 운영체제를 확인하기 위한 모듈
import json

from schedule_data import gameListData

# 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))

# 운영체제 확인 및 ChromeDriver 경로 설정
if platform.system() == "Darwin":  # MacOS
    chrome_driver_path = os.path.join(current_dir, 'selenium', 'chromedriver')
else:  # Windows 또는 기타
    chrome_driver_path = os.path.join(current_dir, 'selenium', 'chromedriver.exe')

# Chrome 옵션 설정 (옵션은 필요에 따라 추가/제거 가능)
chrome_options = Options()
# chrome_options.add_argument('--headless')  # 브라우저를 화면에 띄우지 않고 실행

# ChromeDriver 서비스 설정
service = Service(chrome_driver_path)

# WebDriver 객체 생성
driver = webdriver.Chrome(service=service, options=chrome_options)

game_lines = []  # 게임 정보를 모으기 위한 리스트
pitcher_links = []


def fetch_pitcher_info(games):
    global pitcher_links
    for game in games:
        link = game['preview_link']
        driver.get(link)
        time.sleep(3)  # 페이지 로드 대기 (필요에 따라 조정 가능)

        # class="grid_wrapper" 요소 찾기
        grid_wrapper_elements = driver.find_elements(By.CLASS_NAME, 'grid_wrapper')

        for grid_wrapper_element in grid_wrapper_elements:
            # grid_wrapper의 id 추출
            grid_wrapper_id = grid_wrapper_element.get_attribute('id')
            if grid_wrapper_id:
                # id를 '_'로 split하여 마지막 부분 추출
                id_parts = grid_wrapper_id.split('_')
                if id_parts:
                    last_part = id_parts[-1]
                    all_sp_id = f"sp_{last_part}_sh"

                    # all_sp_id 요소 찾기
                    try:
                        all_sp_element = driver.find_element(By.ID, all_sp_id)
                        all_sp_html = all_sp_element.get_attribute('outerHTML')

                        # all_sp_html에서 <a> 태그의 href 속성 값 추출
                        soup = BeautifulSoup(all_sp_html, 'html.parser')
                        links = [a['href'] for a in soup.select(f"#{all_sp_id} a[href]")]

                        # 투수 이름을 추출하여 game 업데이트
                        for link in links:
                            if not link.strip():  # 링크가 공백인 경우 건너뜀
                                continue

                            try:
                                # 투수 이름 추출
                                pitcher_name = soup.find('a', href=link).text.strip()
                                if not pitcher_name:
                                    print(f"Empty pitcher name found for link: {link}")
                                    continue

                                # 링크 변환
                                modified_link = link.replace('.shtml', '-pitch.shtml#all_pitching_starter')

                                # game 업데이트
                                if game['home_abbr'] == last_part:
                                    game['home_pitcher'] = pitcher_name
                                elif game['away_abbr'] == last_part:
                                    game['away_pitcher'] = pitcher_name

                                # pitcher_links 리스트에 변환된 링크 추가
                                pitcher_links.append(modified_link)

                            except AttributeError:
                                print(f"Invalid link or missing pitcher name for link: {link}")
                                continue
                    except:
                        print(f"No element found with id: {all_sp_id}")


def fetch_starting_pitching_stats():
    global pitcher_links, game_lines  # 전역 변수 pitcher_links 사용

    # 각 Starting Pitching 링크로 이동하여 필요한 정보 추출
    for sp_link in pitcher_links:
        driver.get(sp_link)
        time.sleep(5)
        soup_sp = BeautifulSoup(driver.page_source, 'html.parser')

        # 페이지 제목 추출
        page_title = soup_sp.title.text.strip() if soup_sp.title else 'No Title'
        pitcher_name = page_title.split(' Pitching Stats')[0].strip()

        # id가 pitching_starter.2024인 tr 요소 찾기
        pitching_starter_tr = soup_sp.find('tr', id='pitching_starter.2024')
        if pitching_starter_tr:
            # data-stat가 W_team, L_team, GS인 값 추출
            w_team_data = pitching_starter_tr.find('td', {'data-stat': 'W_team'})
            l_team_data = pitching_starter_tr.find('td', {'data-stat': 'L_team'})
            gs_team_data = pitching_starter_tr.find('td', {'data-stat': 'GS'})
            qs_team_data = pitching_starter_tr.find('td', {'data-stat': 'QS'})

            if w_team_data and l_team_data and gs_team_data and qs_team_data:
                try:
                    w_team_value = int(w_team_data.text)
                    l_team_value = int(l_team_data.text)
                    gs_team_value = int(gs_team_data.text)
                    qs_team_value = int(qs_team_data.text)

                    if gs_team_value != 0:  # ZeroDivisionError 방지
                        win_rate = (w_team_value / gs_team_value) * 100
                        pitcher_stats = {
                            "W_team": w_team_value,
                            "L_team": l_team_value,
                            "GS": gs_team_value,
                            "Win_rate": win_rate,
                            "QS": qs_team_value,
                        }
                        for game_line in game_lines:
                            if game_line['home_pitcher'] == pitcher_name:
                                game_line['home_stats'] = pitcher_stats
                            elif game_line['away_pitcher'] == pitcher_name:
                                game_line['away_stats'] = pitcher_stats
                    else:
                        print(f"{page_title} - GS is zero, cannot calculate win rate for {sp_link}")

                except ValueError:
                    print(
                        f"{page_title} - Invalid data found in {sp_link}: W_team = {w_team_data.text}, L_team = {l_team_data.text}, GS = {gs_team_data.text} QS = {qs_team_data.text}")
            else:
                print(f"{page_title} - Not all required data found in {sp_link}")

        else:
            print(f"{page_title} - No pitching_starter.2024 row found in {sp_link}")


def print_games_for_today(game_list_data, today_date):
    global game_lines

    for game_day in game_list_data:
        for date, games in game_day.items():
            if date == today_date:  # 날짜가 오늘 날짜와 일치하면
                game_lines.extend(games)  # 일치하는 게임들을 game_lines에 추가

    # 이제 game_lines에 오늘 날짜의 게임들이 저장됨
    if game_lines:
        print(f"Games for {today_date}:")

        fetch_pitcher_info(game_lines)  # 투수 정보 수집
        fetch_starting_pitching_stats()  # 투수 스탯 수집

        for game_line in game_lines:
            home_stats = game_line['home_stats']
            away_stats = game_line['away_stats']

            if home_stats:
                home_stats_str = f"경기수: {home_stats['GS']} 승리: {home_stats['W_team']} 패배: {home_stats['L_team']}  승률: {home_stats['Win_rate']:.0f}% QS : {home_stats['QS']}"
            else:
                home_stats_str = "N/A"

            if away_stats:
                away_stats_str = f"경기수: {away_stats['GS']} 승리: {away_stats['W_team']} 패배: {away_stats['L_team']} 승률: {away_stats['Win_rate']:.0f}% QS : {away_stats['QS']}"
            else:
                away_stats_str = "N/A"

            print("--------------------")
            print(f"Game Time: {game_line['game_time']}")
            print(f"Home Team: *{game_line['home_abbr']}* {game_line['home_pitcher']} ({home_stats_str})")
            print(f"Away Team: *{game_line['away_abbr']}* {game_line['away_pitcher']} ({away_stats_str})")

        for game in game_lines:
            print(f"Game Time: {game['game_time']}")
            print(f"Home Team: {game['home']} ({game['home_abbr']})")
            print(f"Away Team: {game['away']} ({game['away_abbr']})")
            print(f"Home Pitcher: {game['home_pitcher']}")
            print(f"Away Pitcher: {game['away_pitcher']}")
            print(f"Home Stats: {game['home_stats']}")
            print(f"Away Stats: {game['away_stats']}")
            print(f"Preview Link: {game['preview_link']}")
            print("-" * 60)
    else:
        print("No games found for today.")


today = datetime.now().strftime('%A, %B %d, %Y').replace(' 0', ' ')
print_games_for_today(gameListData, today)
