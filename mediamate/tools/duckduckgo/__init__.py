"""Duckduckgo_search.

Search for words, documents, images, videos, news, maps and text translation
using the DuckDuckGo.com search engine.
"""

import asyncio
from duckduckgo_search import DDGS, AsyncDDGS, __version__

__all__ = ["DDGS", "AsyncDDGS", "__version__"]


# 必须要添加这句话防止duckduckgo_search与playwright冲突
# metagpt提供ddgs, 默认是同步方法, 该原生接口可以使用异步方法
asyncio.set_event_loop_policy(None)
