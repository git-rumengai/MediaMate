"""
This module provides a class `RedisHandler` for handling Redis operations.
"""
import asyncio
import pickle
from redis import Redis, ConnectionPool, exceptions
from redis import asyncio as aioredis
from mediamate.utils.log_manager import log_manager
from mediamate.config import config

logger = log_manager.get_logger(__file__)


class RedisClient:
    """
    A class for handling Redis operations.

    It manages both synchronous and asynchronous connections to Redis.
    """
    def __init__(self):
        self.redis_url = ''
        self.redis_pool = None
        self.redis_conn = None
        self.aredis_conn = None
        self.async_init_lock = None

    def init(self, db: int):
        """
        Initialize the RedisHandler class.

        Sets up the Redis URL and connection pools for both synchronous and asynchronous operations.

        Args:
            db (int): The database index to be used for Redis connections.
        """
        password = config.get('REDIS_PASSWORD')
        host = config.get('REDIS_HOST')
        port = config.get('REDIS_PORT')
        if password:  # 如果有密码
            self.redis_url = f'redis://:{password}@{host}:{port}/{db}'
        else:  # 如果没有密码
            self.redis_url = f'redis://@{host}:{port}/{db}'

        # 同步连接 - 全局连接池
        self.redis_pool = ConnectionPool.from_url(self.redis_url)
        self.redis_conn = Redis(connection_pool=self.redis_pool, max_connections=30)
        # 异步连接 - 全局连接池
        self.aredis_conn = None
        self.async_init_lock = asyncio.Lock()
        return self

    async def init_async_pool(self):
        """
        Initialize the asynchronous connection pool.

        Ensures that the asynchronous connection is initialized only once.
        """
        async with self.async_init_lock:
            if self.aredis_conn is None:
                self.aredis_conn = aioredis.from_url(self.redis_url, max_connections=30)

    def set_data(self, key, data, ex: int) -> bool:
        """
        Set data synchronously.

        Args:
            key (str): The key for the data.
            data: The data to be stored.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        serialized_data = pickle.dumps(data)
        try:
            self.redis_conn.set(key, serialized_data, ex=ex)
            return True
        except exceptions.RedisError as e:
            logger.error(f"同步设置数据时发生错误: {e}")
            return False

    def get_data(self, key):
        """
        Get data synchronously.

        Args:
            key (str): The key to retrieve data for.

        Returns:
            The deserialized data if successful, None otherwise.
        """
        try:
            serialized_data = self.redis_conn.get(key)
            if serialized_data:
                return pickle.loads(serialized_data)
            return None
        except exceptions.RedisError as e:
            logger.error(f"同步获取数据时发生错误: {e}")
            return None

    def keys(self, key_pattern) -> list:
        """
        Get data synchronously based on a key pattern (regular expression).

        Args:
            key_pattern (str): The regular expression pattern for the keys.

        Returns:
            A dictionary of deserialized data for matching keys, or None if an error occurs.
        """
        result = []
        try:
            matching_keys = self.redis_conn.keys(pattern=key_pattern)
            for key in matching_keys:
                serialized_data = self.redis_conn.get(key)
                if serialized_data:
                    result.append(pickle.loads(serialized_data))
            return result
        except exceptions.RedisError as e:
            logger.error(f"同步获取数据时发生错误: {e}")
            return result

    async def aset_data(self, key, data, ex: int) -> bool:
        """
        Set data asynchronously.

        Args:
            key (str): The key for the data.
            data: The data to be stored.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        await self.init_async_pool()
        serialized_data = pickle.dumps(data)
        try:
            await self.aredis_conn.set(key, serialized_data, ex=ex)
            return True
        except exceptions.RedisError as e:
            logger.error(f"异步设置数据时发生错误: {e}")
            return False

    async def aget_data(self, key):
        """
        Get data asynchronously.

        Args:
            key (str): The key to retrieve data for.

        Returns:
            The deserialized data if successful, None otherwise.
        """
        await self.init_async_pool()
        try:
            serialized_data = await self.aredis_conn.get(key)
            if serialized_data:
                return pickle.loads(serialized_data)
            return None
        except exceptions.RedisError as e:
            logger.error(f"异步获取数据时发生错误: {e}")
            return None

    async def akeys(self, key_pattern) -> list:
        """
        Get data asynchronously based on a key pattern (regular expression).

        Args:
            key_pattern (str): The regular expression pattern for the keys.

        Returns:
            A dictionary of deserialized data for matching keys, or None if an error occurs.
        """
        await self.init_async_pool()
        result = []
        try:
            matching_keys = await self.aredis_conn.keys(pattern=key_pattern)
            for key in matching_keys:
                serialized_data = await self.aredis_conn.get(key)
                if serialized_data:
                    result.append(pickle.loads(serialized_data))
            return result
        except aioredis.RedisError as e:
            logger.error(f"异步获取数据时发生错误: {e}")
            return result
