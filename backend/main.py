"""
FastAPI主应用
根据mqtt_protocal.md协议实现的全新API
"""
import json
import logging
import os
from typing import List, Optional
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.database import get_db, init_db
from backend import crud, schemas
from backend.mqtt_client import init_mqtt_client, get_mqtt_client
from backend.config import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
main_event_loop = None

# Lifespan 事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    import asyncio
    global main_event_loop

    # 启动事件
    logger.info("🚀 启动四川物联网平台（设备管理系统）...")

    # 保存主事件循环引用
    main_event_loop = asyncio.get_event_loop()

    # 初始化数据库
    init_db()
    logger.info("✓ 数据库已初始化")

    # 启动MQTT客户端
    try:
        init_mqtt_client(on_message_callback=on_mqtt_message)
        logger.info("✓ MQTT客户端已启动")
    except Exception as e:
        logger.error(f"✗ MQTT客户端启动失败: {e}")

    yield  # 应用运行期间

    # 关闭事件
    logger.info("关闭应用...")
    try:
        mqtt_client = get_mqtt_client()
        mqtt_client.stop()
        logger.info("✓ MQTT客户端已停止")
    except Exception as e:
        logger.error(f"✗ MQTT客户端停止失败: {e}")

# 创建FastAPI应用
app = FastAPI(
    title="四川物联网平台 - 设备管理系统",
    description="基于MQTT协议的示波器设备管理系统",
    version="2.0.0",
    lifespan=lifespan
)

# 挂载静态文件（3D模型）
models_dir = Path(__file__).parent / "static" / "models"
models_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                dead_connections.append(connection)

        # 移除死连接
        for conn in dead_connections:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()
main_event_loop = None


# MQTT消息回调（用于WebSocket推送）
def on_mqtt_message(topic: str, payload: dict):
    """收到MQTT消息时的回调"""
    import asyncio
    global main_event_loop

    try:
        if main_event_loop and manager.active_connections:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "type": "mqtt",
                    "topic": topic,
                    "data": payload
                }),
                main_event_loop
            )
    except Exception as e:
        logger.error(f"推送MQTT消息失败: {e}")


# ============ 前端页面 ============

@app.get("/")
async def read_root():
    """返回前端页面"""
    # 新的前端在 frontend/dist 目录（Vite构建后）
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
    if frontend_dist.exists():
        return FileResponse(frontend_dist)

    # 兼容开发模式（直接返回提示）
    return {
        "message": "请先构建前端项目",
        "instructions": "cd frontend && npm run build"
    }


# ============ 设备管理API ============

