import os
import platform
import re
import time
import csv

import svgpath2mpl  # svg.path 모듈이 필요합니다.
import matplotlib.path as mpath
from selenium.common import TimeoutException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

successfully_crawled = []
failed_to_crawl = []

# 중개사 정보를 담을 리스트
agent_info_list = []


# 정보 추출 함수 정의
def extract_agent_info(agent_info_element):
    try:
        name_element = agent_info_element.find_element(By.CLASS_NAME, "info_agent_title")
        name = name_element.find_element(By.CLASS_NAME, "title").text
        print(f"이름: {name}")

        representative_element = agent_info_element.find_element(By.CLASS_NAME, "info_agent_wrap")
        rep_dd_element = representative_element.find_element(By.CLASS_NAME, "info_agent").find_element(By.TAG_NAME,
                                                                                                       "dd")
        rep_name = rep_dd_element.text.split("소재지")[0].strip()
        print(f"대표: {rep_name}")

        location_element = rep_dd_element.find_element(By.CLASS_NAME, "tooltip_site")
        driver.execute_script("arguments[0].style.display = 'block';", location_element)
        location = location_element.text
        print(f"소재지: {location}")

        phone_number_element = representative_element.find_element(By.CLASS_NAME, "info_agent--call")
        phone_number = phone_number_element.find_element(By.CLASS_NAME, "text--number").text
        print(f"번호: {phone_number}")

        # 추출한 정보를 리스트에 추가
        agent_info_list.append({
            '이름': name,
            '대표': rep_name,
            '소재지': location,
            '번호': phone_number
        })

    except Exception as info_error:
        print(f"Failed to extract agent info: {info_error}")


