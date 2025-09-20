import csv
import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

URL = "https://www.coursera.org/programs/coursera-para-el-futuro-del-trabajo-th3j0/browse?source=search&query=AI"
RESULTS = "ul#searchResults"

def setup_driver(headless: bool = True):
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,1400")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=opts)
    driver.wait = WebDriverWait(driver, 20)
    return driver

def extract_current_page_titles(driver):
    driver.find_element(By.CSS_SELECTOR, RESULTS)
    h3s= driver.find_elements(By.CSS_SELECTOR, 'h3.cds-CommonCard-title')
    return [h.text.strip() for h in h3s if h.text.strip()]

def click_next_page(driver) -> bool:
    """Click the 'next page' button if enabled; return True if clicked."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        next_btn = driver.find_element(
        By.CSS_SELECTOR,
        'nav[aria-label="pagination"] li.cds-pagination-navControl:last-child button:not([disabled])'
    )
    except NoSuchElementException:
        return False
    time.sleep(2.5)
    driver.execute_script("arguments[0].click();", next_btn)  # JS click avoids overlays
    print("✅ 'Next' btn clicked.")
    time.sleep(0.8 + random.random() * 0.7)
    return True

def extract_course_titles(html, max_pages: int=3, headless:bool=True):
    driver = setup_driver(headless=headless)
    try:
        driver.get(html)

        driver.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, RESULTS)))

        all_titles: list[str]=[]

        for _ in range(max_pages):
            titles = extract_current_page_titles(driver)
            print(f"{_} Page - First title: {titles[0]}")
            if not titles:
                break

            # If we didn't get any new titles, stop
            if set(titles).issubset(set(all_titles)):
                print("⚠️ No new titles found after clicking next.")
                break

            all_titles.extend(titles)
            print(f"📈 Collected {len(all_titles)} total titles")

            # Next page btn
            print("👉 Clicking 'Next' btn.")
            last_titles = extract_current_page_titles(driver)
            if not click_next_page(driver):
                print("❌ No more pages to click.")
                break

            # Wait until the previous first card becomes stale or content changes

            time.sleep(20)
            driver.execute_script("window.scrollTo(0,0);")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

            new_tiles = extract_current_page_titles(driver)
            if new_tiles and last_titles and new_tiles[0] != last_titles[0]:
                print("✅ Page changed successfully.")
            else:
                print("⚠️ Warning: First title did not change after clicking next.")

        # De-dup
        seen = set()
        deduped = []
        for t in all_titles:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        return deduped

    except Exception as e:
        print(f"Error: {e}")
        return [] # return empty list on error

    finally:
        driver.quit()
    

if __name__ == '__main__':
    print("💾 Starting 'Extract course titles' program")

    titles = extract_course_titles(URL, max_pages=6, headless=True)
    print("Titles:", titles)
    downloaded_file = "coursera_courses.csv"
    if titles:
        with open(downloaded_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["title"])
            for t in titles:
                writer.writerow([t])
            print(" ✔️ Titles saved in:", downloaded_file)
    else:
        print(" ❌ No titles were extracted. Nothing saved.")
    print("✅ Program complete.")
