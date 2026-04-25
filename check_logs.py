from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def get_browser_errors():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    try:
        print("Navigating to http://localhost:8502")
        driver.get("http://localhost:8502")
        time.sleep(5)  # Wait for load
        
        print("Console logs:")
        for entry in driver.get_log('browser'):
            print(entry)
    finally:
        driver.quit()

if __name__ == "__main__":
    get_browser_errors()
