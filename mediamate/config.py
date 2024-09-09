"""
This module contains the Config class which is responsible for loading environment variables,
managing configuration settings, and initializing logging.
"""
import asyncio
import os
import logging
import re
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import yaml
from dotenv import load_dotenv


# 加载 .env 文件
load_dotenv()


class Config:
    """
    Configuration class to load environment variables and manage configuration settings.

    This class is responsible for loading environment variables with a specific prefix ('MM__')
    and providing methods to retrieve all configuration variables as a dictionary.
    """
    PROJECT_DIR = os.path.dirname(__file__)
    DATA = os.getenv('MM_DATA', 'data')
    # 创建数据和日志文件夹
    DATA_DIR = os.path.join(os.path.dirname(PROJECT_DIR), DATA)
    os.makedirs(DATA_DIR, exist_ok=True)
    LOG_DIR = os.path.join(DATA_DIR, 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, 'MediaMate.log')
    handler = RotatingFileHandler(
        filename=log_file,
        mode='a',
        maxBytes=3 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )

    # 创建格式化器并设置给处理程序
    formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    # 配置根记录器
    logger = logging.getLogger('root')
    logger.setLevel(logging.INFO)  # 设置根记录器的日志级别
    logger.addHandler(handler)
    ROOT_LOGGER = logger

    # 附加配置
    MEDIA = {}
    def __init__(self):
        """
        Initializes the Config object by loading environment variables.

        It iterates through the environment variables, filters those starting with 'MM__',
        and sets them as attributes of the object.

        :raises ValueError: If there's an error loading or setting an environment variable.
        """
        try:
            self.init()
            for key, value in os.environ.items():
                if key.startswith('MM__'):
                    setattr(Config, key[4:], value)
            self.init_metagpt()
        except (ValueError, KeyError)  as e:
            Config.ROOT_LOGGER.error("Error loading or setting environment variables: %s", e)
        self.init_metagpt()

    @staticmethod
    def init():
        """Initialize the configuration by loading data from a YAML file."""
        data = {}
        config_file = f'{os.path.dirname(Config.PROJECT_DIR)}/.media.yaml'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
        setattr(Config, 'MEDIA', data)

    @classmethod
    def get_all_configs(cls):
        """
        Returns all configuration variables as a dictionary.

        Filters out attributes that start with '__' or are callable.

        :return: A dictionary containing all configuration variables.
        """
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith('__') and not callable(getattr(cls, key))
        }

    @classmethod
    def get(cls, name, default = None):
        """
        Fetches the value of a configuration attribute based on its name.

        Args:
            name (str): The name of the configuration attribute to obtain.
            default: The default value to return if the attribute is not found.

        Returns:
            The value of the configuration attribute if it exists; otherwise, the default value.
        """
        return getattr(cls, name) if hasattr(cls, name) else default

    def init_metagpt(self):
        """Initialize the MetaGPT configuration."""
        api_kye = self.get('302__APIKEY')
        config2 = {'llm': {}}
        if api_kye:
            config2['llm']['api_type'] = 'openai'
            config2['llm']['base_url'] = 'https://api.302.ai/v1'
            config2['llm']['api_key'] = api_kye
            config2['llm']['model'] = self.get('302__LLM') or 'gpt-4o-mini'

        # 设置mategpt配置文件路径
        agent_dir = f'{self.DATA_DIR}/agent/metagpt'
        os.environ['METAGPT_PROJECT_ROOT'] = agent_dir
        os.makedirs(f'{agent_dir}/config', exist_ok=True)
        with open(f'{agent_dir}/config/config2.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config2, file, default_flow_style=False, allow_unicode=True)


class ConfigManager:
    """Configuration manager class to handle configuration data and expiration times."""
    def __init__(self, config_path: str):
        self.config_path: str = config_path
        self.config_data = {}
        self.lock = asyncio.Lock()
        self.expiration_tasks = {}
        self.expiration_times = {}
        self.load_config()
        self._cleanup_expired_keys()

    def load_config(self):
        """Load configuration from the file or initialize an empty config."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file) or {}
                    self.config_data = data.get('config_data', {})
                    self.expiration_times = data.get('expiration_times', {})
            except yaml.YAMLError:
                self.config_data = {}
                self.expiration_times = {}

    async def remove(self, key):
        """Remove a key from the configuration."""
        async with self.lock:
            self.config_data.pop(key, None)
            self.expiration_times.pop(key, None)
            await self.save_config()

    async def set(self, key, value, ex: int = None):
        """Set a value in the config with an optional expiration time."""
        async with self.lock:
            self.config_data[key] = value
            if ex:
                self.expiration_times[key] = datetime.now() + timedelta(seconds=ex) if ex else None
        # Save configuration with expiration update
        await self.save_config()

        # Schedule expiration if needed
        if ex:
            if key in self.expiration_tasks:
                self.expiration_tasks[key].cancel()
            self.expiration_tasks[key] = asyncio.create_task(self._expire_key(key, ex))

    async def save_config(self):
        """Save the current config to the file with locking."""
        async with self.lock:
            result = {
                'config_data': self.config_data
            }
            if self.expiration_times:
                result['expiration_times'] = self.expiration_times
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.safe_dump(result, file, indent=4, allow_unicode=True)

    async def _expire_key(self, key, ex):
        """Wait for the expiration time and then remove the key."""
        try:
            await asyncio.sleep(ex)
            async with self.lock:
                self.config_data.pop(key, None)
                self.expiration_times.pop(key, None)
                await self.save_config()
                self.expiration_tasks.pop(key, None)
        except asyncio.CancelledError:
            # Task was cancelled, key should not be removed
            pass

    def _cleanup_expired_keys(self):
        """Cleanup expired keys."""
        now = datetime.now()
        expired_keys = [key for key, exp_time in self.expiration_times.items() if exp_time and exp_time <= now]
        for key in expired_keys:
            self.config_data.pop(key, None)
            self.expiration_times.pop(key, None)

    def get(self, key, default=None):
        """Get a value from the config, return default if key is not found."""
        # Remove expired keys before accessing
        self._cleanup_expired_keys()
        return self.config_data.get(key, default)

    def keys(self, pattern: str):
        """Return a list of keys matching the given regular expression pattern."""
        regex = re.compile(pattern)
        return [self.config_data[key] for key in self.config_data.keys() if regex.match(key)]


# 创建一个 Config 实例
config = Config()

# 通过 `__all__` 控制公共接口
__all__ = ['config', 'ConfigManager']
