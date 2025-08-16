# scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from .parser import parse_grades_html
from .calculator import calculate_deficit_with_department
from .config import COURSE_CODE_MAPPING
from .credit_deficit_calculator import get_department_from_course_prefix


def run_selenium_process():
    LOGIN_URL = "https://aca.nuk.edu.tw/Student2/login.asp"
    SUCCESS_URL_KEYWORD = "Menu.asp"
    SCORE_QUERY_URL = "https://aca.nuk.edu.tw/Student2/SO/ScoreQuery.asp"
    
    driver = None
    try:
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.get(LOGIN_URL)

        wait = WebDriverWait(driver, 300)
        wait.until(EC.url_contains(SUCCESS_URL_KEYWORD))
        
        print("使用者登入成功！")
        driver.minimize_window()
        print("瀏覽器視窗已最小化，繼續在背景執行...")

        driver.get(SCORE_QUERY_URL)
        print(f"背景已跳轉至：{SCORE_QUERY_URL}")

        page_html = driver.page_source
        
        grades_data = parse_grades_html(page_html)
        print("原始成績資料解析完成！")
        
        # 先進行初步分類以判斷科系
        from .calculator import categorize_and_calculate_credits
        initial_categorized = categorize_and_calculate_credits(grades_data, COURSE_CODE_MAPPING)
        
        # 推測學生科系
        department = get_department_from_course_prefix(initial_categorized)
        print(f"推測學生科系：{department}")
        
        # 使用科系資訊計算學分缺額
        if department:
            results = calculate_deficit_with_department(grades_data, department, COURSE_CODE_MAPPING)
        else:
            results = {
                'categorized_credits': initial_categorized,
                'current_credits_summary': {},
                'deficit_analysis': {
                    'status': 'unknown_department',
                    'message': '無法推測學生科系，請手動指定',
                    'department': '未知',
                    'deficit_details': {}
                }
            }
        
        print("成績分類與學分統計完成！")
        
        return {"status": "success", "message": "成績獲取與分類成功！", "data": results}

    except TimeoutException:
        return {"status": "error", "message": "等待登入超時。"}
    except Exception as e:
        return {"status": "error", "message": f"發生未知錯誤: {e}"}
    finally:
        if driver:
            driver.quit()
        print("瀏覽器已關閉，流程結束。")