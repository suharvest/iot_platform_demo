# MQTT通信协议规约

## 1. Broker配置

### 1.1 默认配置
- **地址**: `localhost`
- **端口**: `1883`
- **协议**: MQTT v3.1.1 或 v5.0

### 1.2 支持外部Broker
本系统支持配置外部MQTT Broker，通过 `.env` 文件配置：

```bash
MQTT_BROKER=your-broker-address
MQTT_PORT=1883
MQTT_USERNAME=your-username  # 可选
MQTT_PASSWORD=your-password  # 可选
```

### 1.3 常见Broker选择
- **本地开发**: Mosquitto
- **云服务**: EMQX Cloud, AWS IoT Core, Azure IoT Hub
- **企业级**: EMQX Enterprise, HiveMQ

---

## 2. Topic规范

### 2.1 Topic层级结构

```
devices/
├── {device_id}/
│   ├── spectrum      # 频谱数据上报
│   ├── status        # 设备状态上报
│   ├── heartbeat     # 心跳消息
│   └── command       # 平台下发指令（预留）
```

### 2.2 Topic详细说明

| Topic | 方向 | QoS | 描述 |
|-------|------|-----|------|
| `devices/{device_id}/spectrum` | 设备→平台 | 0 | 频谱数据实时上报 |
| `devices/{device_id}/status` | 设备→平台 | 1 | 设备状态变更 |
| `devices/{device_id}/heartbeat` | 设备→平台 | 0 | 心跳保活 |
| `devices/{device_id}/command` | 平台→设备 | 1 | 控制指令（预留） |

**注意**: `{device_id}` 为设备唯一标识符，例如: `A7B3-9C2D-E5F6`

---

## 3. 消息格式规范

所有消息均采用 **JSON格式**，UTF-8编码。

### 3.1 频谱数据消息

**Topic**: `devices/{device_id}/spectrum`

**频率**: 实时上报（约1秒1次）

**QoS**: 0（允许丢失，保证实时性）

**消息结构**:
```json
{
  "device_id": "A7B3-9C2D-E5F6",
  "device_name": "RF-Scanner-01",
  "peak_frequency": 2.45,
  "center_frequency": 1.2,
  "timestamp": "2025-11-12T10:30:45.123Z",
  "data_points": [
    [0.0, 2.450],
    [0.2, 2.432],
    [0.4, 2.478],
    [0.6, 2.391],
    [0.8, 2.512],
    [1.0, 2.445]
  ]
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | String | ✓ | 设备唯一标识符 |
| `device_name` | String | ✓ | 设备显示名称 |
| `peak_frequency` | Float | ✓ | 当前峰值频率（GHz） |
| `center_frequency` | Float | ✓ | 中心频率（GHz） |
| `timestamp` | String (ISO 8601) | ✓ | 采集时间戳 |
| `data_points` | Array | ✓ | 频谱数据点 [时间(秒), 频率(GHz)] |

**示例Python代码**:
```python
import paho.mqtt.client as mqtt
import json
from datetime import datetime

def publish_spectrum_data(client, device_id, peak_freq, center_freq, data_points):
    topic = f"devices/{device_id}/spectrum"
    payload = {
        "device_id": device_id,
        "device_name": "RF-Scanner-01",
        "peak_frequency": peak_freq,
        "center_frequency": center_freq,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data_points": data_points
    }
    client.publish(topic, json.dumps(payload), qos=0)
