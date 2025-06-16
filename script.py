from collections import deque
import json, asyncio, requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# At first i will collect urls of all items on the menu
# this will allow me to build links to go through pages and scrape required information quicker

item_links = deque()

def get_items(url):
    r=requests.get(url, headers={'User-Agent':"Mozilla/5.0 (X11; CrOS x86_64 8172.45.0)"})
    if r.status_code != 200:
        raise Exception(f"Failed to fetch page: {url} (status code {r.status_code})")
    soup = BeautifulSoup(r.content, 'html5lib')
    ids = soup.find('main', attrs={'class':'cmp-container cmp-container--overflow-hidden'})
    for ids in soup.find_all('a', href=True):
        href = ids['href']
        if '/product/' in href:
            item_links.append(href)

    print(f"Saved {len(item_links)} item IDs to deque")


# using previously collected urls i will build links to each product and collect information
def get_basic_info():
    basic_info = {}
    while item_links:
        id = item_links.popleft()
        url = f'https://www.mcdonalds.com{id}#accordion-29309a7a60-item-9ea8a10642'
        r = requests.get(url, headers={'User-Agent': "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0)"})
        if r.status_code != 200:
            print(f"Failed to fetch {url} (status {r.status_code})")
            continue
        soup = BeautifulSoup(r.content, 'html5lib')
        title = soup.find("span", class_="cmp-product-details-main__heading-title")
        desc = soup.find("div", class_="cmp-text")
        basic_info[id] = {
            "title": title.text.strip() if title else "No title",
            "description": desc.text.strip().replace('\xa0', ' ') if desc else "Немає опису"
        }
    return basic_info

async def get_nutritional_info(basic_info, output_file):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for id, info in basic_info.items():
            url = f'https://www.mcdonalds.com{id}#accordion-29309a7a60-item-9ea8a10642'
            try:
                await page.goto(url)
                await page.wait_for_selector("li.cmp-nutrition-summary__heading-primary-item", timeout=5000)

                nutrition_items = await page.query_selector_all("li.cmp-nutrition-summary__heading-primary-item")
                nutrition_data = {}

                for item in nutrition_items:
                    metric_el = await item.query_selector("span.metric > span[aria-hidden='true']")
                    value_el = await item.query_selector("span.value > span[aria-hidden='true']")
                    metric = (await metric_el.text_content()).strip() if metric_el else None
                    value = (await value_el.text_content()).strip() if value_el else None
                    if metric and value:
                        nutrition_data[metric] = value

                items = await page.query_selector_all('div.cmp-nutrition-summary--nutrition-table li.label-item')
                for item in items:
                    metric = await item.query_selector('span.metric')
                    value = await item.query_selector('span.value span[aria-hidden="true"]')
                    m = (await metric.inner_text()).strip().rstrip(':') if metric else None
                    v = (await value.inner_text()).strip() if value else None
                    if m and v:
                        nutrition_data[m] = v

                clean_data = { ' '.join(k.split()): ' '.join(v.split()) for k,v in nutrition_data.items() }

                result = {
                    "Назва": info["title"],
                    "Опис": info["description"],
                    "Поживна цінність": clean_data,
                }
                results.append(result)

            except Exception as e:
                print(f"Error fetching {url}: {e}")

        await browser.close()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

async def main():
    get_items("https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html")  
    basic_info = get_basic_info()  
    await get_nutritional_info(basic_info, "data.json")  

if __name__ == '__main__':
    asyncio.run(main())

