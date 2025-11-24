from playwright.sync_api import sync_playwright
import json
import os
import re


def extract_price_only_before_million(text):
    """يستخرج الرقم فقط الذي يأتي قبل كلمة مليون"""
    if not text:
        return None

    match = re.search(r'(\d+(\.\d+)?)\s*مليون', text)
    if match:
        return match.group(1)  # الرقم فقط كـ string
    return None


def scroll_and_wait(page, scrolls=3):
    """التمرير وانتظار تحميل العناصر"""
    for i in range(scrolls):
        page.evaluate(f"window.scrollTo(0, {i * 500});")
        page.wait_for_timeout(1500)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    page.wait_for_timeout(2000)
    page.evaluate("window.scrollTo(0, 0);")
    page.wait_for_timeout(1000)


def scrape_dzairauto(page):
    """استخراج البيانات من DzairAuto"""
    cars = []
    try:
        url = "https://dzairauto.net/Voitures-occasion-avendre"
        print(f"\n📍 DzairAuto: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)
        scroll_and_wait(page)
        
        selectors = [
            "div.d-flex.justify-content-end.text-right",
            "div[class*='d-flex'][class*='justify-content-end'][class*='text-right']",
            ".d-flex.justify-content-end.text-right"
        ]
        
        listings = []
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    listings = elements
                    print(f"  تم العثور على {len(elements)} عنصر باستخدام: {selector}")
                    break
            except Exception:
                continue
        
        if not listings:
            print("  ⚠️ لم يتم العثور على أي عناصر تحتوي على class='d-flex justify-content-end text-right'")
            return []
        
        for idx, listing in enumerate(listings[:50], 1):
            try:
                content = listing.inner_text().strip()
                html_content = listing.inner_html()
                price = extract_price_only_before_million(content)
                if not price:
                    price = "غير متوفر"
                
                name = None
                
                try:
                    title_elem = listing.evaluate("""
                        el => {
                            const parent = el.closest('div[class*="card"], article, div[class*="item"]');
                            if (parent) {
                                const title = parent.querySelector('h5, h4, h3, h2, a, .title, [class*="title"]');
                                return title ? title.innerText.trim() : null;
                            }
                            return null;
                        }
                    """)
                    if title_elem:
                        name = title_elem
                except:
                    pass
                
                if not name:
                    # استخدم أول سطر من النص كاسم تقريبي
                    lines = content.split('\n')
                    name = lines[0].strip()[:100] if lines else content[:100]
                
                car_data = {
                    "content": content,
                    "price": price,
                    "source": "DzairAuto"
                }
                
                if name:
                    car_data["name"] = name
                
                if html_content:
                    car_data["html"] = html_content[:500]
                
                cars.append(car_data)
                
                if idx <= 3:
                    print(f"  [{idx}] المحتوى: {content[:80]}...")
                    print(f"      السعر: {price}")
                
            except Exception as e:
                print(f"  خطأ في معالجة عنصر {idx}: {e}")
                continue
        
        print(f"  ✅ جمعت {len(cars)} عنصر من DzairAuto")
        return cars
    except Exception as e:
        print(f"  ❌ خطأ في DzairAuto: {e}")
        import traceback
        traceback.print_exc()
        return []


def gather_prices_from_dzairauto(headless=True):
    """جمع بيانات السيارات من DzairAuto فقط"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        cars = scrape_dzairauto(page)
        browser.close()
        return cars


def save_to_json(data, filename="latest_car_prices.json"):
    os.makedirs("car-price-tracker/data", exist_ok=True)
    filepath = os.path.join("car-price-tracker", "data", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


if __name__ == "__main__":
    print("=" * 70)
    print("🚗 بدء جمع بيانات السيارات من موقع DzairAuto")
    print("=" * 70)

    all_cars = gather_prices_from_dzairauto(headless=True)  # في GitHub Actions، نستخدم headless=True

    print("\n" + "=" * 70)
    if all_cars:
        print(f"✅ تم جمع {len(all_cars)} سيارة من DzairAuto!")
        for i, car in enumerate(all_cars[:10], 1):
            print(f"  {i}. {car.get('name', 'غير معروف')}")
            print(f"     السعر: {car.get('price', 'غير متوفر')}")
    else:
        print("❌ لم يتم جمع أي بيانات.")

    filepath = save_to_json(all_cars)
    print(f"\n💾 تم حفظ البيانات في: {filepath}")
