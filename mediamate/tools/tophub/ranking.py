import asyncio
from typing import Tuple, List, Dict
from playwright.async_api import Page, async_playwright

from mediamate.utils.enums import TophubType
from mediamate.utils.common import get_useragent


class Ranking:
    urls = {
        TophubType.TECH: 'https://tophub.today/c/tech',
        TophubType.ENT: 'https://tophub.today/c/ent',
        TophubType.COM: 'https://tophub.today/c/community',
        TophubType.FIN: 'https://tophub.today/c/finance',
        TophubType.DEV: 'https://tophub.today/c/developer',
        TophubType.DES: 'https://tophub.today/c/design',
        TophubType.PNM: 'https://tophub.today/c/epaper'
    }

    async def handle_page(self, page: Page, url: str, type_key: str) -> dict:
        """  """
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        containers = page.locator('xpath=//div[@class="bc-cc"]/div')
        await containers.first.wait_for(state='visible')
        containers_all = await containers.all()
        items = []
        for container in containers_all:
            brand = await container.locator('xpath=//div[@class="cc-cd-lb"]').inner_text()
            dt = await container.locator('xpath=//div[@class="cc-cd-if"]/div[1]').inner_text()
            a = container.locator('xpath=//div[@class="cc-cd-cb-l nano-content"]/a')
            a_all = await a.all()
            item = []
            for a_item in a_all:
                title = a_item.locator('xpath=/div/span[2]')
                title_text = await title.inner_text()
                href = await a_item.get_attribute('href')
                href = f'https://tophub.today{href}'
                item.append({'标题': title_text.strip(), '链接': href})
            item = {'媒体': brand.strip(), '时间': dt.strip(), '内容': item}
            # 过滤旧数据
            if '前' in dt:
                items.append(item)
        return {type_key: items}

    async def get_data(self, tophub: Tuple[TophubType, ...] = ()) -> Tuple[Dict[str, List]]:
        """  """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, channel='chrome', args=['--disable-blink-features=AutomationControlled',])
            context = await browser.new_context(user_agent=get_useragent())
            # 启动任务并收集数据
            tasks = []
            for type_key, url in self.urls.items():
                if tophub and type_key not in tophub:
                    continue
                page = await context.new_page()
                task = asyncio.create_task(self.handle_page(page, url, type_key.value))
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            # 关闭浏览器
            await browser.close()
            return results