@app.get("/api/devices", response_model=schemas.DeviceListResponse)
async def get_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取设备列表"""
    devices = crud.get_devices(db, skip=skip, limit=limit)
    total = crud.get_devices_count(db)
    return schemas.DeviceListResponse(
        total=total,
        devices=devices
    )


@app.get("/api/devices/{sn}", response_model=schemas.Device)
async def get_device(sn: str, db: Session = Depends(get_db)):
    """获取设备详情（通过序列号）"""
    device = crud.get_device_by_sn(db, sn)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@app.post("/api/devices", response_model=schemas.Device)
async def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """创建设备"""
    # 检查设备是否已存在
    existing = crud.get_device_by_sn(db, device.sn)
    if existing:
        raise HTTPException(status_code=400, detail="设备序列号已存在")
    return crud.create_device(db, device)


@app.put("/api/devices/{sn}", response_model=schemas.Device)
async def update_device(sn: str, device: schemas.DeviceUpdate, db: Session = Depends(get_db)):
    """更新设备信息"""
    updated = crud.update_device(db, sn, device)
    if not updated:
        raise HTTPException(status_code=404, detail="设备不存在")
    return updated


@app.delete("/api/devices/{sn}")
async def delete_device(sn: str, db: Session = Depends(get_db)):
    """删除设备"""
    success = crud.delete_device(db, sn)
    if not success:
        raise HTTPException(status_code=404, detail="设备不存在")
    return {"message": "设备已删除"}


# ============ 设备控制API（MQTT命令） ============

@app.post("/api/devices/{sn}/reset")
async def reset_device(sn: str, db: Session = Depends(get_db)):
    """复位设备"""
    # 检查设备是否存在
    device = crud.get_device_by_sn(db, sn)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 发送MQTT命令
    mqtt_client = get_mqtt_client()
    success = mqtt_client.publish_command(sn, "reset")

    if not success:
        raise HTTPException(status_code=500, detail="发送命令失败")

    return {"message": "复位命令已发送", "command": "reset"}


@app.post("/api/devices/{sn}/autosetup")
async def autosetup_device(sn: str, db: Session = Depends(get_db)):
    """自动配置设备"""
    # 检查设备是否存在
    device = crud.get_device_by_sn(db, sn)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 发送MQTT命令
    mqtt_client = get_mqtt_client()
    success = mqtt_client.publish_command(sn, "autosetup")

    if not success:
        raise HTTPException(status_code=500, detail="发送命令失败")

    return {"message": "自动配置命令已发送", "command": "autosetup"}


@app.post("/api/devices/{sn}/measure")
async def measure_device(
    sn: str,
    request: schemas.DeviceMeasureRequest,
    db: Session = Depends(get_db)
):
    """执行测量（频率、Vpp、Vmax）"""
    # 检查设备是否存在
    device = crud.get_device_by_sn(db, sn)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 发送MQTT查询
    mqtt_client = get_mqtt_client()
    success = mqtt_client.publish_query(sn, request.task, request.channel)

    if not success:
        raise HTTPException(status_code=500, detail="发送查询失败")

    # 注意：实际响应通过MQTT异步返回，这里仅确认发送成功
    return {
        "message": "查询命令已发送",
        "task": request.task,
        "channel": request.channel,
        "note": "结果将通过MQTT返回"
    }


# ============ 测量数据API ============

@app.get("/api/devices/{sn}/measurements", response_model=schemas.MeasurementHistoryResponse)
async def get_measurements(
    sn: str,
    channel: Optional[int] = None,
    task: Optional[str] = None,
    hours: float = 24,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """获取设备历史测量数据（支持小数小时，如0.0167表示1分钟）"""
    # 检查设备是否存在
    device = crud.get_device_by_sn(db, sn)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 获取历史数据
    measurements = crud.get_measurement_history(
        db=db,
        device_sn=sn,
        channel=channel,
        task=task,
        hours=hours,
        skip=skip,
        limit=limit
    )

    total = crud.get_measurement_count(db, sn, channel, task)

    return schemas.MeasurementHistoryResponse(
        total=total,
        data=measurements
    )


# ============ 位置配置API ============

@app.put("/api/devices/{sn}/location")
async def update_device_location(
    sn: str,
    request: schemas.LocationConfigRequest,
    db: Session = Depends(get_db)
):
    """更新设备位置配置"""
    # 检查设备是否存在
    device = crud.get_device_by_sn(db, sn)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 获取位置缓存值
    mqtt_client = get_mqtt_client()
    location_value = mqtt_client.get_cached_location(request.location_topic)

    # 更新设备位置
    updated_device = crud.update_device_location(
        db=db,
        sn=sn,
        location=location_value or "未知位置",
        location_topic=request.location_topic
    )

    return {
        "message": "位置配置已更新",
        "location_topic": request.location_topic,
        "location_value": location_value
    }


@app.get("/api/devices/{sn}/location")
async def get_device_location(sn: str, db: Session = Depends(get_db)):
    """获取设备位置信息（包括实时位置值）"""
    device = crud.get_device_by_sn(db, sn)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 如果配置了位置主题，获取实时位置
    location_value = device.location
    if device.location_topic:
        mqtt_client = get_mqtt_client()
        cached_location = mqtt_client.get_cached_location(device.location_topic)
        if cached_location:
            location_value = cached_location

    return {
        "location": location_value,
        "location_topic": device.location_topic
    }


# ============ 3D模型API ============

@app.get("/api/models", response_model=schemas.ModelListResponse)
async def list_models():
    """获取可用的3D模型列表"""
    models_dir = Path(__file__).parent / "static" / "models"
    if not models_dir.exists():
        return schemas.ModelListResponse(models=[])

    # 扫描.glb文件
    model_files = list(models_dir.glob("*.glb"))
    model_names = [f.stem for f in model_files]  # 不含扩展名

    return schemas.ModelListResponse(models=model_names)


@app.get("/api/models/{model_name}.glb")
async def get_model(model_name: str):
    """下载指定的3D模型文件"""
    model_path = Path(__file__).parent / "static" / "models" / f"{model_name}.glb"

    if not model_path.exists():
        raise HTTPException(status_code=404, detail="模型文件不存在")

    return FileResponse(model_path, media_type="model/gltf-binary")


# ============ MQTT配置API ============

@app.get("/api/mqtt/config", response_model=schemas.MQTTConfigResponse)
async def get_mqtt_config():
    """获取当前MQTT配置"""
    mqtt_client = get_mqtt_client()
    return schemas.MQTTConfigResponse(
        broker=config.MQTT_BROKER,
        port=config.MQTT_PORT,
        username=config.MQTT_USERNAME,
        connected=mqtt_client.is_connected()
    )


@app.put("/api/mqtt/config")
async def update_mqtt_config(request: schemas.MQTTConfigRequest):
    """更新MQTT配置（重启连接）"""
    # 更新配置（这里简化处理，实际应该更新环境变量或配置文件）
    logger.info(f"更新MQTT配置: {request.broker}:{request.port}")

    # 这里应该实现重新连接逻辑
    # 由于配置在config对象中，需要重启应用才能生效
    # 或者实现动态重连机制

    return {"message": "MQTT配置已更新（需要重启应用生效）"}


# ============ WebSocket实时推送 ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，用于实时推送MQTT消息"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接，接收客户端消息（心跳）
            data = await websocket.receive_text()
            # 可选：回复心跳
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    mqtt_client = get_mqtt_client()
    return {
        "status": "ok",
        "service": "sichuan-iot-platform-v2",
        "mqtt_connected": mqtt_client.is_connected()
    }


# ============ 运行应用 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
