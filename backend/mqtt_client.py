"""
MQTT客户端模块
根据mqtt_protocal.md实现设备通信协议
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Callable, Dict
from threading import Lock
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from backend.config import config
from backend.database import SessionLocal
from backend import crud, schemas

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT客户端类 - 支持mqtt_protocal.md协议"""

    def __init__(self, on_message_callback: Optional[Callable] = None):
        """
        初始化MQTT客户端

        Args:
            on_message_callback: 收到消息时的回调函数（用于WebSocket推送）
        """
        self.client = mqtt.Client(client_id="device_manager_backend", protocol=mqtt.MQTTv311)
        self.on_message_callback = on_message_callback
        self.location_cache: Dict[str, str] = {}  # 缓存位置信息 {topic: location_value}
        self.pending_responses: Dict[str, asyncio.Future] = {}  # 存储等待响应的请求
        self.lock = Lock()

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

            # 订阅主题（根据mqtt_protocal.md）
            topics = [
                ("device/info", 0),  # 设备信息（每5秒推送）
                ("oscilloscope/+/set_rsp", 1),  # 控制命令响应 (+ 表示任意sn)
                ("oscilloscope/+/query_rsp", 1),  # 查询响应 (+ 表示任意sn)
                ("location/#", 0),  # 所有位置主题（用户自定义）
            ]
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"✓ 已订阅: {topic}")
        else:
            logger.error(f"✗ 连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        if rc != 0:
            logger.warning(f"⚠ 意外断开连接，错误码: {rc}，尝试重连...")
        else:
            logger.info("✓ 已断开MQTT连接")

    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())

            logger.info(f"收到消息: {topic} - {payload}")

            # 根据topic类型处理
            if topic == "device/info":
                self._handle_device_info(payload)
            elif topic.startswith("oscilloscope/") and topic.endswith("/set_rsp"):
                # 从主题中提取sn: oscilloscope/{sn}/set_rsp
                sn = topic.split('/')[1]
                self._handle_set_response(sn, payload)
            elif topic.startswith("oscilloscope/") and topic.endswith("/query_rsp"):
                # 从主题中提取sn: oscilloscope/{sn}/query_rsp
                sn = topic.split('/')[1]
                self._handle_query_response(sn, payload)
            elif topic.startswith("location/"):
                self._handle_location(topic, payload)

            # 调用回调函数（用于WebSocket推送）
            if self.on_message_callback:
                self.on_message_callback(topic, payload)

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {msg.payload}, 错误: {e}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)

    def _handle_device_info(self, payload: dict):
        """
        处理设备信息消息 - device/info
        消息格式: {task: "dev_info", type: "oscilloscope", manufacturer: "ZLG", model: "ZDS21104", sn: "OSC001"}
        """
        try:
            msg = schemas.DeviceInfoMessage(**payload)

            db: Session = SessionLocal()
            try:
                # 创建或更新设备
                device = crud.create_or_update_device_from_mqtt(
                    db=db,
                    sn=msg.sn,
                    device_type=msg.type,
                    manufacturer=msg.manufacturer,
                    model=msg.model
                )
                logger.info(f"✓ 更新设备信息: {msg.sn} ({msg.manufacturer} {msg.model})")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"处理设备信息失败: {e}")

    def _handle_set_response(self, sn: str, payload: dict):
        """
        处理控制命令响应 - oscilloscope/{sn}/set_rsp
        消息格式: {task: "reset", status: "done"}
        """
        try:
            msg = schemas.OscilloscopeSetResponse(**payload)
            logger.info(f"✓ [{sn}] 控制命令响应: {msg.task} -> {msg.status}")

            # 如果有等待响应的请求，设置结果
            with self.lock:
                key = f"set_{sn}_{msg.task}"
                if key in self.pending_responses:
                    future = self.pending_responses.pop(key)
                    if not future.done():
                        future.set_result(msg.dict())

        except Exception as e:
            logger.error(f"处理控制响应失败: {e}")

    def _handle_query_response(self, sn: str, payload: dict):
        """
        处理查询响应 - oscilloscope/{sn}/query_rsp
        消息格式: {task: "freq_meas", channel: 1, value: "999.99", unit: "Hz"}
        """
        try:
            msg = schemas.OscilloscopeQueryResponse(**payload)
            logger.info(f"✓ [{sn}] 查询响应: {msg.task} ch{msg.channel} = {msg.value}{msg.unit}")

            # 保存测量数据到数据库
            try:
                value_float = float(msg.value)
                db = SessionLocal()
                try:
                    crud.create_measurement(
                        db=db,
                        device_sn=sn,
                        channel=msg.channel,
                        task=msg.task,
                        value=value_float,
                        unit=msg.unit
                    )
                    logger.info(f"✓ [{sn}] 测量数据已保存: {msg.task} ch{msg.channel} = {value_float}{msg.unit}")
                finally:
                    db.close()
            except ValueError:
                logger.error(f"无法将值转换为浮点数: {msg.value}")

            # 如果有等待响应的请求，设置结果
            with self.lock:
                key = f"query_{sn}_{msg.task}_ch{msg.channel}"
                if key in self.pending_responses:
                    future = self.pending_responses.pop(key)
                    if not future.done():
                        try:
                            value_float = float(msg.value)
                            result = {
                                "task": msg.task,
                                "channel": msg.channel,
                                "value": value_float,
                                "unit": msg.unit,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            future.set_result(result)
                        except ValueError:
                            future.set_exception(ValueError(f"Invalid value: {msg.value}"))

        except Exception as e:
            logger.error(f"处理查询响应失败: {e}")

    def _handle_location(self, topic: str, payload: dict):
        """
        处理位置消息 - location/{topic}
        消息格式: {location: "桌子1"}
        """
        try:
            msg = schemas.LocationMessage(**payload)
            self.location_cache[topic] = msg.location
            logger.info(f"✓ 更新位置缓存: {topic} -> {msg.location}")

        except Exception as e:
            logger.error(f"处理位置消息失败: {e}")

    def get_cached_location(self, location_topic: str) -> Optional[str]:
        """获取缓存的位置值"""
        return self.location_cache.get(location_topic)

    def publish_command(self, sn: str, command: str) -> bool:
        """
        发布控制命令到 oscilloscope/{sn}/set

        Args:
            sn: 设备序列号
            command: "reset" 或 "autosetup"

        Returns:
            是否发布成功
        """
        try:
            message = {
                "task": command,
                "param": {}
            }
            topic = f"oscilloscope/{sn}/set"
            result = self.client.publish(topic, json.dumps(message), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ [{sn}] 已发布命令: {command}")
                return True
            else:
                logger.error(f"✗ [{sn}] 发布命令失败: {command}, rc={result.rc}")
                return False
        except Exception as e:
            logger.error(f"发布命令异常: {e}")
            return False

    def publish_query(self, sn: str, task: str, channel: int) -> bool:
        """
        发布查询请求到 oscilloscope/{sn}/query

        Args:
            sn: 设备序列号
            task: "freq_meas", "vpp_meas", "vmax_meas"
            channel: 通道号 1-4

        Returns:
            是否发布成功
        """
        try:
            message = {
                "task": task,
                "channel": channel
            }
            topic = f"oscilloscope/{sn}/query"
            result = self.client.publish(topic, json.dumps(message), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ [{sn}] 已发布查询: {task} ch{channel}")
                return True
            else:
                logger.error(f"✗ [{sn}] 发布查询失败: {task}, rc={result.rc}")
                return False
        except Exception as e:
            logger.error(f"发布查询异常: {e}")
            return False

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

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.client.is_connected()


# 全局MQTT客户端实例
mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    """获取全局MQTT客户端实例"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient()
    return mqtt_client


def init_mqtt_client(on_message_callback: Optional[Callable] = None):
    """初始化并启动MQTT客户端"""
    global mqtt_client
    mqtt_client = MQTTClient(on_message_callback=on_message_callback)
    mqtt_client.connect()
    mqtt_client.start_background()
    return mqtt_client
