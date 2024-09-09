import asyncio

from typing import List, Dict
from playwright.async_api import Page, async_playwright
from mediamate.utils.common import get_useragent
from mediamate.utils.const import DEFAULT_URL_TIMEOUT
from mediamate.tools.api_market.chat import Chat
from mediamate.utils.log_manager import log_manager


logger = log_manager.get_logger(__file__)


SUMMARY_PROMPT = """
请根据“参考信息”中的内容总结关于“{query}”的信息:

### 约束
1. 不超过100字
2. 不要做任何解释说明
3. 没有相关信息请返回“ERROR”

### 参考信息
{html_text}
"""


class WebSummary:
    def __init__(self):
        self.chat = Chat()

    async def get_page_text(self, page: Page, query: str, url: str):
        """  """
        try:
            await page.goto(url, timeout=DEFAULT_URL_TIMEOUT)
            await page.wait_for_load_state('networkidle')
            # 获取 body 元素的文本内容
            page_text_content = await page.text_content("body")
            summary = self.chat.get_response(SUMMARY_PROMPT.format(query=query, html_text=page_text_content))
            return {query: summary}
        except Exception as e:
            logger.error(e)
            return {query: 'ERROR'}

    async def summary(self, query_urls: List[Dict[str, str]]):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, channel='chrome', args=['--disable-blink-features=AutomationControlled', ])
            context = await browser.new_context(user_agent=get_useragent())
            # 启动任务并收集数据
            tasks = []
            for query_url in query_urls:
                for query, url in query_url.items():
                    page = await context.new_page()
                    task = asyncio.create_task(self.get_page_text(page, query, url))
                    tasks.append(task)
            results = await asyncio.gather(*tasks)
            # 关闭浏览器
            await browser.close()
        return results
