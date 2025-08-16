# acquire_data.py 
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import warnings
from urllib3.exceptions import InsecureRequestWarning

def acquire_all_courses():
    """
    This definitive script uses a post-parsing check to reliably handle 
    the server's deceptive empty pages and will not stop until it gets all data.
    """
    print("--- Launching the Definitive Data Acquisition Script ---")
    print("This script will run slowly and patiently to ensure all data is captured.")

    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    BASE_URL = "https://course.nuk.edu.tw/QueryCourse/QueryResult.asp"
    OUTPUT_FILENAME = "courses_final.json"
    
    # --- Define Query Parameters Here ---
    YEAR = '114'
    SEMESTER = '1'
    PCLASS = 'A'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded', 'Origin': 'https://course.nuk.edu.tw',
        'Referer': 'https://course.nuk.edu.tw/QueryCourse/QueryCourse.asp'
    }

    # -- Step 1: Reliably determine the total number of pages --
    max_page = 0
    while max_page == 0:
        try:
            print("\nInvestigating total number of pages...")
            session = requests.Session()
            session.verify = False
            payload_page1 = {'OpenYear': YEAR, 'Helf': SEMESTER, 'Pclass': PCLASS, 'Page': '1'}
            resp_page1 = session.post(BASE_URL, data=payload_page1, headers=headers, timeout=45)
            resp_page1.encoding = 'utf-8'
            soup_page1 = BeautifulSoup(resp_page1.text, 'html.parser')
            page_buttons = soup_page1.find_all('input', {'type': 'button', 'onclick': True})
            page_numbers = [int(btn['value']) for btn in page_buttons if btn.get('value') and btn.get('value').isdigit()]
            if not page_numbers: raise ValueError("Could not find page number buttons on page 1. Retrying.")
            max_page = max(page_numbers)
            print(f"Investigation complete. Total pages found: {max_page}")
        except Exception as e:
            print(f" > Failed to determine total pages: {e}. Retrying in 15 seconds...")
            time.sleep(2)

    # -- Step 2: Loop through all pages with the definitive retry logic --
    all_courses = []
    for page in range(1, max_page + 1):
        page_completed = False
        while not page_completed:
            try:
                print(f"\nAttempting to fetch page {page}/{max_page}...")
                session = requests.Session()
                session.verify = False
                payload = {'OpenYear': YEAR, 'Helf': SEMESTER, 'Pclass': PCLASS, 'Page': str(page)}
                resp = session.post(BASE_URL, data=payload, headers=headers, timeout=45)
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # --- THIS IS THE CORRECTED LINE ---
                table = soup.find('table', attrs={'border': '1', 'style': 'font-size: 10pt'})

                if not table: raise ValueError("Server response did not contain the course table.")

                rows = table.find_all('tr')[2:]
                page_courses = []
                for row in rows:
                    cols_tags = row.find_all('td')
                    if len(cols_tags) < 25: continue
                    cols = [c.get_text(strip=True) for c in cols_tags]
                    teacher_names = cols_tags[14].get_text(separator=', ', strip=True)
                    
                    course = {
                        "id": f"{cols[2]}-{teacher_names}", "department": cols[0].upper(), "code": cols[2], "dept_code": cols[4], 
                        "grade": cols[5], "class_type": cols[6], "name": cols[7], "credits": cols[8], "type": cols[9], 
                        "limit": cols[10], "confirmed": cols[11], "online_count": cols[12], "remaining": cols[13], 
                        "teacher": teacher_names, "classroom": cols[15],
                        "time": {"Mon": [t.strip() for t in cols[16].split(',') if t.strip()],"Tue": [t.strip() for t in cols[17].split(',') if t.strip()],"Wed": [t.strip() for t in cols[18].split(',') if t.strip()],"Thu": [t.strip() for t in cols[19].split(',') if t.strip()],"Fri": [t.strip() for t in cols[20].split(',') if t.strip()],"Sat": [t.strip() for t in cols[21].split(',') if t.strip()],"Sun": [t.strip() for t in cols[22].split(',') if t.strip()],},
                        "prerequisites": cols[23], "note": cols[24],
                    }
                    page_courses.append(course)
                
                if len(page_courses) == 0 and page <= max_page:
                    raise ValueError("Server returned a deceptive empty page.")

                print(f"  > Success! Page {page} fetched with {len(page_courses)} courses.")
                all_courses.extend(page_courses)
                page_completed = True

            except Exception as e:
                wait_time = 0.1
                print(f"  > Failed to process page {page}: {e}")
                print(f"  > Waiting {wait_time:.0f} seconds before retrying...")
                time.sleep(wait_time)
        
        if page <= max_page:
            human_delay = 0.1
            print(f"  > Page complete. Pausing for {human_delay:.1f} seconds...")
            time.sleep(human_delay)
    
    # --- Create the final structured data object ---
    final_data = {
        "query_params": {
            "OpenYear": YEAR,
            "Helf": SEMESTER
        },
        "courses": all_courses
    }

    print(f"\nTask Complete! Total courses fetched: {len(all_courses)} ")
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print(f"Success! The definitive course data has been saved to '{OUTPUT_FILENAME}'.")

if __name__ == "__main__":
    acquire_all_courses()