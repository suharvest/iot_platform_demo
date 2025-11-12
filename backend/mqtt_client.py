"""
MQTT客户端模块
负责订阅设备消息并处理数据
"""
import json
import logging
from datetime import datetime
from typing import Optional, Callable
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from backend.config import config
from backend.database import SessionLocal
from backend import crud, schemas

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT客户端类"""

    def __init__(self, on_spectrum_callback: Optional[Callable] = None):
        """
        初始化MQTT客户端

        Args:
            on_spectrum_callback: 收到频谱数据时的回调函数
        """
        self.client = mqtt.Client(client_id="sichuan_iot_platform")
        self.on_spectrum_callback = on_spectrum_callback

        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # 设置认证
        if config.MQTT_USERNAME and config.MQTT_PASSWORD:
            self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            logger.info(f"✓ 已连接到MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")

            # 订阅所有设备的topic
            topics = [
                (f"{config.MQTT_TOPIC_PREFIX}/+/spectrum", 0),
                (f"{config.MQTT_TOPIC_PREFIX}/+/status", 1),
                (f"{config.MQTT_TOPIC_PREFIX}/+/heartbeat", 0),
            ]
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"✓ 已订阅: {topic}")
        else:
            logger.error(f"✗ 连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        if rc != 0:
            logger.warning(f"⚠ 意外断开连接，错误码: {rc}")

    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())

            logger.info(f"收到消息: {topic}")

            # 根据topic类型处理
            if "/spectrum" in topic:
                self._handle_spectrum(payload)
            elif "/status" in topic:
                self._handle_status(payload)
            elif "/heartbeat" in topic:
                self._handle_heartbeat(payload)

        except json.JSONDecodeError:
            logger.error(f"JSON解析失败: {msg.payload}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")

    def _handle_spectrum(self, payload: dict):
        """处理频谱数据"""
        try:
            # 验证消息格式
            msg = schemas.MQTTSpectrumMessage(**payload)

            # 获取数据库会话
            db: Session = SessionLocal()

            try:
                # 确保设备存在
                device = crud.get_device(db, msg.device_id)
                if not device:
                    # 自动创建设备
                    device_create = schemas.DeviceCreate(
                        name=msg.device_name,
                        device_id=msg.device_id,
                        center_frequency=msg.center_frequency,
                    )
                    device = crud.create_device(db, device_create)
                    logger.info(f"✓ 自动创建设备: {msg.device_id}")

                # 更新设备状态为在线
                crud.update_device_status(
                    db, msg.device_id, "online", msg.center_frequency
                )

                # 保存频谱数据
                spectrum_create = schemas.SpectrumDataCreate(
                    device_id=msg.device_id,
                    peak_frequency=msg.peak_frequency,
                    data_json=json.dumps(msg.data_points),
                )
                crud.create_spectrum_data(db, spectrum_create)

                logger.info(
                    f"✓ 已保存频谱数据: {msg.device_id}, peak={msg.peak_frequency}GHz"
                )

                # 调用回调函数（用于WebSocket推送）
                if self.on_spectrum_callback:
                    self.on_spectrum_callback(payload)

            finally:
                db.close()

        except Exception as e:
            logger.error(f"处理频谱数据失败: {e}")

    def _handle_status(self, payload: dict):
        """处理设备状态消息"""
        try:
            msg = schemas.MQTTStatusMessage(**payload)

            db: Session = SessionLocal()
            try:
                # 更新设备状态
                device = crud.get_device(db, msg.device_id)
                if device:
                    crud.update_device_status(
                        db, msg.device_id, msg.status, msg.center_frequency
                    )
                    logger.info(f"✓ 更新设备状态: {msg.device_id} -> {msg.status}")
                else:
                    logger.warning(f"设备不存在: {msg.device_id}")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"处理状态消息失败: {e}")

    def _handle_heartbeat(self, payload: dict):
        """处理心跳消息"""
        try:
            msg = schemas.MQTTHeartbeatMessage(**payload)
            logger.debug(f"收到心跳: {msg.device_id}")

            # 更新设备最后活跃时间
            db: Session = SessionLocal()
            try:
                device = crud.get_device(db, msg.device_id)
                if device:
                    device.last_update = datetime.utcnow()
                    db.commit()
            finally:
                db.close()

        except Exception as e:
            logger.error(f"处理心跳失败: {e}")

    def connect(self):
        """连接到MQTT Broker"""
        try:
            self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
            logger.info(f"正在连接MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise

    def start(self):
        """启动MQTT客户端（阻塞模式）"""
        self.client.loop_forever()

    def start_background(self):
        """启动MQTT客户端（后台模式）"""
        self.client.loop_start()

    def stop(self):
        """停止MQTT客户端"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT客户端已停止")


# 全局MQTT客户端实例
mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    """获取全局MQTT客户端实例"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient()
    return mqtt_client
