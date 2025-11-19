"""
配置管理模块
从环境变量加载配置
"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Config:
    """系统配置类"""

    # MQTT配置
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "devices")

    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/devices.db")

    # API服务配置
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

    # 启动配置
    START_LOCAL_MQTT = os.getenv("START_LOCAL_MQTT", "false").lower() == "true"

    @classmethod
    def get_mqtt_config(cls):
        """获取MQTT配置字典"""
        config = {
            "broker": cls.MQTT_BROKER,
            "port": cls.MQTT_PORT,
        }
        if cls.MQTT_USERNAME:
            config["username"] = cls.MQTT_USERNAME
        if cls.MQTT_PASSWORD:
            config["password"] = cls.MQTT_PASSWORD
        return config


# 创建全局配置实例
config = Config()
