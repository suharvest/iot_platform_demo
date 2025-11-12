# 四川物联网平台 - 产线设备实时监控系统

基于MQTT的产线设备频谱分析实时监控系统，实现设备数据采集、存储、可视化展示。

![Platform](https://img.shields.io/badge/Platform-IoT-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-orange)
![Vue](https://img.shields.io/badge/Vue-3.3-brightgreen)

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API文档](#api文档)
- [MQTT协议](#mqtt协议)
- [配置说明](#配置说明)
- [开发指南](#开发指南)

## ✨ 功能特性

- ✅ **实时数据采集**: 通过MQTT订阅设备频谱数据
- ✅ **数据持久化**: SQLite数据库存储设备信息和历史数据
- ✅ **实时推送**: WebSocket推送最新数据到前端
- ✅ **可视化展示**: ECharts绘制频谱趋势图
- ✅ **设备管理**: RESTful API管理设备信息
- ✅ **轻量部署**: 单脚本启动，无需容器化
- ✅ **灵活配置**: 支持外部MQTT Broker配置

## 🏗️ 系统架构

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│ 设备(频谱仪) │──MQTT──▶│ MQTT Broker  │──订阅──▶│  后端服务   │
│             │       │(Mosquitto)   │       │  (FastAPI)  │
└─────────────┘       └──────────────┘       └──────┬──────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │   SQLite DB     │
                                           │ (时序数据存储)   │
                                           └─────────────────┘
                                                    │
                                                    │ WebSocket
                                                    ▼
                                           ┌─────────────────┐
                                           │  前端页面       │
                                           │  (Vue 3)       │
                                           └─────────────────┘
```

## 🚀 快速开始

### 前置要求

- **Python 3.11+**
- **uv** (Python包管理工具)
- **Mosquitto** (MQTT Broker，可选)

### 安装uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 安装Mosquitto（可选）

如果需要使用本地MQTT Broker：

```bash
# macOS
brew install mosquitto

# Ubuntu/Debian
sudo apt-get install mosquitto

# 启动Mosquitto
mosquitto -d
```

### 克隆项目

```bash
git clone <repository-url>
cd sichuan_iot_platform
```

### 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置MQTT Broker地址
vim .env
```

### 启动系统

```bash
./start.sh
```

启动成功后，浏览器会自动打开 `http://localhost:8000`

### 模拟设备数据

在另一个终端运行设备模拟器：

```bash
uv run python device_simulator.py
```

## 📁 项目结构

```
sichuan_iot_platform/
├── backend/                    # 后端代码
│   ├── __init__.py
│   ├── main.py                # FastAPI主应用
│   ├── config.py              # 配置管理
│   ├── database.py            # 数据库配置
│   ├── models.py              # 数据模型
│   ├── schemas.py             # Pydantic模型
│   ├── crud.py                # 数据库操作
│   └── mqtt_client.py         # MQTT客户端
├── frontend/                   # 前端代码
│   └── index.html             # 单页面应用
├── data/                       # 数据存储
│   └── spectrum.db            # SQLite数据库
├── docs/                       # 文档
│   ├── MQTT_PROTOCOL.md       # MQTT协议规约
│   └── API.md                 # API文档
├── pyproject.toml              # uv项目配置
├── .env                        # 环境变量配置
├── .env.example                # 环境变量模板
├── start.sh                    # 启动脚本
├── stop.sh                     # 停止脚本
├── device_simulator.py         # 设备模拟器
└── README.md                   # 本文件
```

## 📖 API文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | 前端页面 |
| GET | `/api/devices` | 获取设备列表 |
| GET | `/api/devices/{device_id}` | 获取设备详情 |
| POST | `/api/devices` | 创建设备 |
| PUT | `/api/devices/{device_id}` | 更新设备 |
| DELETE | `/api/devices/{device_id}` | 删除设备 |
| GET | `/api/spectrum/latest` | 获取最新频谱数据 |
| GET | `/api/spectrum/history` | 获取历史频谱数据（分页） |
| WS | `/ws` | WebSocket实时推送 |

详细API文档见 [docs/API.md](docs/API.md)

## 📡 MQTT协议

### Topic结构

```
devices/{device_id}/spectrum      # 频谱数据
devices/{device_id}/status        # 设备状态
devices/{device_id}/heartbeat     # 心跳
```

### 消息格式

**频谱数据消息**:
```json
{
  "device_id": "A7B3-9C2D-E5F6",
  "device_name": "RF-Scanner-01",
  "peak_frequency": 2.45,
  "center_frequency": 1.2,
  "timestamp": "2025-11-12T10:30:45Z",
  "data_points": [[0.0, 2.45], [0.2, 2.43], ...]
}
```

完整MQTT协议规约见 [docs/MQTT_PROTOCOL.md](docs/MQTT_PROTOCOL.md)

## ⚙️ 配置说明

### 环境变量 (.env)

```bash
# MQTT配置
MQTT_BROKER=localhost           # MQTT Broker地址
MQTT_PORT=1883                  # MQTT端口
MQTT_USERNAME=                  # MQTT用户名（可选）
MQTT_PASSWORD=                  # MQTT密码（可选）
MQTT_TOPIC_PREFIX=devices       # Topic前缀

# 数据库配置
DATABASE_URL=sqlite:///./data/spectrum.db

# 后端服务配置
API_HOST=0.0.0.0
API_PORT=8000

# 启动配置
START_LOCAL_MQTT=false          # 是否启动本地MQTT
```

### 使用外部MQTT Broker

1. 修改 `.env` 文件：
   ```bash
   MQTT_BROKER=your-broker-address.com
   MQTT_PORT=1883
   MQTT_USERNAME=your-username
   MQTT_PASSWORD=your-password
   START_LOCAL_MQTT=false
   ```

2. 重启服务：
   ```bash
   ./stop.sh
   ./start.sh
   ```

## 🛠️ 开发指南

### 安装开发依赖

```bash
uv sync --dev
```

### 运行测试

```bash
uv run pytest
```

### 数据库迁移

```bash
# 初始化数据库
uv run python -c "from backend.database import init_db; init_db()"

# 清空数据库
rm data/spectrum.db
```

### 代码风格

项目使用：
- **Python**: PEP 8
- **JavaScript**: ES6+
- **CSS**: BEM命名规范

### 添加新功能

1. 修改数据模型 (`backend/models.py`, `backend/schemas.py`)
2. 更新CRUD操作 (`backend/crud.py`)
3. 添加API路由 (`backend/main.py`)
4. 更新前端页面 (`frontend/index.html`)

## 🐛 故障排查

### 服务无法启动

1. 检查端口是否被占用：
   ```bash
   lsof -i :8000
   ```

2. 查看日志：
   ```bash
   tail -f logs/backend.log
   ```

### MQTT连接失败

1. 检查Mosquitto是否运行：
   ```bash
   ps aux | grep mosquitto
   ```

2. 测试MQTT连接：
   ```bash
   mosquitto_sub -h localhost -t "devices/#" -v
   ```

### 前端无法连接WebSocket

1. 检查浏览器控制台错误
2. 确认后端服务正常运行
3. 检查防火墙设置

## 📝 更新日志

### v0.1.0 (2025-11-12)

- ✨ 初始版本发布
- ✅ 实现MQTT数据采集
- ✅ 实现实时频谱可视化
- ✅ 完成设备管理API
- ✅ 编写MQTT协议规约文档

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 License

MIT License

## 👥 联系方式

- **项目地址**: https://github.com/your-org/sichuan-iot-platform
- **问题反馈**: https://github.com/your-org/sichuan-iot-platform/issues
