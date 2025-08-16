# fetcher.py (Simplified Version)
import time
import random
import logging
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# User agent pool to mimic different browsers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36',
]

def _make_session() -> requests.Session:
    """Creates a requests session with automatic retries for server errors."""
    s = requests.Session()
    # Retry on common server errors with increasing backoff time
    retries = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.verify = False # Ignore SSL certificate verification errors
    return s

def fetch_course_update_from_nuk(year: str, semester: str, sclass: str, cono: str) -> Optional[Dict]:
    """
    Fetches the enrollment status for a single course using a robust 2-step process.
    Returns a dict: {"confirmed":..., "online_count":..., "remaining":...} or None on failure.
    """
    session = _make_session()
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://course.nuk.edu.tw/QueryCourse/QueryCourse.asp'
    }

    form_url = "https://course.nuk.edu.tw/QueryCourse/QueryCourse.asp"
    list_url = "https://course.nuk.edu.tw/QueryCourse/QueryResult.asp"
    
    for attempt in range(10):
        try:
            # Step 1: Visit the form page to get session cookies and hidden inputs
            logger.info(f"Attempt {attempt + 1}: Fetching hidden inputs from form page...")
            form_resp = session.get(form_url, headers=headers, timeout=15)
            form_resp.encoding = 'big5'
            soup = BeautifulSoup(form_resp.text, 'html.parser')
            
            hidden_inputs = {}
            inputs = soup.find_all('input', {'type': 'hidden'})
            for hidden in inputs:
                name = hidden.get('name')
                if name:
                    hidden_inputs[name] = hidden.get('value', '')
            
            # Step 2: Submit the search with the complete payload
            payload = {
                'OpenYear': year,
                'Helf': semester,
                'Pclass': 'A',
                'Sclass': sclass,
                'Page': '1'
            }
            payload.update(hidden_inputs)
            
            logger.info(f"Attempt {attempt + 1}: Submitting search for Sclass={sclass}...")
            r = session.post(list_url, data=payload, headers=headers, timeout=15)
            r.encoding = 'utf-8' # Result page is utf-8
            soup = BeautifulSoup(r.text, 'html.parser')

            table = soup.find('table', attrs={'border': '1', 'style': 'font-size: 10pt'})
            if not table:
                raise ValueError('No course table found in search result.')

            rows = table.find_all('tr')[2:]
            for row in rows:
                cols = [c.get_text(strip=True) for c in row.find_all('td')]
                if len(cols) >= 25 and cols[2] == cono:
                    result = {
                        "confirmed": cols[11],
                        "online_count": cols[12],
                        "remaining": cols[13]
                    }
                    logger.info(f"Successfully found course {cono}")
                    return result # Success, exit the function

            # If the loop finishes, the course was not found in the results for this attempt
            raise ValueError(f"Course {cono} not found in search results on attempt {attempt + 1}")

        except Exception as e:
            logger.warning(f"Fetch attempt {attempt + 1} failed: {e}")
            if attempt < 2: # If this was not the last attempt
                sleep_time = (attempt + 1) * 2 + random.random()
                logger.info(f"Waiting for {sleep_time:.1f} seconds before retrying...")
                time.sleep(sleep_time)
            continue # Go to the next attempt

    # If all attempts fail, return None
    logger.error(f"Failed to fetch data for course {cono} after multiple attempts.")
    return None