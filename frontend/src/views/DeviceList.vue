<template>
  <div class="device-list-page">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <svg class="logo-icon" width="32" height="32" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <h1 class="title">设备管理器</h1>
      </div>
      <div class="header-right">
        <button class="btn-icon" @click="refreshDevices">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M21 3V7H17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </header>

    <div class="content">
      <!-- MQTT配置面板 -->
      <div class="mqtt-panel card">
        <div class="panel-header" @click="mqttPanelExpanded = !mqttPanelExpanded">
          <div class="panel-title-group">
            <h3>MQTT配置</h3>
            <span :class="['status-badge', mqttConnected ? 'connected' : 'disconnected']">
              {{ mqttConnected ? '已连接' : '未连接' }}
            </span>
          </div>
          <svg
            class="expand-icon"
            :class="{ expanded: mqttPanelExpanded }"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
          >
            <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>

        <div v-if="mqttPanelExpanded" class="panel-content">
          <div class="form-grid">
            <div class="form-group">
              <label>Broker地址</label>
              <input v-model="mqttConfig.broker" type="text" placeholder="mqtt.broker.com" />
            </div>
            <div class="form-group">
              <label>端口</label>
              <input v-model="mqttConfig.port" type="number" placeholder="1883" />
            </div>
            <div class="form-group">
              <label>用户名</label>
              <input v-model="mqttConfig.username" type="text" placeholder="device_manager" />
            </div>
            <div class="form-group">
              <label>密码</label>
              <input v-model="mqttConfig.password" type="password" placeholder="············" />
            </div>
          </div>
          <button class="btn btn-primary mt-4" @click="updateMqttConfig">
            应用/更新
          </button>
        </div>
      </div>

      <!-- 设备列表 -->
      <div class="device-section">
        <div class="section-header">
          <h2>设备列表</h2>
          <button class="btn btn-primary btn-sm" @click="refreshDevices">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style="margin-right: 4px;">
              <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            刷新
          </button>
        </div>

        <div class="table-container card">
          <table v-if="devices.length > 0">
            <thead>
              <tr>
                <th>设备名称</th>
                <th>型号</th>
                <th>序列号</th>
                <th>位置</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="device in devices" :key="device.sn">
                <td>{{ device.device_name }}</td>
                <td>{{ device.model || '-' }}</td>
                <td><code>{{ device.sn }}</code></td>
                <td>{{ device.location || '-' }}</td>
                <td>
                  <span :class="['status-indicator', device.status === 'online' ? 'status-online' : 'status-offline']">
                    {{ device.status === 'online' ? '在线' : '离线' }}
                  </span>
                </td>
                <td>
                  <button class="btn btn-primary btn-sm" @click="goToDetail(device.sn)">
                    详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else class="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>暂无设备</p>
            <p class="text-dim text-sm">等待设备通过MQTT连接...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { deviceApi, mqttApi } from '../utils/api'

export default {
  name: 'DeviceList',
  setup() {
    const router = useRouter()
    const devices = ref([])
    const mqttPanelExpanded = ref(false)
    const mqttConnected = ref(false)
    const mqttConfig = ref({
      broker: 'localhost',
      port: 1883,
      username: 'device_manager',
      password: ''
    })

    // 加载设备列表
    const loadDevices = async () => {
      try {
        const response = await deviceApi.getDevices()
        devices.value = response.devices || []
      } catch (error) {
        console.error('加载设备列表失败:', error)
      }
    }

    // 刷新设备
    const refreshDevices = () => {
      loadDevices()
    }

    // 跳转到设备详情
    const goToDetail = (sn) => {
      router.push(`/devices/${sn}`)
    }

    // 加载MQTT配置
    const loadMqttConfig = async () => {
      try {
        const config = await mqttApi.getConfig()
        mqttConfig.value.broker = config.broker
        mqttConfig.value.port = config.port
        mqttConfig.value.username = config.username || ''
        mqttConnected.value = config.connected
      } catch (error) {
        console.error('加载MQTT配置失败:', error)
      }
    }

    // 更新MQTT配置
    const updateMqttConfig = async () => {
      try {
        await mqttApi.updateConfig(mqttConfig.value)
        alert('MQTT配置已更新（需要重启应用生效）')
      } catch (error) {
        console.error('更新MQTT配置失败:', error)
        alert('更新失败')
      }
    }

    onMounted(() => {
      loadDevices()
      loadMqttConfig()

      // 定时刷新设备列表
      setInterval(loadDevices, 10000)
    })

    return {
      devices,
      mqttPanelExpanded,
      mqttConnected,
      mqttConfig,
      refreshDevices,
      goToDetail,
      updateMqttConfig
    }
  }
}
</script>

<style scoped>
.device-list-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  color: var(--color-primary);
}

.title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  gap: 12px;
}

.btn-icon {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-icon:hover {
  border-color: var(--color-primary);
  background: rgba(59, 130, 246, 0.1);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* MQTT面板 */
.mqtt-panel {
  margin-bottom: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.panel-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-title-group h3 {
  font-size: 18px;
  font-weight: 600;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.connected {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-success);
}

.status-badge.disconnected {
  background: rgba(239, 68, 68, 0.2);
  color: var(--color-danger);
}

.expand-icon {
  color: var(--text-secondary);
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.panel-content {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input {
  width: 100%;
}

/* 设备列表区域 */
.device-section {
  margin-top: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
}

.table-container {
  overflow-x: auto;
}

code {
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--color-primary);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-dim);
}

.empty-state svg {
  margin-bottom: 16px;
  color: var(--text-dim);
}

.empty-state p {
  margin: 8px 0;
}
</style>
