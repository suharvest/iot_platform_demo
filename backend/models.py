"""
数据库模型定义
根据mqtt_protocal.md协议设计的全新数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from backend.database import Base


class Device(Base):
    """设备表 - 存储示波器等IoT设备信息"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_name = Column(String(200), nullable=False, comment="设备名称")
    device_type = Column(String(50), nullable=False, default="oscilloscope", comment="设备类型")
    manufacturer = Column(String(100), comment="制造商，如ZLG")
    model = Column(String(100), comment="型号，如ZDS21104")
    sn = Column(String(100), unique=True, nullable=False, index=True, comment="序列号，唯一标识")
    location = Column(String(200), comment="位置描述，如'桌子1'")
    location_topic = Column(String(200), comment="位置MQTT主题，用于获取实时位置")
    status = Column(String(20), default="offline", comment="状态: online/offline")
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="最后更新时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<Device(sn={self.sn}, name={self.device_name}, model={self.model}, status={self.status})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "sn": self.sn,
            "location": self.location,
            "location_topic": self.location_topic,
            "status": self.status,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MeasurementData(Base):
    """测量数据表 - 存储示波器测量数据（频率、电压等）"""
    __tablename__ = "measurement_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_sn = Column(String(100), ForeignKey("devices.sn", ondelete="CASCADE"), nullable=False, comment="设备序列号")
    channel = Column(Integer, nullable=False, comment="通道号 1-4")
    task = Column(String(50), nullable=False, comment="测量任务: freq_meas/vpp_meas/vmax_meas")
    value = Column(Float, nullable=False, comment="测量值")
    unit = Column(String(20), nullable=False, comment="单位: Hz/V")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="测量时间")

    # 创建复合索引，优化查询性能
    __table_args__ = (
        Index('idx_device_channel_timestamp', 'device_sn', 'channel', 'timestamp'),
        Index('idx_device_task_timestamp', 'device_sn', 'task', 'timestamp'),
    )

    def __repr__(self):
        return f"<MeasurementData(device={self.device_sn}, ch={self.channel}, task={self.task}, value={self.value}{self.unit})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "device_sn": self.device_sn,
            "channel": self.channel,
            "task": self.task,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
