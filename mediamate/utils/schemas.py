"""
This module defines data models (schemas) used for data validation and serialization.

"""

from pydantic import BaseModel, Field, field_validator, constr
from typing import Tuple
from mediamate.utils.const import DEFAULT_LOCATION
from mediamate.platforms.enums import PlatformType


class MediaLoginInfo(BaseModel):
    platform: PlatformType = None
    account: constr(min_length=1) = None
    headless: bool = True
    proxy: str = ''
    location: Tuple[float, float] = Field(DEFAULT_LOCATION, description="A tuple representing longitude and latitude")
    # 数据处理参数
    creator: dict = {}
    base: dict = {}

    @field_validator('location')
    def check_location(cls, v):
        if not (-180 <= v[0] <= 180) or not (-90 <= v[1] <= 90):
            raise ValueError('Invalid latitude or longitude')
        return v
