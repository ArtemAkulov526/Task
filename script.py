from collections import deque
import json, asyncio
from playwright.async_api import async_playwright

# At first i will collect urls of all items on the menu
# this will allow me to build links to go through pages and scrape required information quicker

item_ids = deque()

async def get_items(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to the URL
        response = await page.goto(url)
        if not response or response.status != 200:
            raise Exception(f"Failed to fetch page: {url} (status code {response.status if response else 'N/A'})")

        # Wait for <li> elements to appear
        await page.wait_for_selector('a[href]')

        # Find all <a> elements with an href attribute
        anchors = await page.query_selector_all('a[href]')

        for a in anchors:
            href = await a.get_attribute('href')
            if href and '/product/' in href:
                item_ids.append(href)

        print(f"Saved {len(item_ids)} item IDs to deque")
        await browser.close()

# using previously collected urls i will build links to each product and collect information

async def get_info(OUTPUT_FILE):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        results = []

        while item_ids:
            id = item_ids.popleft()
            url = f'https://www.mcdonalds.com{id}#accordion-29309a7a60-item-9ea8a10642'

            try:
                await page.goto(url)

                title_el = await page.query_selector("span.cmp-product-details-main__heading-title")
                title = (await title_el.text_content()).strip() if title_el else "Немає назви"

                desc = await page.query_selector("div.cmp-text")
                text = await desc.text_content() if desc else "Немає опису"
                description = text.replace('\xa0', ' ').strip()

                await page.wait_for_selector("li.cmp-nutrition-summary__heading-primary-item")
                nutrition_items = await page.query_selector_all("li.cmp-nutrition-summary__heading-primary-item")

                nutrition_data = {}
                for item in nutrition_items:
                    metric_el = await item.query_selector("span.metric > span[aria-hidden='true']")
                    metric = (await metric_el.text_content()).strip() if metric_el else "Немає назви"

                    value_el = await item.query_selector("span.value > span[aria-hidden='true']")
                    value = (await value_el.text_content()).strip() if value_el else "Не знайдено значення"

                    if metric and value:
                        nutrition_data[metric] = value
                
                items = await page.query_selector_all('div.cmp-nutrition-summary--nutrition-table li.label-item')

                for item in items:
                    metric = await item.query_selector('span.metric')
                    m = (await metric.inner_text()).strip().rstrip(':') if metric else "Немає назви"
                    
                    value = await item.query_selector('span.value span[aria-hidden="true"]')
                    v = (await value.inner_text()).strip() if value else "Не знайдено значення"
                    
                    if m and v:
                        nutrition_data[m] = v

                clean_data = {}
                for key, value in nutrition_data.items():
                    clean_key = ' '.join(key.replace('\n', ' ').strip().split())
                    clean_value = ' '.join(value.replace('\n', ' ').strip().split())
                    clean_data[clean_key] = clean_value


                result = {
                    "Назва": title,
                    "Опис": description,
                    "Поживна цінність": clean_data,
                }
                results.append(result)

            except Exception as e:
                print(f"Error fetching {url}: {e}")

        await browser.close()
        

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
    

async def main():
    await get_items('https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html')
    await get_info('data.json')

if __name__ == '__main__':
    asyncio.run(main()) 