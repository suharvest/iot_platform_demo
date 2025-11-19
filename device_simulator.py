#!/usr/bin/env python3
"""
MQTT设备模拟器 V2.0
根据mqtt_protocal.md协议模拟设备
- 3个示波器设备（支持详情页的完整功能）
- 2个IoT设备（仅基础信息，不支持测量）
"""

import json
import time
import random
import argparse
from datetime import datetime
from typing import Dict, List
import paho.mqtt.client as mqtt


class OscilloscopeSimulator:
    """示波器模拟器 - 支持完整的测量和控制功能"""

    def __init__(
        self,
        broker: str = "127.0.0.1",
        port: int = 1883,
        device_sn: str = "OSC001",
        manufacturer: str = "ZLG",
        model: str = "ZDS21104"
    ):
        self.broker = broker
        self.port = port
        self.device_sn = device_sn
        self.manufacturer = manufacturer
        self.model = model
        self.device_type = "oscilloscope"

        # MQTT客户端
        self.client = mqtt.Client(client_id=f"simulator_{device_sn}")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # 模拟测量数据（各通道）
        self.channel_data = {
            1: {"freq": 120.0, "vpp": 3.3, "vmax": 3.5},
            2: {"freq": 240.0, "vpp": 5.0, "vmax": 5.2},
            3: {"freq": 60.0, "vpp": 1.8, "vmax": 2.0},
            4: {"freq": 480.0, "vpp": 2.5, "vmax": 2.7},
        }

        self.running = False

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            print(f"✓ [{self.device_sn}] 已连接到MQTT Broker")

            # 订阅控制和查询主题（包含设备序列号）
            client.subscribe(f"oscilloscope/{self.device_sn}/set", qos=1)
            client.subscribe(f"oscilloscope/{self.device_sn}/query", qos=1)
            print(f"✓ [{self.device_sn}] 已订阅: oscilloscope/{self.device_sn}/set, oscilloscope/{self.device_sn}/query")
        else:
            print(f"✗ [{self.device_sn}] 连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        if rc != 0:
            print(f"⚠ [{self.device_sn}] 意外断开连接，错误码: {rc}")

    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            payload = json.loads(msg.payload.decode())
            print(f"\n📨 [{self.device_sn}] 收到消息: {msg.topic} - {payload}")

            # 处理控制命令
            if msg.topic == f"oscilloscope/{self.device_sn}/set":
                self._handle_set_command(payload)

            # 处理查询请求
            elif msg.topic == f"oscilloscope/{self.device_sn}/query":
                self._handle_query(payload)

        except json.JSONDecodeError as e:
            print(f"✗ [{self.device_sn}] JSON解析失败: {e}")
        except Exception as e:
            print(f"✗ [{self.device_sn}] 处理消息失败: {e}")

    def _handle_set_command(self, payload: Dict):
        """处理控制命令"""
        task = payload.get("task")
        param = payload.get("param", {})

        print(f"⚙️  [{self.device_sn}] 执行命令: {task}")

        # 模拟命令执行延迟
        time.sleep(0.3)

        # 发送响应
        response = {
            "task": task,
            "status": "done"
        }

        self.client.publish(f"oscilloscope/{self.device_sn}/set_rsp", json.dumps(response), qos=1)
        print(f"✓ [{self.device_sn}] 命令响应已发送: {task} -> done")

        # 执行相应的操作
        if task == "reset":
            print(f"   [{self.device_sn}] [模拟] 设备复位中...")
            for ch in self.channel_data:
                self.channel_data[ch]["freq"] += random.uniform(-10, 10)

        elif task == "autosetup":
            print(f"   [{self.device_sn}] [模拟] 自动配置中...")
            for ch in self.channel_data:
                self.channel_data[ch]["vpp"] *= random.uniform(0.9, 1.1)

    def _handle_query(self, payload: Dict):
        """处理查询请求"""
        task = payload.get("task")
        channel = payload.get("channel", 1)

        print(f"🔍 [{self.device_sn}] 查询: {task}, 通道: {channel}")

        # 获取通道数据
        if channel not in self.channel_data:
            print(f"✗ [{self.device_sn}] 无效的通道: {channel}")
            return

        ch_data = self.channel_data[channel]

        # 根据查询类型返回数据
        value = None
        unit = None

        if task == "freq_meas":
            # 频率测量（添加随机波动）
            value = ch_data["freq"] + random.uniform(-5, 5)
            unit = "Hz"

        elif task == "vpp_meas":
            # 峰峰值测量
            value = ch_data["vpp"] + random.uniform(-0.1, 0.1)
            unit = "V"

        elif task == "vmax_meas":
            # 最大值测量
            value = ch_data["vmax"] + random.uniform(-0.1, 0.1)
            unit = "V"

        else:
            print(f"✗ [{self.device_sn}] 未知的查询任务: {task}")
            return

        # 发送查询响应
        response = {
            "task": task,
            "channel": channel,
            "value": f"{value:.2f}",  # 字符串格式，保留2位小数
            "unit": unit
        }

        self.client.publish(f"oscilloscope/{self.device_sn}/query_rsp", json.dumps(response), qos=1)
        print(f"✓ [{self.device_sn}] 查询响应已发送: {value:.2f} {unit}")

    def _send_device_info(self):
        """发送设备信息（每5秒）"""
        message = {
            "task": "dev_info",
            "type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "sn": self.device_sn
        }

        self.client.publish("device/info", json.dumps(message), qos=0)
        # print(f"📤 [{self.device_sn}] 发送设备信息")

    def connect(self):
        """连接到MQTT Broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"✗ [{self.device_sn}] 连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def run(self):
        """运行模拟器"""
        if not self.connect():
            return

        self.running = True

        try:
            # 立即发送一次设备信息
            self._send_device_info()

            last_info_time = time.time()
            info_interval = 5  # 5秒发送一次设备信息

            while self.running:
                current_time = time.time()

                # 定期发送设备信息
                if current_time - last_info_time >= info_interval:
                    self._send_device_info()
                    last_info_time = current_time

                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            self.disconnect()


class IoTDeviceSimulator:
    """IoT设备模拟器 - 仅发送基础设备信息，不支持测量功能"""

    def __init__(
        self,
        broker: str = "127.0.0.1",
        port: int = 1883,
        device_sn: str = "IOT001",
        manufacturer: str = "Generic",
        model: str = "SensorNode1",
        device_type: str = "sensor"
    ):
        self.broker = broker
        self.port = port
        self.device_sn = device_sn
        self.manufacturer = manufacturer
        self.model = model
        self.device_type = device_type

        # MQTT客户端
        self.client = mqtt.Client(client_id=f"simulator_{device_sn}")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.running = False

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            print(f"✓ [{self.device_sn}] 已连接到MQTT Broker")
        else:
            print(f"✗ [{self.device_sn}] 连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        if rc != 0:
            print(f"⚠ [{self.device_sn}] 意外断开连接，错误码: {rc}")

    def _send_device_info(self):
        """发送设备信息（每5秒）"""
        message = {
            "task": "dev_info",
            "type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "sn": self.device_sn
        }

        self.client.publish("device/info", json.dumps(message), qos=0)
        # print(f"📤 [{self.device_sn}] 发送设备信息")

    def connect(self):
        """连接到MQTT Broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"✗ [{self.device_sn}] 连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def run(self):
        """运行模拟器"""
        if not self.connect():
            return

        self.running = True

        try:
            # 立即发送一次设备信息
            self._send_device_info()

            last_info_time = time.time()
            info_interval = 5  # 5秒发送一次设备信息

            while self.running:
                current_time = time.time()

                # 定期发送设备信息
                if current_time - last_info_time >= info_interval:
                    self._send_device_info()
                    last_info_time = current_time

                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            self.disconnect()


class LocationSimulator:
    """位置模拟器（独立设备）"""

    def __init__(
        self,
        broker: str = "127.0.0.1",
        port: int = 1883,
        location_id: str = "desk1",
        location_name: str = "桌子1"
    ):
        self.broker = broker
        self.port = port
        self.location_id = location_id
        self.location_name = location_name

        self.client = mqtt.Client(client_id=f"location_sim_{location_id}")
        self.running = False

    def connect(self):
        """连接到MQTT Broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(0.3)
            return True
        except Exception as e:
            print(f"✗ [Location-{self.location_id}] 连接失败: {e}")
            return False

    def send_location(self):
        """发送位置信息"""
        topic = f"location/{self.location_id}"
        message = {
            "location": self.location_name
        }

        self.client.publish(topic, json.dumps(message), qos=0)
        # print(f"📍 [Location-{self.location_id}] 发送位置: {self.location_name}")

    def run(self):
        """运行位置模拟器"""
        if not self.connect():
            return

        self.running = True

        try:
            # 立即发送一次位置信息
            self.send_location()

            # 每10秒发送一次
            interval = 10
            last_time = time.time()

            while self.running:
                current_time = time.time()
                if current_time - last_time >= interval:
                    self.send_location()
                    last_time = current_time

                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            self.client.loop_stop()
            self.client.disconnect()


def run_default_simulator(broker: str = "127.0.0.1", port: int = 1883):
    """运行默认的5设备模拟器（3个示波器 + 2个IoT设备）"""
    import threading

    print("="*70)
    print("  🚀 启动设备模拟器")
    print("  - 3个示波器设备（支持详情页功能）")
    print("  - 2个IoT设备（仅基础信息）")
    print("  - 5个位置追踪器")
    print("="*70)
    print()

    simulators = []

    # 3个示波器设备（支持完整功能）
    oscilloscope_configs = [
        {
            "sn": "OSC001",
            "manufacturer": "ZLG",
            "model": "ZDS21104",
            "name": "Oscilloscope 1"
        },
        {
            "sn": "OSC002",
            "manufacturer": "ZLG",
            "model": "ZDS21034",
            "name": "Oscilloscope 2"
        },
        {
            "sn": "OSC003",
            "manufacturer": "Tektronix",
            "model": "TBS2000",
            "name": "Oscilloscope 3"
        },
    ]

    print("📊 示波器设备（支持详情页）：")
    for config in oscilloscope_configs:
        sim = OscilloscopeSimulator(
            broker=broker,
            port=port,
            device_sn=config["sn"],
            manufacturer=config["manufacturer"],
            model=config["model"]
        )
        simulators.append(sim)
        print(f"   - {config['name']}: {config['manufacturer']} {config['model']} (SN: {config['sn']})")

    print()

    # 2个IoT设备（仅基础信息，不支持详情页）
    iot_configs = [
        {
            "sn": "IOT001",
            "manufacturer": "Generic",
            "model": "SensorNode1",
            "device_type": "sensor",
            "name": "IoT Device A"
        },
        {
            "sn": "IOT002",
            "manufacturer": "Generic",
            "model": "Actuator2",
            "device_type": "actuator",
            "name": "IoT Device B"
        },
    ]

    print("🔌 IoT设备（仅基础信息）：")
    for config in iot_configs:
        sim = IoTDeviceSimulator(
            broker=broker,
            port=port,
            device_sn=config["sn"],
            manufacturer=config["manufacturer"],
            model=config["model"],
            device_type=config["device_type"]
        )
        simulators.append(sim)
        print(f"   - {config['name']}: {config['manufacturer']} {config['model']} (SN: {config['sn']})")

    print()

    # 5个位置追踪器
    location_configs = [
        {"id": "desk1", "name": "桌子1"},
        {"id": "desk2", "name": "桌子2"},
        {"id": "desk3", "name": "桌子3"},
        {"id": "shelf1", "name": "货架1"},
        {"id": "workbench", "name": "工作台"},
    ]

    location_sims = []
    print("📍 位置追踪器：")
    for config in location_configs:
        loc_sim = LocationSimulator(
            broker=broker,
            port=port,
            location_id=config["id"],
            location_name=config["name"]
        )
        location_sims.append(loc_sim)
        print(f"   - {config['id']}: {config['name']}")

    print()
    print("-"*70)

    # 启动所有模拟器（在后台线程中）
    threads = []

    print("\n🔌 正在启动所有设备...")
    for sim in simulators:
        thread = threading.Thread(target=sim.run, daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(0.3)  # 避免同时连接

    print("\n📍 正在启动位置追踪器...")
    for loc_sim in location_sims:
        thread = threading.Thread(target=loc_sim.run, daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(0.2)

    print("\n" + "="*70)
    print("  ✅ 所有模拟器已启动")
    print("="*70)
    print()
    print("💡 提示：")
    print("  - 示波器设备会响应 oscilloscope/set 和 oscilloscope/query 命令")
    print("  - IoT设备仅发送基础信息，不支持测量功能")
    print("  - 所有设备每5秒发送一次 device/info")
    print("  - 位置追踪器每10秒发送一次位置信息")
    print()
    print("⌨️  按 Ctrl+C 停止所有模拟器")
    print()

    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  正在停止所有模拟器...")
        for sim in simulators:
            sim.running = False
        for loc_sim in location_sims:
            loc_sim.running = False

        # 等待线程结束
        for thread in threads:
            thread.join(timeout=1)

        print("✅ 所有模拟器已停止")
        print("👋 再见！\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="MQTT设备模拟器 V2.0 - 根据mqtt_protocal.md协议",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 启动默认5设备模拟器（3个示波器 + 2个IoT设备）
  python device_simulator_v2.py

  # 指定MQTT Broker地址
  python device_simulator_v2.py --broker mqtt.example.com --port 1883

  # 单独启动一个示波器
  python device_simulator_v2.py --single-osc --sn OSC999 --model ZDS21104

  # 单独启动一个IoT设备
  python device_simulator_v2.py --single-iot --sn IOT999 --model SensorX

  # 仅启动位置模拟器
  python device_simulator_v2.py --location-only --location-id desk9 --location-name 桌子9
        """
    )

    parser.add_argument(
        "--broker",
        default="127.0.0.1",
        help="MQTT Broker地址 (默认: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT Broker端口 (默认: 1883)"
    )

    parser.add_argument(
        "--single-osc",
        action="store_true",
        help="仅启动单个示波器设备"
    )

    parser.add_argument(
        "--single-iot",
        action="store_true",
        help="仅启动单个IoT设备"
    )

    parser.add_argument(
        "--sn",
        default="OSC001",
        help="设备序列号 (默认: OSC001)"
    )

    parser.add_argument(
        "--manufacturer",
        default="ZLG",
        help="制造商 (默认: ZLG)"
    )

    parser.add_argument(
        "--model",
        default="ZDS21104",
        help="设备型号 (默认: ZDS21104)"
    )

    parser.add_argument(
        "--device-type",
        default="sensor",
        help="IoT设备类型 (默认: sensor)"
    )

    parser.add_argument(
        "--location-only",
        action="store_true",
        help="仅启动位置模拟器"
    )

    parser.add_argument(
        "--location-id",
        default="desk1",
        help="位置ID (默认: desk1)"
    )

    parser.add_argument(
        "--location-name",
        default="桌子1",
        help="位置名称 (默认: 桌子1)"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("  MQTT设备模拟器 V2.0")
    print("  根据 mqtt_protocal.md 协议")
    print("="*70 + "\n")

    # 单个示波器模式
    if args.single_osc:
        simulator = OscilloscopeSimulator(
            broker=args.broker,
            port=args.port,
            device_sn=args.sn,
            manufacturer=args.manufacturer,
            model=args.model
        )
        print(f"🚀 启动单个示波器: {args.sn} ({args.manufacturer} {args.model})")
        print(f"🔌 连接到: {args.broker}:{args.port}\n")
        simulator.run()

    # 单个IoT设备模式
    elif args.single_iot:
        simulator = IoTDeviceSimulator(
            broker=args.broker,
            port=args.port,
            device_sn=args.sn,
            manufacturer=args.manufacturer,
            model=args.model,
            device_type=args.device_type
        )
        print(f"🚀 启动单个IoT设备: {args.sn} ({args.manufacturer} {args.model})")
        print(f"🔌 连接到: {args.broker}:{args.port}\n")
        simulator.run()

    # 仅位置模拟器
    elif args.location_only:
        loc_sim = LocationSimulator(
            broker=args.broker,
            port=args.port,
            location_id=args.location_id,
            location_name=args.location_name
        )
        print(f"🚀 启动位置模拟器: {args.location_id} -> {args.location_name}")
        print(f"🔌 连接到: {args.broker}:{args.port}\n")
        loc_sim.run()

    # 默认5设备模式
    else:
        print(f"🔌 连接到: {args.broker}:{args.port}\n")
        run_default_simulator(broker=args.broker, port=args.port)


if __name__ == "__main__":
    main()