```

---

### 3.2 设备状态消息

**Topic**: `devices/{device_id}/status`

**频率**: 状态变更时上报

**QoS**: 1（至少一次送达）

**消息结构**:
```json
{
  "device_id": "A7B3-9C2D-E5F6",
  "status": "online",
  "center_frequency": 1.2,
  "metadata": {
    "firmware_version": "v1.2.3",
    "hardware_version": "v2.0"
  },
  "timestamp": "2025-11-12T10:30:45.123Z"
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | String | ✓ | 设备唯一标识符 |
| `status` | Enum | ✓ | 设备状态: `online`, `offline`, `error` |
| `center_frequency` | Float | ✓ | 中心频率（GHz） |
| `metadata` | Object | ✗ | 附加元数据 |
| `timestamp` | String (ISO 8601) | ✓ | 时间戳 |

**示例Python代码**:
```python
def publish_status(client, device_id, status):
    topic = f"devices/{device_id}/status"
    payload = {
        "device_id": device_id,
        "status": status,
        "center_frequency": 1.2,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    client.publish(topic, json.dumps(payload), qos=1)
```

---

### 3.3 心跳消息

**Topic**: `devices/{device_id}/heartbeat`

**频率**: 每30秒

**QoS**: 0

**消息结构**:
```json
{
  "device_id": "A7B3-9C2D-E5F6",
  "timestamp": "2025-11-12T10:30:45.123Z"
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `device_id` | String | ✓ | 设备唯一标识符 |
| `timestamp` | String (ISO 8601) | ✓ | 时间戳 |

---

## 4. 接入指南

### 4.1 设备接入步骤

1. **连接Broker**
   ```python
   import paho.mqtt.client as mqtt

   client = mqtt.Client(client_id=f"device_{device_id}")
   client.username_pw_set(username, password)  # 如果需要认证
   client.connect(broker_address, port, 60)
   ```

2. **发送状态上线**
   ```python
   publish_status(client, device_id, "online")
   ```

3. **定时发送频谱数据**
   ```python
   while True:
       data_points = collect_spectrum_data()
       publish_spectrum_data(client, device_id, peak_freq, center_freq, data_points)
       time.sleep(1)
   ```

4. **发送心跳**
   ```python
   def send_heartbeat():
       topic = f"devices/{device_id}/heartbeat"
       payload = {
           "device_id": device_id,
           "timestamp": datetime.utcnow().isoformat() + "Z"
       }
       client.publish(topic, json.dumps(payload), qos=0)

   # 每30秒执行一次
   ```

### 4.2 完整示例代码

参见项目仓库中的 `examples/device_simulator.py`

---

## 5. 测试工具

### 5.1 使用mosquitto_pub测试

**发送频谱数据**:
```bash
mosquitto_pub -h localhost -t "devices/TEST-DEVICE-01/spectrum" -m '{
  "device_id": "TEST-DEVICE-01",
  "device_name": "Test Scanner",
  "peak_frequency": 2.45,
  "center_frequency": 1.2,
  "timestamp": "2025-11-12T10:30:45Z",
  "data_points": [[0, 2.45], [0.2, 2.43], [0.4, 2.48]]
}'
```

**发送状态消息**:
```bash
mosquitto_pub -h localhost -t "devices/TEST-DEVICE-01/status" -m '{
  "device_id": "TEST-DEVICE-01",
  "status": "online",
  "center_frequency": 1.2,
  "timestamp": "2025-11-12T10:30:45Z"
}' -q 1
```

### 5.2 使用MQTTX客户端

推荐使用图形化工具 [MQTTX](https://mqttx.app/) 进行测试和调试。

---

## 6. 常见问题

### Q1: 如何确定device_id？
**A**: `device_id` 应该是设备的唯一标识符，可以是设备MAC地址、序列号或UUID。

### Q2: 频谱数据data_points数组的大小？
**A**: 建议每次上报60-100个数据点（代表1分钟内的采样），过多会增加带宽占用。

### Q3: 连接失败怎么办？
**A**:
1. 检查MQTT Broker是否启动
2. 验证网络连接
3. 确认用户名密码（如果配置）
4. 查看防火墙设置

### Q4: 如何处理设备离线？
**A**: 平台会根据心跳超时（90秒无心跳）自动标记设备为离线状态。

### Q5: 支持SSL/TLS加密吗？
**A**: 当前版本支持明文传输。如需加密，请配置Broker的TLS端口（通常为8883）并更新`.env`配置。

---

## 7. 协议版本

- **当前版本**: v1.0
- **发布日期**: 2025-11-12
- **维护者**: 四川物联网平台团队

---

## 8. 更新记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-11-12 | 初始版本发布 |

---

## 9. 联系方式

如有问题或建议，请联系：
- **GitHub Issues**: https://github.com/your-org/sichuan-iot-platform/issues
- **Email**: support@example.com
