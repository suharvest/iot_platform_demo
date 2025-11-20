#!/usr/bin/env python3
"""
测试设备离线检测功能

测试场景:
1. 启动一个设备模拟器,验证设备在线
2. 停止模拟器,等待16秒
3. 查询设备状态,验证设备离线
"""

import time
import requests
import json
import sys
import threading
from device_simulator import OscilloscopeSimulator

# API 基础URL
API_BASE = "http://127.0.0.1:9099/api"

# 测试设备配置
TEST_DEVICE = {
    "sn": "OSC001",
    "manufacturer": "ZLG",
    "model": "ZDS21104"
}


def get_device_status(sn: str) -> dict:
    """获取设备状态"""
    try:
        response = requests.get(f"{API_BASE}/devices/{sn}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"✗ 获取设备状态失败: {e}")
        return None


def wait_with_countdown(seconds: int, message: str):
    """带倒计时的等待"""
    print(f"\n{message}")
    for i in range(seconds, 0, -1):
        print(f"   倒计时: {i} 秒...", end="\r")
        time.sleep(1)
    print(" " * 50, end="\r")  # 清除倒计时行


def main():
    print("=" * 70)
    print("  设备离线检测功能测试")
    print("=" * 70)
    print()

    # 第1步: 启动设备模拟器
    print("📍 步骤1: 启动设备模拟器")
    print(f"   - 设备序列号: {TEST_DEVICE['sn']}")
    print(f"   - 制造商: {TEST_DEVICE['manufacturer']}")
    print(f"   - 型号: {TEST_DEVICE['model']}")

    simulator = OscilloscopeSimulator(
        broker="127.0.0.1",
        port=1883,
        device_sn=TEST_DEVICE["sn"],
        manufacturer=TEST_DEVICE["manufacturer"],
        model=TEST_DEVICE["model"]
    )

    # 在后台线程中运行模拟器
    sim_thread = threading.Thread(target=simulator.run, daemon=True)
    sim_thread.start()

    # 等待设备上线
    wait_with_countdown(8, "   等待设备发送心跳并上线...")

    # 第2步: 验证设备在线
    print("\n📍 步骤2: 验证设备在线状态")
    device = get_device_status(TEST_DEVICE["sn"])

    if device:
        print(f"   ✓ 设备信息已获取")
        print(f"   - 设备名称: {device.get('device_name')}")
        print(f"   - 当前状态: {device.get('status')}")
        print(f"   - 最后更新: {device.get('last_update')}")

        if device.get('status') == 'online':
            print(f"   ✅ 设备状态正确: online")
        else:
            print(f"   ❌ 设备状态错误: 预期 online, 实际 {device.get('status')}")
    else:
        print("   ❌ 无法获取设备信息")
        return

    # 第3步: 停止设备模拟器
    print("\n📍 步骤3: 停止设备模拟器")
    simulator.disconnect()
    print("   ✓ 设备模拟器已停止发送心跳")

    # 第4步: 等待离线超时
    wait_with_countdown(16, "   等待设备离线超时 (15秒超时 + 1秒余量)...")

    # 第5步: 验证设备离线
    print("\n📍 步骤4: 验证设备离线状态")
    device = get_device_status(TEST_DEVICE["sn"])

    if device:
        print(f"   ✓ 设备信息已获取")
        print(f"   - 设备名称: {device.get('device_name')}")
        print(f"   - 当前状态: {device.get('status')}")
        print(f"   - 最后更新: {device.get('last_update')}")

        if device.get('status') == 'offline':
            print(f"   ✅ 设备状态正确: offline")
        else:
            print(f"   ❌ 设备状态错误: 预期 offline, 实际 {device.get('status')}")
    else:
        print("   ❌ 无法获取设备信息")

    # 总结
    print("\n" + "=" * 70)
    print("  测试完成!")
    print("=" * 70)
    print("\n💡 离线检测逻辑:")
    print("   - 设备每5秒发送一次心跳 (device/info)")
    print("   - 超过15秒未收到心跳则判定为离线")
    print("   - 状态是在API查询时动态计算的,不会持久化到数据库")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        sys.exit(0)
