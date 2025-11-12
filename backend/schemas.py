"""
Pydantic数据模型（用于API请求/响应验证）
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 设备相关模型 ============

class DeviceBase(BaseModel):
    """设备基础模型"""

    name: str = Field(..., description="设备名称")
    device_id: str = Field(..., description="设备ID")
    center_frequency: Optional[float] = Field(None, description="中心频率(GHz)")


class DeviceCreate(DeviceBase):
    """创建设备请求模型"""

    pass


class DeviceUpdate(BaseModel):
    """更新设备请求模型"""

    name: Optional[str] = None
    status: Optional[str] = None
    center_frequency: Optional[float] = None


class Device(DeviceBase):
    """设备响应模型"""

    id: int
    status: str
    last_update: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 频谱数据相关模型 ============

class SpectrumDataCreate(BaseModel):
    """创建频谱数据请求模型"""

    device_id: str
    peak_frequency: float
    frequency_change: Optional[float] = None
    data_json: Optional[str] = None


class SpectrumData(BaseModel):
    """频谱数据响应模型"""

    id: int
    device_id: str
    peak_frequency: float
    frequency_change: Optional[float] = None
    data_json: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ============ MQTT消息模型 ============

class MQTTSpectrumMessage(BaseModel):
    """MQTT频谱数据消息模型"""

    device_id: str
    device_name: str
    peak_frequency: float
    center_frequency: float
    timestamp: str
    data_points: List[List[float]]  # [[time, frequency], ...]


class MQTTStatusMessage(BaseModel):
    """MQTT设备状态消息模型"""

    device_id: str
    status: str  # online, offline, error
    center_frequency: float
    timestamp: str
    metadata: Optional[dict] = None


class MQTTHeartbeatMessage(BaseModel):
    """MQTT心跳消息模型"""

    device_id: str
    timestamp: str


# ============ API响应模型 ============

class SpectrumHistoryResponse(BaseModel):
    """频谱历史数据响应"""

    total: int
    page: int
    page_size: int
    data: List[SpectrumData]


class DeviceListResponse(BaseModel):
    """设备列表响应"""

    total: int
    devices: List[Device]
