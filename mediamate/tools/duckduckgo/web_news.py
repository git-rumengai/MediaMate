import asyncio

import re
import math
from datetime import datetime, timedelta
from typing import List, Tuple

from mediamate.tools.duckduckgo import AsyncDDGS


class WebNews:
    async def filter_news(self, ddgs, keyword: str, max_results: int, blacklist: Tuple[str, ...], days: int, region = 'cn-zh',) -> list[dict[str, str]]:
        """  """
        news = await ddgs.anews(keyword, region=region, safesearch='off', timelimit=None, max_results=max_results)
        if news:
            # 过滤掉不符合条件的新闻
            filtered_news = [
                item for item in news
                if datetime.fromisoformat(item['date']).replace(tzinfo=None) >= datetime.now() - timedelta(days=days) and not any(domain in item.get('url', '') for domain in blacklist)
            ]
            return filtered_news
        return []

    async def get_ddgs_news(self,
                            keywords: List[str],
                            blacklist: Tuple[str, ...] = (),
                            limit: int = 5,
                            days: int = 7,
                            truncat: bool = False,
                            sentence: int = -1,
                            force_image: bool = False,
                            region='cn-zh',
                            ) -> list[dict[str, str]]:
        """
        获取新闻
            - keywords: 搜索关键词列表
            - blacklist: 黑名单网站列表
            - limit: 返回新闻的数量限制
            - days: 新闻文章的时间范围（天数）
            - truncat: 是否截断新闻内容到完整句子
            - sentence: 限制新闻内容到指定句子数
            - force_image: 只要有图片的新闻
            - force_body: 只要有内容的新闻
            - region: 搜索的地区代码
        """
        max_results = math.ceil(limit / len(keywords)) * 2
        async with AsyncDDGS() as ddgs:
            tasks = (self.filter_news(ddgs, keyword, max_results, blacklist, days, region) for keyword in keywords)
            news = await asyncio.gather(*tasks)
            filtered_news = [item for sublist in news for item in sublist]
            if force_image:
                filtered_news = [item for item in filtered_news if item['image'].strip() != '']
            filtered_news: List[dict] = list({item['url']: item for item in filtered_news}.values())
            cn_end_punctuation = '。！？'
            en_end_punctuation = '.!?'
            punctuation = cn_end_punctuation if region == 'cn-zh' else en_end_punctuation
            for index, inner in enumerate(filtered_news):
                body = inner['body']
                body_sentences = re.split(f'(?<=[{punctuation}])', body)
                if truncat:
                    if not body.endswith(tuple(punctuation)):
                        body_sentences = body_sentences[:-1]
                if sentence > -1:
                    if len(body_sentences) > sentence:
                        body_sentences = body_sentences[:sentence]
                body = ''.join(body_sentences)
                filtered_news[index]['body'] = body
            recent_news = sorted(
                filtered_news,
                key=lambda x: datetime.fromisoformat(x['date']).replace(tzinfo=None),
                reverse=True
            )
        return recent_news[:limit]
