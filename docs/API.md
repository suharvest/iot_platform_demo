# API接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: v0.1.0
- **Content-Type**: `application/json`

## 认证

当前版本暂不需要认证。后续版本将添加Token认证机制。

---

## 设备管理

### 获取设备列表

获取所有已注册设备的列表。

**请求**

```http
GET /api/devices?skip=0&limit=100
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| skip | integer | 否 | 0 | 跳过的记录数 |
| limit | integer | 否 | 100 | 返回的最大记录数 |

**响应**

```json
{
  "total": 1,
  "devices": [
    {
      "id": 1,
      "name": "RF-Scanner-01",
      "device_id": "A7B3-9C2D-E5F6",
      "status": "online",
      "center_frequency": 1.2,
      "last_update": "2025-11-12T10:30:45.123456",
      "created_at": "2025-11-12T09:00:00.000000"
    }
  ]
}
```

**状态码**

- `200 OK`: 成功

---

### 获取设备详情

根据设备ID获取单个设备的详细信息。

**请求**

```http
GET /api/devices/{device_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| device_id | string | 是 | 设备唯一标识符 |

**响应**

```json
{
  "id": 1,
  "name": "RF-Scanner-01",
  "device_id": "A7B3-9C2D-E5F6",
  "status": "online",
  "center_frequency": 1.2,
  "last_update": "2025-11-12T10:30:45.123456",
  "created_at": "2025-11-12T09:00:00.000000"
}
```

**状态码**

- `200 OK`: 成功
- `404 Not Found`: 设备不存在

---

### 创建设备

手动创建新设备记录。

**请求**

```http
POST /api/devices
Content-Type: application/json

{
  "name": "RF-Scanner-02",
  "device_id": "B8C4-0D3E-F7G8",
  "center_frequency": 1.5
}
```

**请求体**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 设备名称 |
| device_id | string | 是 | 设备唯一标识符 |
| center_frequency | float | 否 | 中心频率(GHz) |

**响应**

```json
{
  "id": 2,
  "name": "RF-Scanner-02",
  "device_id": "B8C4-0D3E-F7G8",
  "status": "offline",
  "center_frequency": 1.5,
  "last_update": null,
  "created_at": "2025-11-12T10:35:00.000000"
}
```

**状态码**

- `200 OK`: 创建成功
- `400 Bad Request`: 设备ID已存在或参数错误

---

### 更新设备

更新设备信息。

**请求**

```http
PUT /api/devices/{device_id}
Content-Type: application/json

{
  "name": "RF-Scanner-02-Updated",
  "status": "online",
  "center_frequency": 1.8
}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| device_id | string | 是 | 设备唯一标识符 |

**请求体**

所有字段都是可选的，只更新提供的字段。

| 字段 | 类型 | 描述 |
|------|------|------|
| name | string | 设备名称 |
| status | string | 设备状态 (online/offline/error) |
| center_frequency | float | 中心频率(GHz) |

**响应**

```json
{
  "id": 2,
  "name": "RF-Scanner-02-Updated",
  "device_id": "B8C4-0D3E-F7G8",
  "status": "online",
  "center_frequency": 1.8,
  "last_update": "2025-11-12T10:40:00.000000",
  "created_at": "2025-11-12T10:35:00.000000"
}
```

**状态码**

- `200 OK`: 更新成功
- `404 Not Found`: 设备不存在

---

### 删除设备

删除设备记录及其关联的所有频谱数据。

**请求**

```http
DELETE /api/devices/{device_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| device_id | string | 是 | 设备唯一标识符 |

**响应**

```json
{
  "message": "设备已删除"
}
```

**状态码**

- `200 OK`: 删除成功
- `404 Not Found`: 设备不存在

---

## 频谱数据

### 获取最新频谱数据

获取指定设备的最新频谱数据。

**请求**

```http
GET /api/spectrum/latest?device_id=A7B3-9C2D-E5F6
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| device_id | string | 是 | 设备唯一标识符 |

**响应**

```json
{
  "id": 123,
  "device_id": "A7B3-9C2D-E5F6",
  "peak_frequency": 2.45,
  "frequency_change": 0.01,
  "data_points": [
    [0.0, 2.45],
    [0.2, 2.43],
    [0.4, 2.48],
    ...
  ],
  "timestamp": "2025-11-12T10:30:45.123456"
}
```

**状态码**

- `200 OK`: 成功
- `404 Not Found`: 暂无频谱数据

---

### 获取历史频谱数据

获取指定设备的历史频谱数据（分页）。

**请求**

```http
GET /api/spectrum/history?device_id=A7B3-9C2D-E5F6&page=1&page_size=50
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| device_id | string | 是 | - | 设备唯一标识符 |
| page | integer | 否 | 1 | 页码（从1开始） |
| page_size | integer | 否 | 50 | 每页记录数 |

**响应**

```json
{
  "total": 1234,
  "page": 1,
  "page_size": 50,
  "data": [
    {
      "id": 123,
      "device_id": "A7B3-9C2D-E5F6",
      "peak_frequency": 2.45,
      "frequency_change": 0.01,
      "data_json": "[[0.0, 2.45], [0.2, 2.43], ...]",
      "timestamp": "2025-11-12T10:30:45.123456"
    },
    ...
  ]
}
```

**状态码**

- `200 OK`: 成功

---

## WebSocket

### 实时数据推送

通过WebSocket接收实时频谱数据推送。

**连接**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('WebSocket已连接');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};
```

**接收的消息格式**

```json
{
  "type": "spectrum",
  "data": {
    "device_id": "A7B3-9C2D-E5F6",
    "device_name": "RF-Scanner-01",
    "peak_frequency": 2.45,
    "center_frequency": 1.2,
    "timestamp": "2025-11-12T10:30:45Z",
    "data_points": [[0.0, 2.45], [0.2, 2.43], ...]
  }
}
```

**消息类型**

| type | 描述 |
|------|------|
| spectrum | 频谱数据更新 |
| status | 设备状态变更（待实现） |

---

## 健康检查

### 服务健康状态

检查服务是否正常运行。

**请求**

```http
GET /health
```

**响应**

```json
{
  "status": "ok",
  "service": "sichuan-iot-platform"
}
```

**状态码**

- `200 OK`: 服务正常

---

## 错误响应

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

### HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用示例

### Python

```python
import requests

# 获取设备列表
response = requests.get('http://localhost:8000/api/devices')
devices = response.json()

# 获取最新频谱数据
response = requests.get(
    'http://localhost:8000/api/spectrum/latest',
    params={'device_id': 'A7B3-9C2D-E5F6'}
)
spectrum = response.json()

# 创建设备
new_device = {
    'name': 'RF-Scanner-03',
    'device_id': 'C9D5-1E4F-G8H9',
    'center_frequency': 2.0
}
response = requests.post(
    'http://localhost:8000/api/devices',
    json=new_device
)
```

### JavaScript (fetch)

```javascript
// 获取设备列表
fetch('http://localhost:8000/api/devices')
  .then(res => res.json())
  .then(data => console.log(data));

// 获取最新频谱数据
fetch('http://localhost:8000/api/spectrum/latest?device_id=A7B3-9C2D-E5F6')
  .then(res => res.json())
  .then(data => console.log(data));

// 创建设备
fetch('http://localhost:8000/api/devices', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'RF-Scanner-03',
    device_id: 'C9D5-1E4F-G8H9',
    center_frequency: 2.0
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### curl

```bash
# 获取设备列表
curl http://localhost:8000/api/devices

# 获取最新频谱数据
curl "http://localhost:8000/api/spectrum/latest?device_id=A7B3-9C2D-E5F6"

# 创建设备
curl -X POST http://localhost:8000/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RF-Scanner-03",
    "device_id": "C9D5-1E4F-G8H9",
    "center_frequency": 2.0
  }'

# 更新设备
curl -X PUT http://localhost:8000/api/devices/A7B3-9C2D-E5F6 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "offline"
  }'

# 删除设备
curl -X DELETE http://localhost:8000/api/devices/A7B3-9C2D-E5F6
```

---

## 交互式文档

启动服务后，访问以下地址查看交互式API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

在Swagger UI中可以直接测试所有API接口。
