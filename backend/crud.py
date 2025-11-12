"""
数据库CRUD操作
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend import models, schemas


# ============ 设备操作 ============

def get_device(db: Session, device_id: str) -> Optional[models.Device]:
    """根据device_id获取设备"""
    return db.query(models.Device).filter(models.Device.device_id == device_id).first()


def get_devices(db: Session, skip: int = 0, limit: int = 100) -> List[models.Device]:
    """获取设备列表"""
    return db.query(models.Device).offset(skip).limit(limit).all()


def create_device(db: Session, device: schemas.DeviceCreate) -> models.Device:
    """创建设备"""
    db_device = models.Device(
        name=device.name,
        device_id=device.device_id,
        center_frequency=device.center_frequency,
        status="offline",
        created_at=datetime.utcnow(),
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, device_id: str, device_update: schemas.DeviceUpdate) -> Optional[models.Device]:
    """更新设备信息"""
    db_device = get_device(db, device_id)
    if db_device:
        update_data = device_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_device, key, value)
        db_device.last_update = datetime.utcnow()
        db.commit()
        db.refresh(db_device)
    return db_device


def update_device_status(db: Session, device_id: str, status: str, center_frequency: float = None) -> Optional[models.Device]:
    """更新设备状态"""
    db_device = get_device(db, device_id)
    if db_device:
        db_device.status = status
        if center_frequency is not None:
            db_device.center_frequency = center_frequency
        db_device.last_update = datetime.utcnow()
        db.commit()
        db.refresh(db_device)
    return db_device


def delete_device(db: Session, device_id: str) -> bool:
    """删除设备"""
    db_device = get_device(db, device_id)
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False


# ============ 频谱数据操作 ============

def create_spectrum_data(db: Session, spectrum: schemas.SpectrumDataCreate) -> models.SpectrumData:
    """创建频谱数据记录"""
    db_spectrum = models.SpectrumData(
        device_id=spectrum.device_id,
        peak_frequency=spectrum.peak_frequency,
        frequency_change=spectrum.frequency_change,
        data_json=spectrum.data_json,
        timestamp=datetime.utcnow(),
    )
    db.add(db_spectrum)
    db.commit()
    db.refresh(db_spectrum)
    return db_spectrum


def get_latest_spectrum_data(db: Session, device_id: str) -> Optional[models.SpectrumData]:
    """获取设备最新的频谱数据"""
    return (
        db.query(models.SpectrumData)
        .filter(models.SpectrumData.device_id == device_id)
        .order_by(desc(models.SpectrumData.timestamp))
        .first()
    )


def get_spectrum_history(
    db: Session, device_id: str, skip: int = 0, limit: int = 100
) -> List[models.SpectrumData]:
    """获取设备历史频谱数据"""
    return (
        db.query(models.SpectrumData)
        .filter(models.SpectrumData.device_id == device_id)
        .order_by(desc(models.SpectrumData.timestamp))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_spectrum_count(db: Session, device_id: str) -> int:
    """获取设备频谱数据总数"""
    return db.query(models.SpectrumData).filter(models.SpectrumData.device_id == device_id).count()
