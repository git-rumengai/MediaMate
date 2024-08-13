"""
This module defines the NewsClient class, which is used to interact with Google News RSS feeds.
The class provides methods to fetch news articles based on various configurations such as location,
language, and topic. It also includes functionality to print and export news articles.
"""

import difflib
from datetime import datetime

import requests
from bs4 import BeautifulSoup as soup

from mediamate.tools.google_news.utils import (
    LOCATION_MAP,
    LANG_MAP,
    TOPIC_MAP,
    TOP_NEWS_URL,
    TOPIC_URL,
    QUERY_URL
)


# pylint: disable=R0902
class GoogleNewsClient:
    """
    Client for fetching and managing news articles from Google News RSS feeds.
    """
    def __init__(self):
        """
        Initializes the NewsClient with default settings.
        """
        # list of available locations, languages and topics
        self.locations = list(LOCATION_MAP)
        self.languages = list(LANG_MAP)
        self.topics = list(TOPIC_MAP)

        # default settings
        self.location = 'China'
        self.language = 'chinese simplified'
        self.topic = 'Top Stories'
        self.query = None

        # other settings
        self.max_results = 5

    # pylint: disable=R0913
    def set_params(self, location='United States', language='english', topic='Top Stories', query=None, max_results=5):
        """
        Sets the configuration of the NewsClient.

        :param location: Location to filter news by.
        :param language: Language to filter news by.
        :param topic: Topic to filter news by.
        :param query: Custom query to filter news by.
        :param max_results: Maximum number of news articles to return.
        """
        self.location = location
        self.language = language
        self.topic = topic
        self.query = query
        self.max_results = max_results

    def get_config(self):
        """
        Returns the current configuration settings.

        :return: Dictionary with current configuration.
        """
        config = {
            'location': self.location,
            'language': self.language,
            'topic': self.topic,
            'query': self.query
        }
        return config

    @property
    def params_dict(self):
        """
        Constructs and returns the parameters dictionary for HTTP request.

        :return: Dictionary with parameters for the HTTP request.
        """
        location_code = 'CN'
        language_code = 'zh-Hans'
        if self.location:
            closest_location = difflib.get_close_matches(self.location, self.locations, n=1, cutoff=0.8)
            location_code = LOCATION_MAP.get(closest_location[0], 'CN') if closest_location else 'CN'

        if self.language:
            closest_language = difflib.get_close_matches(self.language, self.languages, n=1, cutoff=0.8)
            language_code = LANG_MAP.get(closest_language[0], 'zh-Hans') if closest_language else 'zh-Hans'

        params = {
            'hl': language_code,
            'gl': location_code,
            'ceid': f'{location_code}:{language_code}'
        }
        return params

    def get_news(self):
        """
        Fetches news articles based on the current configuration.

        :return: List of news items.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
        }
        if self.query:
            query_item_url = QUERY_URL + self.query
            resp = requests.get(query_item_url, params=self.params_dict, headers=headers, timeout=30)
            xml_page = resp.content
        elif self.topic is None or self.topic == 'Top Stories':
            resp = requests.get(TOP_NEWS_URL, params=self.params_dict, headers=headers, timeout=30)
            xml_page = resp.content

        else:
            closest_topic = difflib.get_close_matches(self.topic, self.topics, n=1, cutoff=0.8)
            topic_code = TOPIC_MAP.get(closest_topic[0], 'Technology') if closest_topic else 'Technology'
            resp = requests.get(TOPIC_URL.format(topic_code), params=self.params_dict, headers=headers, timeout=30)
            xml_page = resp.content

        soup_page = soup(xml_page, "xml")
        news_list = soup_page.findAll("item")
        return news_list

    def export_news(self):
        """
        Exports the news articles as a list of dictionaries.

        :return: List of dictionaries containing news articles.
        """
        news_items = self.get_news()
        items = []
        for news in news_items[:self.max_results]:
            title = news.title.text.split(' - ', 1)[0]
            source = news.source.text
            link = news.link.text
            pubdate = news.pubDate.text

            item = {
                'title': title,
                'source': source,
                'link': link,
                'publish_date': pubdate,
            }

            items.append(item)

        sorted_items = sorted(items, key=lambda x: datetime.strptime(x['publish_date'], "%a, %d %b %Y %H:%M:%S %Z"), reverse=True)
        return sorted_items
