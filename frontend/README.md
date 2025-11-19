# 四川物联网平台 - 前端项目

基于 Vue 3 + Vite + Three.js 开发的设备管理前端系统。

## 功能特性

- ✅ 设备列表管理
- ✅ 设备详情展示
- ✅ 实时趋势监控（ECharts）
- ✅ MQTT配置管理
- ✅ 设备位置配置
- ✅ 3D模型查看器（Three.js）
- ✅ 设备控制（复位、自动配置）
- ✅ 实时测量（频率、Vpp、Vmax）
- ✅ 深色科技风UI

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 5.x
- **路由**: Vue Router 4.x
- **3D渲染**: Three.js 0.160+
- **图表**: ECharts 5.4+
- **HTTP客户端**: Axios
- **样式**: 原生CSS（深色科技风）

## 项目结构

```
frontend/
├── public/              # 静态资源
│   └── models/          # 3D模型文件(.glb)
├── src/
│   ├── assets/
│   │   └── styles/
│   │       └── main.css    # 全局样式
│   ├── components/
│   │   ├── LocationPicker.vue    # 位置配置器
│   │   └── Model3DViewer.vue     # 3D模型查看器
│   ├── router/
│   │   └── index.js              # 路由配置
│   ├── utils/
│   │   └── api.js                # API封装
│   ├── views/
│   │   ├── DeviceList.vue        # 设备列表页
│   │   └── DeviceDetail.vue      # 设备详情页
│   ├── App.vue
│   └── main.js
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录

### 4. 预览生产构建

```bash
npm run preview
```

## 配置说明

### 后端API代理

`vite.config.js` 中已配置代理：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

如果后端运行在不同端口，请修改 `target`。

### 3D模型文件

将 `.glb` 格式的3D模型文件放置在：
- 开发环境：`public/models/`
- 生产环境：后端 `backend/static/models/`

**模型命名规则**：
- 文件名必须与设备的 `model` 字段完全一致
- 例如：设备型号为 `ZDS21104`，则模型文件为 `ZDS21104.glb`

**模型要求**：
- 格式：GLB（二进制glTF）
- 多边形数：< 50,000
- 文件大小：< 5MB
- 贴图分辨率：≤ 2048×2048

## 页面功能说明

### 设备列表页 (`/devices`)

- 展示所有设备的状态和基本信息
- MQTT配置面板（可折叠）
- 支持刷新设备列表
- 点击"详情"跳转到设备详情页

### 设备详情页 (`/devices/:sn`)

**设备信息卡片**：
- 显示设备名称、型号、序列号、位置、状态
- 点击位置可配置位置主题
- 「自动配置」按钮：发送autosetup命令
- 「复位」按钮：发送reset命令
- 「3D视图」按钮：仅当模型文件存在时显示

**实时趋势监控**：
- 频率/幅度Tab切换
- 通道选择（1-4）
- 实时读取开关（开启后每2秒自动查询）
- ECharts图表展示最近24小时数据
- 显示当前测量值和变化百分比

## 组件说明

### LocationPicker 组件

用于配置设备位置的模态框组件。

**功能**：
- 输入位置MQTT主题
- 实时预览位置值
- 保存位置配置

### Model3DViewer 组件

基于Three.js的3D模型查看器。

**功能**：
- 加载.glb格式的3D模型
- 右键拖拽旋转
- 滚轮缩放
- 科技感灯光效果
- 网格地面
- 自动居中和缩放

**交互**：
- 右键：旋转模型
- 滚轮：缩放
- 禁用平移

## API接口

所有API请求通过 `src/utils/api.js` 封装。

**设备API**：
- `GET /api/devices` - 获取设备列表
- `GET /api/devices/:sn` - 获取设备详情
- `POST /api/devices/:sn/reset` - 复位设备
- `POST /api/devices/:sn/autosetup` - 自动配置
- `POST /api/devices/:sn/measure` - 执行测量
- `GET /api/devices/:sn/measurements` - 获取历史数据
- `PUT /api/devices/:sn/location` - 更新位置配置

**模型API**：
- `GET /api/models` - 获取可用模型列表
- `GET /api/models/:name.glb` - 下载模型文件

**MQTT API**：
- `GET /api/mqtt/config` - 获取MQTT配置
- `PUT /api/mqtt/config` - 更新MQTT配置

## 样式系统

### 颜色变量

```css
--bg-primary: #0a0e27        /* 主背景 */
--bg-secondary: #151932      /* 次背景 */
--bg-card: rgba(21, 25, 50, 0.6)  /* 卡片背景 */

--color-primary: #3b82f6     /* 主题色 */
--color-success: #10b981     /* 成功/在线 */
--color-danger: #ef4444      /* 危险/离线 */

--text-primary: #e5e7eb      /* 主文字 */
--text-secondary: #9ca3af    /* 次文字 */
```

### 常用类

- `.btn` - 按钮基础样式
- `.btn-primary` - 主按钮
- `.btn-secondary` - 次按钮
- `.card` - 卡片容器
- `.status-indicator` - 状态指示器
- `.modal-overlay` - 模态框遮罩
- `.modal` - 模态框

## 开发注意事项

1. **Three.js资源清理**：
   - 组件销毁时必须调用 `renderer.dispose()` 和 `controls.dispose()`
   - 移除DOM节点：`viewerContainer.value.removeChild(renderer.domElement)`

2. **ECharts内存管理**：
   - 组件销毁时调用 `chart.dispose()`
   - 窗口resize时调用 `chart.resize()`

3. **实时查询**：
   - 使用 `setInterval` 时务必在组件销毁时 `clearInterval`
   - 避免多次开启导致重复请求

4. **MQTT消息**：
   - 可通过WebSocket `/ws` 接收实时MQTT消息推送
   - 消息格式：`{type: "mqtt", topic: "...", data: {...}}`

## 故障排查

### 3D模型不显示

1. 检查模型文件是否存在于 `/backend/static/models/` 目录
2. 确认文件名与设备 `model` 字段完全匹配
3. 查看浏览器控制台是否有加载错误
4. 检查模型文件格式是否为 `.glb`

### ECharts图表不渲染

1. 确保 `chartContainer` ref 已正确绑定
2. 检查容器是否有宽高
3. 确认 ECharts 是否正确初始化

### API请求失败

1. 检查后端是否已启动（http://localhost:8000）
2. 查看浏览器Network面板确认请求状态
3. 检查Vite代理配置是否正确

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**注意**：Three.js 需要 WebGL 2.0 支持。

## License

MIT
