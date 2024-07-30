from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta
import os
from bs4 import BeautifulSoup
import platform  # 운영체제를 확인하기 위한 모듈

# MLB 팀 이름과 약어 매핑
team_abbr = {
    "Arizona D'Backs": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago White Sox": "CHW",
    "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KCR",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Yankees": "NYY",
    "New York Mets": "NYM",
    "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SDP",
    "San Francisco Giants": "SFG",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TBR",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH"
}

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

try:
    # 크롤링할 웹 페이지 URL
    today = datetime.now().strftime('%A, %B %d, %Y').replace(' 0', ' ')
    print(f"Today is: {today}")
    url = 'https://www.baseball-reference.com/leagues/MLB-schedule.shtml'
    driver.get(url)
    time.sleep(5)

    # 오늘 날짜 포맷 설정

    # class="section_content" 요소 찾기
    sections = driver.find_elements(By.CLASS_NAME, 'section_content')

    game_lines = []  # 게임 정보를 모으기 위한 리스트
    preview_links = []  # Preview 링크를 모으기 위한 리스트
    pitcher_links = []  # Pitcher 링크를 모으기 위한 리스트
    pitcher_starting_links = []  # Pitcher 링크를 모으기 위한 리스트
    starting_pitching_links = [] # Starting Pitcher 링크를 모으기 위한 리스트

    for section in sections:
        # 각 section에서 div 요소들 찾기
        divs = section.find_elements(By.TAG_NAME, 'div')

        for div in divs:

            # 각 div에서 h3 요소 찾기
            h3_elements = div.find_elements(By.TAG_NAME, 'h3')

            for h3 in h3_elements:
                # if today in h3.text or "Today's Games" in h3.text:
                if today in h3.text :
                #     날짜가 맞는 경우, 해당 div의 p 요소들 찾기
                    p_elements = div.find_elements(By.TAG_NAME, 'p')
                    for p in p_elements:
                        game_info = p.text

                        if 'Preview' in game_info:
                            game_info = game_info.replace('Preview', '').strip()
                            time_part, teams_part = game_info.split(' ', 2)[:2], game_info.split(' ', 2)[2]
                            game_time_str = ' '.join(time_part)
                            # 'TBD' 체크
                            if time_part[0] == 'TBD':
                                continue  # 'TBD'인 경우 반복 건너뛰기
                            # 원래 시간 문자열을 datetime 객체로 변환
                            game_time = datetime.strptime(game_time_str, "%I:%M %p")

                            # 한국 시간으로 변환 (UTC-4를 기준으로 변환, 필요한 경우 조정)
                            game_time_korea = (game_time + timedelta(hours=13)).strftime("%I:%M %p")

                            away, home = teams_part.split(' @ ')
                            away_abbr = team_abbr.get(away, away)  # 약어로 변환
                            home_abbr = team_abbr.get(home, home)  # 약어로 변환
                            game_line = {
                                "game_time": game_time_korea,
                                "home": home,
                                "home_abbr": home_abbr,
                                "away": away,
                                "away_abbr": away_abbr,
                                "home_pitcher": "",
                                "away_pitcher": "",
                                "home_stats": "",
                                "away_stats": ""
                            }
                            game_lines.append(game_line)

                            # Preview 링크 추출
                            try:
                                preview_link = p.find_element(By.LINK_TEXT, 'Preview').get_attribute('href')
                                preview_links.append(preview_link)
                            except:
                                pass  # Preview 링크가 없는 경우 예외 처리

    # 모든 게임 정보를 출력
    # print('\n'.join(game_lines))

    # Preview 링크 방문 및 HTML 소스 출력 후 내용 분석
    for link in preview_links:
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

                        # 투수 이름을 추출하여 game_lines에 업데이트
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

                                # game_lines 업데이트
                                for game_line in game_lines:
                                    if game_line['home_abbr'] == last_part:
                                        game_line['home_pitcher'] = pitcher_name
                                    elif game_line['away_abbr'] == last_part:
                                        game_line['away_pitcher'] = pitcher_name

                                # pitcher_links 리스트에 변환된 링크 추가
                                pitcher_links.append(modified_link)

                            except AttributeError:
                                print(f"Invalid link or missing pitcher name for link: {link}")
                                continue
                    except:
                        print(f"No element found with id: {all_sp_id}")


    # # 각 링크로 이동하여 footer no_hide_long 클래스가 있는 <a> 태그의 내용이 "Starting Pitching"인 링크들 출력
    #
    # for link_to_follow in pitcher_links:
    #     driver.get(link_to_follow)
    #     time.sleep(5)
    #     all_pitching_advanced_element = driver.find_element(By.ID, 'all_pitching_advanced')
    #     all_pitching_advanced_html = all_pitching_advanced_element.get_attribute('outerHTML')
    #
    #     # BeautifulSoup으로 HTML 파싱
    #     soup = BeautifulSoup(all_pitching_advanced_html, 'html.parser')
    #
    #     footer_links = soup.find_all('div',class_='footer no_hide_long')
    #
    #
    #
    #     for footer in footer_links:
    #         # 모든 <a> 태그 순회
    #         for link in footer.find_all('a'):
    #             if 'Starting Pitching' in link.text:  # 'Starting Pitching' 텍스트가 포함된 링크 찾기
    #                 starting_pitching_links.append("https://www.baseball-reference.com"+link['href'])
    #
    #         # 찾은 링크들 출력

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

            if w_team_data and l_team_data and gs_team_data:
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

        # 업데이트된 게임 정보 출력
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
        print(f"Home Team: **{game_line['home_abbr']}** {game_line['home_pitcher']} ({home_stats_str})")
        print(f"Away Team: **{game_line['away_abbr']}** {game_line['away_pitcher']} ({away_stats_str})")



finally:
    # WebDriver 종료
    driver.quit()
