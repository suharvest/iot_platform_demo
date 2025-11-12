#!/usr/bin/env python3
"""
MQTT设备模拟器
用于测试系统功能
"""
import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt

# 配置
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
DEVICE_ID = "A7B3-9C2D-E5F6"
DEVICE_NAME = "RF-Scanner-01"
CENTER_FREQUENCY = 1.2


def generate_spectrum_data(prev_base=None):
    """生成模拟的频谱数据"""
    # 生成60个数据点（代表1分钟）
    data_points = []

    # 如果有上一次的基准频率，在此基础上随机漂移，模拟连续变化
    if prev_base is None:
        base_freq = 2.45  # 初始基准频率2.45GHz
    else:
        # 在上一次的基础上随机漂移 ±0.05GHz
        base_freq = prev_base + random.uniform(-0.05, 0.05)
        # 限制在合理范围内
        base_freq = max(2.3, min(2.6, base_freq))

    for i in range(60):
        time_sec = i / 60.0  # 0-1分钟
        # 添加随机波动，并模拟正弦波形
        wave = 0.1 * random.random() * (1 + 0.5 * random.choice([-1, 1]) * (i % 20) / 10)
        freq = base_freq + random.uniform(-0.15, 0.15) + wave
        data_points.append([time_sec, round(freq, 3)])

    # 计算峰值频率
    peak_frequency = max(data_points, key=lambda x: x[1])[1]

    return {
        "device_id": DEVICE_ID,
        "device_name": DEVICE_NAME,
        "peak_frequency": peak_frequency,
        "center_frequency": CENTER_FREQUENCY,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data_points": data_points
    }, base_freq


def on_connect(client, userdata, flags, rc):
    """连接回调"""
    if rc == 0:
        print(f"✓ 已连接到MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"✗ 连接失败，错误码: {rc}")


def main():
    """主函数"""
    print("========================================")
    print("  MQTT设备模拟器")
    print("========================================")
    print(f"设备ID: {DEVICE_ID}")
    print(f"设备名称: {DEVICE_NAME}")
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print("========================================")
    print()

    # 创建MQTT客户端
    client = mqtt.Client(client_id=f"simulator_{DEVICE_ID}")
    client.on_connect = on_connect

    # 连接
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return

    time.sleep(1)

    # 发送上线状态
    status_topic = f"devices/{DEVICE_ID}/status"
    status_msg = {
        "device_id": DEVICE_ID,
        "status": "online",
        "center_frequency": CENTER_FREQUENCY,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    client.publish(status_topic, json.dumps(status_msg), qos=1)
    print(f"✓ 已发送上线状态")

    # 定时发送频谱数据
    spectrum_topic = f"devices/{DEVICE_ID}/spectrum"
    heartbeat_topic = f"devices/{DEVICE_ID}/heartbeat"

    print(f"✓ 开始发送数据...")
    print(f"   频谱数据: 每5秒")
    print(f"   心跳: 每30秒")
    print()
    print("按 Ctrl+C 停止")
    print()

    count = 0
    last_base_freq = None  # 保存上一次的基准频率
    try:
        while True:
            # 发送频谱数据（连续变化）
            spectrum_data, last_base_freq = generate_spectrum_data(last_base_freq)
            client.publish(spectrum_topic, json.dumps(spectrum_data), qos=0)
            print(f"[{count}] 已发送频谱数据: peak={spectrum_data['peak_frequency']:.2f}GHz, base={last_base_freq:.2f}GHz")

            # 每6次发送一次心跳（5秒*6=30秒）
            if count % 6 == 0:
                heartbeat_msg = {
                    "device_id": DEVICE_ID,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                client.publish(heartbeat_topic, json.dumps(heartbeat_msg), qos=0)
                print(f"[{count}] 已发送心跳")

            count += 1
            time.sleep(5)  # 每5秒发送一次

    except KeyboardInterrupt:
        print()
        print("停止模拟器...")

        # 发送离线状态
        status_msg = {
            "device_id": DEVICE_ID,
            "status": "offline",
            "center_frequency": CENTER_FREQUENCY,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        client.publish(status_topic, json.dumps(status_msg), qos=1)
        print("✓ 已发送离线状态")

        client.loop_stop()
        client.disconnect()
        print("✓ 已断开连接")


if __name__ == "__main__":
    main()
