# 四川物联网平台 V2.0 - 设备管理系统

基于MQTT协议的示波器设备管理系统，支持实时监控、3D可视化和设备控制。

## 📚 目录

- [快速开始](#快速开始)
- [主要功能](#主要功能)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [详细安装](#详细安装)
- [使用指南](#使用指南)
- [常见问题](#常见问题)
- [开发文档](#开发文档)

## 🚀 快速开始

### 第一步：启动 MQTT Broker(如果已有，则不需要)

**macOS 用户**：
```bash
brew install mosquitto
brew services start mosquitto
```

**Linux 用户**：
```bash
sudo apt-get install mosquitto
sudo systemctl start mosquitto
```

**Docker 用户**：
```bash
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto
```

### 第二步：一键启动所有服务

```bash
./start_all.sh
```

就这么简单！🎉

脚本会自动：
- ✅ 检查并安装后端依赖（uv）
- ✅ 检查并安装前端依赖（npm）
- ✅ 启动后端服务（FastAPI）
- ✅ 启动前端服务（Vue + Vite）
- ✅ 3秒后自动打开浏览器

### 第三步：访问系统

浏览器会自动打开 http://localhost:5173

你也可以手动访问：
- 🌐 **前端界面**：
  - 本机：http://localhost:5173
  - 局域网：http://你的IP:5173 （启动脚本会自动显示）
- 📡 **后端API**：
  - 本机：http://localhost:9099
  - 局域网：http://你的IP:9099
- 📚 **API文档**：http://localhost:9099/docs

> **💡 提示**：服务已配置为监听 `0.0.0.0`，支持局域网内其他设备访问。启动后会自动显示局域网访问地址。

### （可选）运行设备模拟器

在**新的终端窗口**运行：

```bash
uv run device_simulator.py
```

模拟器会创建 5 个虚拟设备：
- 3 个示波器（OSC001, OSC002, OSC003）
- 2 个物联网设备（IOT001, IOT002）

### 停止服务

```bash
./stop_all.sh
```

### 查看日志

```bash
# 后端日志
tail -f logs/backend.log

# 前端日志
tail -f logs/frontend.log
```

## 🎯 主要功能

### 后端功能
- ✅ 基于mqtt_protocal.md的完整MQTT协议支持
- ✅ FastAPI RESTful API
- ✅ SQLite数据库存储（全新数据模型）
- ✅ 设备自动发现和注册
- ✅ 实时测量数据采集（频率、Vpp、Vmax）
- ✅ 设备控制命令（复位、自动配置）
- ✅ 位置追踪器集成
- ✅ 3D模型文件服务
- ✅ WebSocket实时推送

### 前端功能
- ✅ Vue 3 + Vite现代化架构
- ✅ 设备列表和详情页面
- ✅ 实时趋势图表（ECharts）
- ✅ 3D模型查看器（Three.js）
  - 右键旋转
  - 滚轮缩放
  - 科技感灯光效果
- ✅ MQTT配置管理
- ✅ 位置配置器
- ✅ 深色科技风UI
- ✅ 中文界面

## 📋 系统架构

```
┌─────────────┐         MQTT         ┌──────────────┐
│   设备      │ ◄──────────────────► │ MQTT Broker  │
│ (示波器)    │  device/info         │ (Mosquitto)  │
│             │  oscilloscope/*      │              │
└─────────────┘                      └──────┬───────┘
                                            │
                                            │ Subscribe
                                            ▼
                                     ┌──────────────┐
                                     │   后端       │
                                     │  FastAPI     │
                                     │  + SQLite    │
                                     └──────┬───────┘
                                            │
                                            │ HTTP/WebSocket
                                            ▼
                                     ┌──────────────┐
                                     │   前端       │
                                     │  Vue 3       │
                                     │  + Three.js  │
                                     └──────────────┘
```

## 🛠️ 技术栈

### 后端
- **Python**: 3.11+
- **框架**: FastAPI 0.109+
- **数据库**: SQLite + SQLAlchemy 2.0+
- **MQTT**: paho-mqtt 2.0+
- **包管理**: uv

### 前端
- **框架**: Vue 3.4+ (Composition API)
- **构建**: Vite 5.0+
- **路由**: Vue Router 4.2+
- **3D渲染**: Three.js 0.160+
- **图表**: ECharts 5.4+
- **HTTP**: Axios

## 📦 项目结构

```
sichuan_iot_platform/
├── backend/                    # 后端代码
│   ├── main.py                # FastAPI应用入口
│   ├── models.py              # 数据库模型
│   ├── schemas.py             # Pydantic模型
│   ├── crud.py                # 数据库操作
│   ├── mqtt_client.py         # MQTT客户端
│   ├── database.py            # 数据库配置
│   ├── config.py              # 配置管理
│   └── static/
│       └── models/            # 3D模型文件(.glb)
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 复用组件
│   │   ├── router/            # 路由配置
│   │   ├── utils/             # 工具函数
│   │   └── assets/            # 静态资源
│   ├── public/
│   │   └── models/            # 3D模型文件（开发）
│   ├── package.json
│   └── vite.config.js
├── mqtt_protocal.md           # MQTT协议文档
├── .env                       # 环境配置
└── README_V2.md               # 本文档
```

## 🚀 快速开始

### 方法1：一键启动（推荐）⭐

```bash
# 1. 启动MQTT Broker（首次运行需要）
brew services start mosquitto  # macOS
# 或
sudo systemctl start mosquitto  # Linux
# 或
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto  # Docker

# 2. 一键启动所有服务
./start_all.sh
```

脚本会自动：
- ✅ 检查并安装所有依赖
- ✅ 在后台启动后端服务
- ✅ 在后台启动前端服务
- ✅ 自动打开浏览器
- ✅ 生成日志文件方便调试

**停止所有服务**：
```bash
./stop_all.sh
```

**查看日志**：
```bash
tail -f backend.log   # 查看后端日志
tail -f frontend.log  # 查看前端日志
```

访问地址：
- 前端：http://localhost:5173
- 后端API：http://localhost:9099
- API文档：http://localhost:9099/docs

---

### 方法2：手动启动

#### 1. 环境准备

**系统要求**：
- Python 3.11+
- Node.js 18+
- MQTT Broker（如Mosquitto）

**安装uv（Python包管理器）**：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. 后端启动

```bash
# 1. 进入项目根目录
cd /Users/harvest/project/sichuan_iot_platform

# 2. 安装Python依赖
uv sync

# 3. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，配置MQTT Broker地址等

# 4. 启动后端
uv run python -m backend.main
```

后端将运行在 http://localhost:9099

**API文档**：http://localhost:9099/docs

#### 3. 前端启动

在**新的终端窗口**中：

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:5173

#### 4. 启动MQTT Broker（如果需要）

使用Mosquitto：
```bash
# macOS
brew install mosquitto
brew services start mosquitto

# Linux
sudo apt-get install mosquitto
sudo systemctl start mosquitto

# 或使用Docker
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto
```

## 📝 配置说明

### 后端配置 (.env)

```env
# 数据库
DATABASE_URL=sqlite:///./data/devices.db

# MQTT配置
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=device_manager
MQTT_PASSWORD=your_password

# API配置
API_HOST=0.0.0.0
API_PORT=8000
```

### 3D模型文件

**放置位置**：
- `backend/static/models/` （生产环境）
- `frontend/public/models/` （开发环境，可选）

**命名规则**：
- 文件名必须与设备的 `model` 字段完全匹配
- 例如：设备型号 `ZDS21104` → 模型文件 `ZDS21104.glb`

**模型要求**：
- 格式：GLB（二进制glTF）
- 多边形数：< 50,000
- 文件大小：< 5MB
- 贴图分辨率：≤ 2048×2048

**如何创建模型**：
1. 使用Blender等3D软件建模
2. 导出为glTF 2.0格式
3. 选择"GLB"（单文件）选项
4. 优化模型（减少面数、压缩贴图）

## 📡 MQTT协议说明

系统实现了完整的mqtt_protocal.md协议。

### 主题结构

**设备 → 平台**：
- `device/info` - 设备信息（每5秒）
- `oscilloscope/set_rsp` - 控制命令响应
- `oscilloscope/query_rsp` - 查询结果响应

**平台 → 设备**：
- `oscilloscope/set` - 控制命令（reset、autosetup）
- `oscilloscope/query` - 查询请求（freq_meas、vpp_meas、vmax_meas）

**位置主题**（独立）：
- `location/*` - 用户自定义位置主题

### 消息格式示例

**设备信息**：
```json
{
  "task": "dev_info",
  "type": "oscilloscope",
  "manufacturer": "ZLG",
  "model": "ZDS21104",
  "sn": "OSC001"
}
```

**查询频率**：
```json
// 发送
{
  "task": "freq_meas",
  "channel": 1
}

// 响应
{
  "task": "freq_meas",
  "channel": 1,
  "value": "999.99",
  "unit": "Hz"
}
```

## 🔧 开发指南

### 后端开发

**添加新的API端点**：
1. 在 `backend/schemas.py` 定义请求/响应模型
2. 在 `backend/crud.py` 添加数据库操作
3. 在 `backend/main.py` 添加路由

**数据库迁移**：
```bash
# 当前使用 SQLAlchemy 的 create_all()
# 如需更高级的迁移，可集成 Alembic
```

### 前端开发

**添加新页面**：
1. 在 `frontend/src/views/` 创建Vue组件
2. 在 `frontend/src/router/index.js` 添加路由

**调用API**：
```javascript
import { deviceApi } from '@/utils/api'

// 获取设备列表
const devices = await deviceApi.getDevices()

// 执行测量
await deviceApi.measure(sn, {
  task: 'freq_meas',
  channel: 1
})
```

### 设备模拟器

使用 `device_simulator.py` 模拟设备发送MQTT消息：

```bash
# 需要更新模拟器以支持新协议
uv run python device_simulator.py
```

**模拟器需实现**：
- 每5秒发送 `device/info`
- 监听 `oscilloscope/set` 并响应
- 监听 `oscilloscope/query` 并响应

## 🎨 UI设计说明

### 深色科技风主题

**颜色方案**：
- 主背景：#0a0e27（深蓝黑）
- 次背景：#151932
- 主题色：#3b82f6（科技蓝）
- 成功色：#10b981（青绿）
- 在线状态：绿色发光点
- 离线状态：灰色

**视觉特效**：
- 毛玻璃效果（backdrop-filter: blur）
- 边框发光（box-shadow）
- 渐变背景
- 平滑过渡动画

### 页面布局

**设备列表页**：
- 顶部：导航栏 + Logo
- MQTT配置：可折叠面板
- 设备表格：悬停高亮、状态指示

**设备详情页**：
- 返回按钮 + 标题
- 设备信息卡片
- 实时趋势图表（Tab切换）
- 操作按钮（自动配置、复位、3D视图）

## 🐛 故障排查

### 后端无法启动

1. 检查Python版本：`python --version`
2. 检查依赖安装：`uv sync`
3. 检查MQTT Broker是否运行：`telnet localhost 1883`
4. 查看日志输出

### 前端无法连接后端

1. 确认后端已启动（http://localhost:9099/health）
2. 检查Vite代理配置（vite.config.js）
3. 查看浏览器控制台Network面板

### 3D模型不显示

1. 确认模型文件存在：`ls backend/static/models/`
2. 文件名是否与设备model字段匹配
3. 浏览器是否支持WebGL 2.0
4. 检查浏览器控制台错误

### 设备不在线

1. 确认设备已连接到MQTT Broker
2. 检查设备是否发送 `device/info` 消息
3. 查看后端日志是否收到消息
4. 检查数据库中设备状态

## 📊 性能优化

### 后端
- 数据库查询添加索引（已实现）
- MQTT消息批量处理
- WebSocket连接池管理

### 前端
- 图表数据节流（避免过度更新）
- 3D模型懒加载
- 路由懒加载
- 静态资源CDN（生产环境）

## 🔒 安全考虑

- MQTT认证（用户名/密码）
- API接口可添加JWT认证
- 避免SQL注入（已使用ORM）
- XSS防护（Vue自动转义）
- HTTPS部署（生产环境）

## ❓ 常见问题

### 1. MQTT Broker 未运行

**错误提示**：`⚠️ MQTT Broker未运行！`

**解决方法**：
```bash
# macOS
brew services start mosquitto

# Linux
sudo systemctl start mosquitto

# 检查是否运行
telnet localhost 1883
```

### 2. 端口被占用

**错误提示**：`Address already in use`

**解决方法**：
```bash
# 停止所有服务
./stop_all.sh

# 或手动查找并结束进程
lsof -ti:8000 | xargs kill  # 后端端口
lsof -ti:5173 | xargs kill  # 前端端口
```

### 3. 前端或后端无法访问

**检查服务是否运行**：
```bash
# 检查后端
curl http://localhost:9099/health

# 检查进程
ps aux | grep "backend.main"
ps aux | grep "vite"
```

**查看日志**：
```bash
tail -n 50 logs/backend.log
tail -n 50 logs/frontend.log
```

### 4. 3D 模型不显示

**原因**：模型文件不存在

**解决方法**：
将 `.glb` 格式的 3D 模型文件放入：
```
backend/static/models/
```

文件名必须与设备型号完全匹配，例如：
- `ZDS21104.glb`
- `ZDS21034.glb`
- `TBS2000.glb`

### 5. 图表时间显示错误

图表默认显示UTC时间并自动转换为本地时间。时间范围可在前端代码中配置：

```javascript
// frontend/src/views/DeviceDetail.vue
const CHART_TIME_RANGE_MINUTES = 1  // 修改显示的分钟数
```

### 6. 实时数据不更新

确保：
1. MQTT Broker正在运行
2. 设备模拟器正在运行
3. 后端成功连接到MQTT Broker
4. 检查后端日志查看是否接收到消息

## 📈 未来计划

- [ ] 用户认证和权限管理
- [ ] 设备分组和标签
- [ ] 历史数据导出（CSV、Excel）
- [ ] 告警规则配置
- [ ] 多设备3D场景总览
- [ ] 移动端适配
- [ ] Docker部署方案
- [ ] Kubernetes配置

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 License

MIT License

## 👥 联系方式

- 项目地址：https://github.com/your-repo/sichuan_iot_platform
- 问题反馈：https://github.com/your-repo/sichuan_iot_platform/issues

---

**版本**: V2.0.0
**最后更新**: 2025-11-19
**作者**: Claude Code + Harvest
