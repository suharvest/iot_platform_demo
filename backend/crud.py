"""
数据库CRUD操作
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from backend import models, schemas


# ============ 设备操作 ============

def get_device_by_sn(db: Session, sn: str) -> Optional[models.Device]:
    """根据序列号获取设备"""
    return db.query(models.Device).filter(models.Device.sn == sn).first()


def get_devices(db: Session, skip: int = 0, limit: int = 100) -> List[models.Device]:
    """获取设备列表"""
    return db.query(models.Device).offset(skip).limit(limit).all()


def get_devices_count(db: Session) -> int:
    """获取设备总数"""
    return db.query(models.Device).count()


def create_device(db: Session, device: schemas.DeviceCreate) -> models.Device:
    """创建设备"""
    db_device = models.Device(
        device_name=device.device_name,
        device_type=device.device_type,
        manufacturer=device.manufacturer,
        model=device.model,
        sn=device.sn,
        location=device.location,
        location_topic=device.location_topic,
        status="offline",
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def create_or_update_device_from_mqtt(
    db: Session,
    sn: str,
    device_type: str,
    manufacturer: str,
    model: str
) -> models.Device:
    """从MQTT消息创建或更新设备"""
    db_device = get_device_by_sn(db, sn)

    if db_device:
        # 更新现有设备
        db_device.device_type = device_type
        db_device.manufacturer = manufacturer
        db_device.model = model
        db_device.status = "online"
        db_device.last_update = datetime.utcnow()
    else:
        # 创建新设备
        db_device = models.Device(
            device_name=f"{device_type.capitalize()} {sn}",
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            sn=sn,
            status="online",
        )
        db.add(db_device)

    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, sn: str, device_update: schemas.DeviceUpdate) -> Optional[models.Device]:
    """更新设备信息"""
    db_device = get_device_by_sn(db, sn)
    if db_device:
        update_data = device_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_device, key, value)
        db.commit()
        db.refresh(db_device)
    return db_device


def update_device_status(db: Session, sn: str, status: str) -> Optional[models.Device]:
    """更新设备状态"""
    db_device = get_device_by_sn(db, sn)
    if db_device:
        db_device.status = status
        db.commit()
        db.refresh(db_device)
    return db_device


def update_device_location(db: Session, sn: str, location: str, location_topic: str) -> Optional[models.Device]:
    """更新设备位置配置"""
    db_device = get_device_by_sn(db, sn)
    if db_device:
        db_device.location = location
        db_device.location_topic = location_topic
        db.commit()
        db.refresh(db_device)
    return db_device


def delete_device(db: Session, sn: str) -> bool:
    """删除设备"""
    db_device = get_device_by_sn(db, sn)
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False


# ============ 测量数据操作 ============

def create_measurement(
    db: Session,
    device_sn: str,
    channel: int,
    task: str,
    value: float,
    unit: str
) -> models.MeasurementData:
    """创建测量数据记录（简化版）"""
    db_measurement = models.MeasurementData(
        device_sn=device_sn,
        channel=channel,
        task=task,
        value=value,
        unit=unit,
    )
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement


def create_measurement_data(db: Session, measurement: schemas.MeasurementDataCreate) -> models.MeasurementData:
    """创建测量数据记录"""
    db_measurement = models.MeasurementData(
        device_sn=measurement.device_sn,
        channel=measurement.channel,
        task=measurement.task,
        value=measurement.value,
        unit=measurement.unit,
    )
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement


def get_latest_measurement(
    db: Session,
    device_sn: str,
    channel: int,
    task: str
) -> Optional[models.MeasurementData]:
    """获取设备最新的测量数据"""
    return (
        db.query(models.MeasurementData)
        .filter(
            and_(
                models.MeasurementData.device_sn == device_sn,
                models.MeasurementData.channel == channel,
                models.MeasurementData.task == task
            )
        )
        .order_by(desc(models.MeasurementData.timestamp))
        .first()
    )


def get_measurement_history(
    db: Session,
    device_sn: str,
    channel: Optional[int] = None,
    task: Optional[str] = None,
    hours: float = 24,
    skip: int = 0,
    limit: int = 1000
) -> List[models.MeasurementData]:
    """获取设备历史测量数据（支持小数小时）"""
    query = db.query(models.MeasurementData).filter(
        models.MeasurementData.device_sn == device_sn
    )

    # 过滤通道
    if channel is not None:
        query = query.filter(models.MeasurementData.channel == channel)

    # 过滤任务类型
    if task is not None:
        query = query.filter(models.MeasurementData.task == task)

    # 过滤时间范围
    if hours > 0:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(models.MeasurementData.timestamp >= time_threshold)

    return (
        query
        .order_by(desc(models.MeasurementData.timestamp))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_measurement_count(
    db: Session,
    device_sn: str,
    channel: Optional[int] = None,
    task: Optional[str] = None
) -> int:
    """获取测量数据总数"""
    query = db.query(models.MeasurementData).filter(
        models.MeasurementData.device_sn == device_sn
    )

    if channel is not None:
        query = query.filter(models.MeasurementData.channel == channel)

    if task is not None:
        query = query.filter(models.MeasurementData.task == task)

    return query.count()
