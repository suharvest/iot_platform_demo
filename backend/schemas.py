"""
Pydantic数据模型（用于API请求/响应验证）
根据mqtt_protocal.md协议设计
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 设备相关模型 ============

class DeviceBase(BaseModel):
    """设备基础模型"""
    device_name: str = Field(..., description="设备名称")
    device_type: str = Field(default="oscilloscope", description="设备类型")
    manufacturer: Optional[str] = Field(None, description="制造商")
    model: Optional[str] = Field(None, description="型号")
    location: Optional[str] = Field(None, description="位置描述")
    location_topic: Optional[str] = Field(None, description="位置MQTT主题")


class DeviceCreate(DeviceBase):
    """创建设备请求模型"""
    sn: str = Field(..., description="序列号，唯一标识")


class DeviceUpdate(BaseModel):
    """更新设备请求模型"""
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    location_topic: Optional[str] = None
    status: Optional[str] = None


class Device(DeviceBase):
    """设备响应模型"""
    id: int
    sn: str
    status: str
    last_update: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    total: int
    devices: List[Device]


# ============ 测量数据相关模型 ============

class MeasurementDataCreate(BaseModel):
    """创建测量数据请求模型"""
    device_sn: str
    channel: int = Field(..., ge=1, le=4, description="通道号 1-4")
    task: str = Field(..., description="测量任务: freq_meas/vpp_meas/vmax_meas")
    value: float
    unit: str = Field(..., description="单位: Hz/V")


class MeasurementData(BaseModel):
    """测量数据响应模型"""
    id: int
    device_sn: str
    channel: int
    task: str
    value: float
    unit: str
    timestamp: datetime

    class Config:
        from_attributes = True


class MeasurementHistoryResponse(BaseModel):
    """测量历史数据响应"""
    total: int
    data: List[MeasurementData]


# ============ MQTT消息模型（根据mqtt_protocal.md） ============

class DeviceInfoMessage(BaseModel):
    """设备信息消息 - device/info"""
    task: str = Field(default="dev_info")
    type: str = Field(..., description="设备类型，如oscilloscope")
    manufacturer: str = Field(..., description="制造商，如ZLG")
    model: str = Field(..., description="型号，如ZDS21104")
    sn: str = Field(..., description="序列号，如OSC001")


class OscilloscopeSetMessage(BaseModel):
    """示波器控制消息 - oscilloscope/set"""
    task: str = Field(..., description="任务: reset/autosetup")
    param: Dict[str, Any] = Field(default_factory=dict, description="参数")


class OscilloscopeSetResponse(BaseModel):
    """示波器控制响应 - oscilloscope/set_rsp"""
    task: str
    status: str = Field(..., description="状态: done/error")


class OscilloscopeQueryMessage(BaseModel):
    """示波器查询消息 - oscilloscope/query"""
    task: str = Field(..., description="任务: freq_meas/vpp_meas/vmax_meas")
    channel: int = Field(..., ge=1, le=4, description="通道号 1-4")


class OscilloscopeQueryResponse(BaseModel):
    """示波器查询响应 - oscilloscope/query_rsp"""
    task: str
    channel: int
    value: str = Field(..., description="测量值（字符串格式）")
    unit: str = Field(..., description="单位: Hz/V")


class LocationMessage(BaseModel):
    """位置消息 - location/{topic}"""
    location: str = Field(..., description="位置描述")


# ============ API请求模型 ============

class DeviceCommandRequest(BaseModel):
    """设备控制命令请求"""
    command: str = Field(..., description="命令: reset/autosetup")


class DeviceMeasureRequest(BaseModel):
    """设备测量请求"""
    task: str = Field(..., description="测量任务: freq_meas/vpp_meas/vmax_meas")
    channel: int = Field(..., ge=1, le=4, description="通道号 1-4")


class DeviceMeasureResponse(BaseModel):
    """设备测量响应"""
    task: str
    channel: int
    value: float
    unit: str
    timestamp: datetime


class LocationConfigRequest(BaseModel):
    """位置配置请求"""
    location_topic: str = Field(..., description="位置MQTT主题")


class MQTTConfigRequest(BaseModel):
    """MQTT配置请求"""
    broker: str = Field(..., description="MQTT Broker地址")
    port: int = Field(default=1883, description="MQTT端口")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")


class MQTTConfigResponse(BaseModel):
    """MQTT配置响应"""
    broker: str
    port: int
    username: Optional[str] = None
    connected: bool = Field(..., description="连接状态")


# ============ 3D模型相关 ============

class ModelListResponse(BaseModel):
    """3D模型列表响应"""
    models: List[str] = Field(..., description="可用的模型文件名列表（不含扩展名）")
