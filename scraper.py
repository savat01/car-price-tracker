# scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
import time
import os

def gather_prices():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    url = "https://dzairauto.net/Voitures-occasion-avendre"
    driver.get(url)
    time.sleep(5)  # انتظار تحميل الصفحة

    cars = []
    elements = driver.find_elements(By.CSS_SELECTOR, 'div.car-title')
    for elem in elements[:20]:
        try:
            name = elem.text
            price_elem = elem.find_element(By.XPATH, './following-sibling::*[contains(text(),"دج")]')
            price = price_elem.text
            cars.append({'name': name, 'price': price})
        except Exception as e:
            continue

    driver.quit()
    return cars

def save_to_json(data):
    os.makedirs("data", exist_ok=True)
    with open("data/latest_car_prices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    prices = gather_prices()
    save_to_json(prices)
