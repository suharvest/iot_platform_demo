"""
FastAPI主应用
"""
import json
import logging
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path

from backend.database import get_db, init_db
from backend import crud, schemas
from backend.mqtt_client import get_mqtt_client, MQTTClient
from backend.config import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="四川物联网平台",
    description="产线设备实时监控系统",
    version="0.1.0",
)

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

# 全局事件循环引用
main_event_loop = None


# MQTT消息回调（用于WebSocket推送）
def on_spectrum_received(data: dict):
    """收到频谱数据时的回调"""
    import asyncio
    global main_event_loop

    try:
        if main_event_loop and manager.active_connections:
            # 使用主事件循环在另一个线程中运行协程
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "type": "spectrum",
                    "data": data
                }),
                main_event_loop
            )
    except Exception as e:
        logger.error(f"推送频谱数据失败: {e}")


# ============ 启动和关闭事件 ============

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    import asyncio
    global main_event_loop

    logger.info("🚀 启动四川物联网平台...")

    # 保存主事件循环引用
    main_event_loop = asyncio.get_event_loop()

    # 初始化数据库
    init_db()

    # 启动MQTT客户端
    mqtt_client = MQTTClient(on_spectrum_callback=on_spectrum_received)
    try:
        mqtt_client.connect()
        mqtt_client.start_background()
        logger.info("✓ MQTT客户端已启动")
    except Exception as e:
        logger.error(f"✗ MQTT客户端启动失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("关闭应用...")
    try:
        mqtt_client = get_mqtt_client()
        mqtt_client.stop()
    except:
        pass


# ============ 静态文件和首页 ============

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回前端页面"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    else:
        return HTMLResponse(content="<h1>前端页面未找到</h1><p>请检查frontend/index.html是否存在</p>")


# ============ 设备管理API ============

@app.get("/api/devices", response_model=schemas.DeviceListResponse)
async def get_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取设备列表"""
    devices = crud.get_devices(db, skip=skip, limit=limit)
    return schemas.DeviceListResponse(
        total=len(devices),
        devices=devices
    )


@app.get("/api/devices/{device_id}", response_model=schemas.Device)
async def get_device(device_id: str, db: Session = Depends(get_db)):
    """获取设备详情"""
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@app.post("/api/devices", response_model=schemas.Device)
async def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """创建设备"""
    # 检查设备是否已存在
    existing = crud.get_device(db, device.device_id)
    if existing:
        raise HTTPException(status_code=400, detail="设备ID已存在")
    return crud.create_device(db, device)


@app.put("/api/devices/{device_id}", response_model=schemas.Device)
async def update_device(device_id: str, device: schemas.DeviceUpdate, db: Session = Depends(get_db)):
    """更新设备"""
    updated = crud.update_device(db, device_id, device)
    if not updated:
        raise HTTPException(status_code=404, detail="设备不存在")
    return updated


@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str, db: Session = Depends(get_db)):
    """删除设备"""
    success = crud.delete_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="设备不存在")
    return {"message": "设备已删除"}


# ============ 频谱数据API ============

@app.get("/api/spectrum/latest")
async def get_latest_spectrum(device_id: str, db: Session = Depends(get_db)):
    """获取最新频谱数据"""
    spectrum = crud.get_latest_spectrum_data(db, device_id)
    if not spectrum:
        raise HTTPException(status_code=404, detail="暂无频谱数据")

    # 解析JSON数据
    data_dict = spectrum.to_dict()
    if data_dict["data_json"]:
        try:
            data_dict["data_points"] = json.loads(data_dict["data_json"])
            del data_dict["data_json"]
        except:
            pass

    return data_dict


@app.get("/api/spectrum/history", response_model=schemas.SpectrumHistoryResponse)
async def get_spectrum_history(
    device_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """获取历史频谱数据（分页）"""
    skip = (page - 1) * page_size
    data = crud.get_spectrum_history(db, device_id, skip=skip, limit=page_size)
    total = crud.get_spectrum_count(db, device_id)

    return schemas.SpectrumHistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=data
    )


# ============ WebSocket实时推送 ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，用于实时推送频谱数据"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接，接收客户端消息（心跳）
            data = await websocket.receive_text()
            # 可以在这里处理客户端发来的消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "sichuan-iot-platform"}


# ============ 运行应用 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )
