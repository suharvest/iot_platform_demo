"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base


class Device(Base):
    """设备信息表"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="设备名称")
    device_id = Column(String(50), unique=True, nullable=False, index=True, comment="设备ID")
    status = Column(String(20), default="offline", comment="设备状态: online/offline/error")
    center_frequency = Column(Float, comment="中心频率(GHz)")
    last_update = Column(DateTime, comment="最后更新时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    spectrum_data = relationship("SpectrumData", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device(id={self.id}, device_id={self.device_id}, name={self.name}, status={self.status})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "device_id": self.device_id,
            "status": self.status,
            "center_frequency": self.center_frequency,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SpectrumData(Base):
    """频谱数据表（时序数据）"""

    __tablename__ = "spectrum_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), ForeignKey("devices.device_id"), nullable=False, comment="设备ID")
    peak_frequency = Column(Float, nullable=False, comment="峰值频率(GHz)")
    frequency_change = Column(Float, comment="频率变化量")
    data_json = Column(Text, comment="完整频谱数据JSON")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, comment="采集时间")

    # 关系
    device = relationship("Device", back_populates="spectrum_data")

    # 复合索引
    __table_args__ = (
        Index("idx_device_time", "device_id", "timestamp"),
    )

    def __repr__(self):
        return f"<SpectrumData(id={self.id}, device_id={self.device_id}, peak_frequency={self.peak_frequency})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "peak_frequency": self.peak_frequency,
            "frequency_change": self.frequency_change,
            "data_json": self.data_json,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