# Point-in-Polygon 알고리즘 구현
def point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon
    :param point: (x, y) coordinates of the point
    :param polygon: List of (x, y) coordinates of the polygon
    :return: True if the point is inside the polygon, False otherwise
    """
    path = mpath.Path(polygon)
    return path.contains_point(point)


# SVG Path를 좌표 리스트로 변환
def svg_path_to_coordinates(svg_path):
    path = svgpath2mpl.parse_path(svg_path)
    return [(point[0], point[1]) for point in path.to_polygons()[0]]  # 다각형으로 변환


# 현재 스크립트의 디렉토리 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--start-maximized')  # 브라우저가 최대화된 상태로 실행됩니다.

# WebDriver 객체 생성
# 운영체제 확인 및 ChromeDriver 경로 설정
if platform.system() == "Darwin":  # MacOS
    chrome_driver_path = os.path.join(current_dir, 'selenium', 'chromedriver')
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
else:  # Windows 또는 기타
    chrome_driver_path = os.path.join(current_dir, 'selenium', 'chromedriver.exe')
    driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

# 크롤링할 URL 리스트
urls = ['https://new.land.naver.com/complexes?ms=37.4632,127.0539,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.514951,127.014219,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.471582,127.026744,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.4452,127.0476,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.4892509,127.0258563,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.4935754,127.0424216,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.4853348,127.0466702,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.454929,127.06378,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.5047,127.0019,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.484265,126.98864,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.488518,127.016437,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.4448,127.0641,15&a=PRE&b=B1&e=RETAIL',
        'https://new.land.naver.com/complexes?ms=37.470101,127.039888,15&a=PRE&b=B1&e=RETAIL',
        ]

# 여러 URL에 대해 순차적으로 크롤링 수행
for url in urls:
    driver.get(url)
    print(f"Opened URL: {url}")
    time.sleep(1)

    try:
        # 상단 우측 중개사 버튼 클릭
        agent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".map_controls--righttop.is-expanded .map_control--agent"))
        )
        agent_button.click()
        print("Clicked on the agent button successfully.")
        time.sleep(1)

        # marker_agent 요소를 로드하기 전까지 기다림 (최대 10초 대기)
        try:
            marker_agent_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".marker_agent"))
            )
        except TimeoutException:
            print(f"marker_agent 요소가 로드되지 않아서 URL을 건너뜁니다: {url}")
            failed_to_crawl.append(url)
            continue  # 다음 URL로 넘어감

        if not marker_agent_elements:
            print(f"No marker_agent elements found for URL: {url}")
            failed_to_crawl.append(url)
            continue
        # SVG 요소 추출
        svg_element = driver.find_element(By.XPATH,
                                          "//*[@id='complex_map']/div[1]/div/div[1]/div[3]/div[1]/*[local-name()='svg']")

        # SVG path 추출
        svg_path = svg_element.find_element(By.XPATH, ".//*[local-name()='path']").get_attribute("d")
        polygon_coordinates = svg_path_to_coordinates(svg_path)

        # marker_agent 처리
        for index, marker_agent_element in enumerate(marker_agent_elements, start=1):
            try:
                # style = marker_agent_element.get_attribute("style")
                # left = float(re.search(r'left:\s*([\d.]+)px', style).group(1))  # 소수점 포함
                # top = float(re.search(r'top:\s*([\d.]+)px', style).group(1))  # 소수점 포함

                style = marker_agent_element.get_attribute("style")

                # left와 top 값에 음수도 포함할 수 있도록 정규식을 수정
                left_match = re.search(r'left:\s*([\d.-]+)px', style)
                top_match = re.search(r'top:\s*([\d.-]+)px', style)

                # left와 top 값이 모두 정상적으로 추출되었을 때만 처리
                if left_match and top_match:
                    left = float(left_match.group(1))
                    top = float(top_match.group(1))
                else:
                    print(f"스타일 값에서 좌표를 추출하는 데 실패했습니다: {style}")
                # Point-in-Polygon 체크
                if point_in_polygon((left, top), polygon_coordinates):
                    driver.execute_script("arguments[0].setAttribute('aria-expanded', 'true');", marker_agent_element)
                    print(f"Set aria-expanded to 'true' for marker_agent element {index}.")

                    # tooltip_inner 요소 확인
                    tooltip_inner = WebDriverWait(driver, 10).until(
                        EC.visibility_of(marker_agent_element.find_element(By.CLASS_NAME, "tooltip_inner"))
                    )
                    driver.execute_script(
                        "arguments[0].style.display = 'block'; arguments[0].style.position = 'absolute'; arguments[0].style.zIndex = '99999';",
                        tooltip_inner)
                    buttons = tooltip_inner.find_elements(By.CLASS_NAME, "agent_name")
                    if buttons:
                        for button_index, button in enumerate(buttons, start=1):
                            try:
                                # 버튼의 이름을 추출
                                agent_name = button.text.strip()
                                print(f"Attempting to click button for agent: {agent_name}")
                                driver.execute_script("arguments[0].style.zIndex = '100000';", button)
                                button.click()  # 버튼 클릭
                                list_panel_element = driver.find_element(By.CLASS_NAME, "list_panel")
                                driver.execute_script("arguments[0].style.width = '99px';", list_panel_element)
                                print(f"Clicked button {button_index} in marker_agent {index} successfully.")

                                # 중개사 정보 추출
                                agent_info_element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "list_agent_info"))
                                )
                                extract_agent_info(agent_info_element)

                                # 크롤링 성공 시 이름 저장
                                successfully_crawled.append(agent_name)

                            except Exception as button_click_error:
                                print(
                                    f"Failed to click button {button_index} in marker_agent {index}: {button_click_error}")
                                # 크롤링 실패 시 이름 저장
                                failed_to_crawl.append(agent_name)
                    else:
                        print(f"No buttons found in marker_agent {index}.")

                    driver.execute_script("arguments[0].setAttribute('aria-expanded', 'false');", marker_agent_element)

            except Exception as marker_agent_error:
                print(f"An error occurred with marker_agent {index}: {marker_agent_error}")

    except Exception as e:
        print(f"An error occurred: {e}")

# 크롤링된 정보를 CSV 파일로 저장
csv_file_path = os.path.join(current_dir, 'agent_info.csv')
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
    fieldnames = ['이름', '대표', '소재지', '번호']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()  # 헤더 작성
    for agent_info in agent_info_list:
        writer.writerow(agent_info)

print(f"Agent information successfully saved to {csv_file_path}")

# WebDriver 종료 (작업 완료 후)
driver.quit()
