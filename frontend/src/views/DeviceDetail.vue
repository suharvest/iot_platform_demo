<template>
  <div class="device-detail-page">
    <!-- 顶部导航 -->
    <header class="header">
      <button class="btn-back" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        返回
      </button>
      <h1 class="title">{{ deviceType }}详情</h1>
      <div></div>
    </header>

    <div v-if="device" class="content">
      <!-- 设备信息卡片 -->
      <div class="device-info-card card">
        <h3 class="card-title">设备信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">设备名称</span>
            <span class="value">{{ device.device_name }}</span>
          </div>
          <div class="info-item">
            <span class="label">型号</span>
            <span class="value">{{ device.model || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">序列号</span>
            <span class="value"><code>{{ device.sn }}</code></span>
          </div>
          <div class="info-item clickable" @click="showLocationPicker = true">
            <span class="label">位置</span>
            <span class="value location">
              {{ device.location || '未配置' }}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M21 10C21 17 12 23 12 23C12 23 3 17 3 10C3 5.02944 7.02944 1 12 1C16.9706 1 21 5.02944 21 10Z" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2"/>
              </svg>
            </span>
          </div>
          <div class="info-item">
            <span class="label">状态</span>
            <span :class="['status-indicator', device.status === 'online' ? 'status-online' : 'status-offline']">
              {{ device.status === 'online' ? '在线' : '离线' }}
            </span>
          </div>
        </div>

        <div class="action-buttons">
          <button class="btn btn-primary" @click="autoSetup">自动配置</button>
          <button class="btn btn-secondary" @click="resetDevice">复位</button>
          <button v-if="hasModel" class="btn btn-primary" @click="show3DViewer = true">
            3D视图
          </button>
        </div>
      </div>

      <!-- 实时趋势监控 -->
      <div class="monitoring-card card">
        <h3 class="card-title">实时趋势监控</h3>

        <div class="monitoring-controls">
          <div class="tabs">
            <button
              :class="['tab', { active: activeTab === 'frequency' }]"
              @click="activeTab = 'frequency'"
            >
              频率
            </button>
            <button
              :class="['tab', { active: activeTab === 'amplitude' }]"
              @click="activeTab = 'amplitude'"
            >
              幅度
            </button>
          </div>

          <div class="controls-right">
            <select v-model="selectedChannel" class="channel-select">
              <option :value="1">通道 1</option>
              <option :value="2">通道 2</option>
              <option :value="3">通道 3</option>
              <option :value="4">通道 4</option>
            </select>

            <label class="realtime-toggle">
              <input type="checkbox" v-model="realtimeRead" />
              <span>实时读取</span>
            </label>
          </div>
        </div>

        <!-- 当前测量值 - 显示在图表上方 -->
        <div v-if="latestValue" class="current-value">
          <div class="value-label">{{ activeTab === 'frequency' ? '频率' : '幅度' }}</div>
          <div class="value-number">{{ latestValue.value }} {{ latestValue.unit }}</div>
          <div class="value-change" :class="{ positive: latestValue.change > 0, negative: latestValue.change < 0 }">
            {{ latestValue.change > 0 ? '+' : '' }}{{ latestValue.change }}%
          </div>
        </div>

        <!-- 图表容器 -->
        <div v-show="measurements.length > 0" ref="chartContainer" class="chart-container"></div>

        <!-- 空状态提示 -->
        <div v-if="measurements.length === 0" class="empty-state">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
            <path d="M9 19l-7-7 7-7M15 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>暂无测量数据</p>
          <p class="hint">开启"实时读取"或点击"自动配置"开始采集数据</p>
        </div>
      </div>
    </div>

    <!-- 位置配置器模态框 -->
    <LocationPicker
      v-if="showLocationPicker"
      :device="device"
      @close="showLocationPicker = false"
      @updated="onLocationUpdated"
    />

    <!-- 3D模型查看器 -->
    <Model3DViewer
      v-if="show3DViewer"
      :model-name="device.model"
      @close="show3DViewer = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { deviceApi, modelApi } from '../utils/api'
import * as echarts from 'echarts'
import LocationPicker from '../components/LocationPicker.vue'
import Model3DViewer from '../components/Model3DViewer.vue'

export default {
  name: 'DeviceDetail',
  components: {
    LocationPicker,
    Model3DViewer
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const sn = route.params.sn

    const device = ref(null)
    const activeTab = ref('frequency')
    const selectedChannel = ref(1)
    const realtimeRead = ref(false)
    const showLocationPicker = ref(false)
    const show3DViewer = ref(false)
    const latestValue = ref(null)
    const measurements = ref([])
    const chartContainer = ref(null)
    let chart = null
    let realtimeInterval = null
    const availableModels = ref([])

    // 图表时间范围配置（单位：分钟）
    const CHART_TIME_RANGE_MINUTES = 1

    const deviceType = computed(() => {
      if (!device.value) return '设备'
      return device.value.device_type === 'oscilloscope' ? '示波器' : '设备'
    })

    const hasModel = computed(() => {
      return device.value && availableModels.value.includes(device.value.model)
    })

    // 加载设备信息
    const loadDevice = async () => {
      try {
        device.value = await deviceApi.getDevice(sn)
      } catch (error) {
        console.error('加载设备失败:', error)
      }
    }

    // 加载可用模型列表
    const loadModels = async () => {
      try {
        const response = await modelApi.getModels()
        availableModels.value = response.models || []
      } catch (error) {
        console.error('加载模型列表失败:', error)
      }
    }

    // 加载测量数据
    const loadMeasurements = async () => {
      try {
        const task = activeTab.value === 'frequency' ? 'freq_meas' : 'vpp_meas'
        const hoursToFetch = CHART_TIME_RANGE_MINUTES / 60  // 转换为小时
        const response = await deviceApi.getMeasurements(sn, {
          channel: selectedChannel.value,
          task,
          hours: hoursToFetch
        })
        measurements.value = response.data || []
        updateChart()
      } catch (error) {
        console.error('加载测量数据失败:', error)
      }
    }

    // 初始化图表
    const initChart = () => {
      if (!chartContainer.value) return

      chart = echarts.init(chartContainer.value, 'dark')

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(21, 25, 50, 0.9)',
          borderColor: 'rgba(59, 130, 246, 0.3)',
          textStyle: {
            color: '#e5e7eb'
          },
          formatter: (params) => {
            const param = params[0]
            const date = new Date(param.value[0])
            const timeStr = date.toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            })
            return `${timeStr}<br/>${param.marker}${param.seriesName}: ${param.value[1]}`
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: {
            lineStyle: {
              color: 'rgba(59, 130, 246, 0.3)'
            }
          },
          axisLabel: {
            color: '#9ca3af',
            formatter: (value) => {
              const date = new Date(value)
              return date.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })
            }
          }
        },
        yAxis: {
          type: 'value',
          axisLine: {
            lineStyle: {
              color: 'rgba(59, 130, 246, 0.3)'
            }
          },
          axisLabel: {
            color: '#9ca3af'
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(59, 130, 246, 0.1)'
            }
          }
        },
        series: [
          {
            name: activeTab.value === 'frequency' ? '频率' : '幅度',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            itemStyle: {
              color: '#3b82f6'
            },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                  { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
                ]
              }
            },
            data: []
          }
        ]
      }

      chart.setOption(option)
    }

    // 更新图表
    const updateChart = () => {
      if (measurements.value.length === 0) return

      // 如果图表还未初始化，或者容器不可见，则初始化图表
      if (!chart || !chartContainer.value || chartContainer.value.offsetParent === null) {
        // 等待DOM更新后初始化
        nextTick(() => {
          initChart()
          updateChart()
        })
        return
      }

      // 将UTC时间戳转换为本地时间显示
      const data = measurements.value.map(m => {
        // 后端返回的是UTC时间字符串，需要转换为本地时间
        const utcDate = new Date(m.timestamp + 'Z')  // 添加'Z'确保被解析为UTC
        return [utcDate.getTime(), m.value]
      })

      chart.setOption({
        series: [{
          data
        }]
      })

      // 确保图表尺寸正确
      chart.resize()

      // 更新最新值
      if (measurements.value.length > 0) {
        const latest = measurements.value[0]
        const previous = measurements.value[1]
        const change = previous ? ((latest.value - previous.value) / previous.value * 100).toFixed(1) : 0

        latestValue.value = {
          value: latest.value.toFixed(2),
          unit: latest.unit,
          change: parseFloat(change)
        }
      }
    }

    // 自动配置
    const autoSetup = async () => {
      try {
        await deviceApi.autoSetup(sn)
        alert('自动配置命令已发送')
      } catch (error) {
        console.error('自动配置失败:', error)
        alert('命令发送失败')
      }
    }

    // 复位设备
    const resetDevice = async () => {
      if (!confirm('确定要复位设备吗？')) return

      try {
        await deviceApi.resetDevice(sn)
        alert('复位命令已发送')
      } catch (error) {
        console.error('复位失败:', error)
        alert('命令发送失败')
      }
    }

    // 执行测量
    const measure = async () => {
      const task = activeTab.value === 'frequency' ? 'freq_meas' : 'vpp_meas'
      try {
        await deviceApi.measure(sn, {
          task,
          channel: selectedChannel.value
        })
        // 等待一下再刷新数据
        setTimeout(loadMeasurements, 1000)
      } catch (error) {
        console.error('测量失败:', error)
      }
    }

    // 实时读取
    watch(realtimeRead, (newVal) => {
      if (newVal) {
        // 开始实时读取
        measure()
        realtimeInterval = setInterval(measure, 2000)
      } else {
        // 停止实时读取
        if (realtimeInterval) {
          clearInterval(realtimeInterval)
          realtimeInterval = null
        }
      }
    })

    // 监听tab切换
    watch(activeTab, () => {
      loadMeasurements()
    })

    // 监听通道切换
    watch(selectedChannel, () => {
      loadMeasurements()
    })

    // 位置更新回调
    const onLocationUpdated = () => {
      loadDevice()
    }

    // 返回
    const goBack = () => {
      router.push('/devices')
    }

    onMounted(() => {
      loadDevice()
      loadModels()
      loadMeasurements()

      // 窗口resize时调整图表
      window.addEventListener('resize', () => {
        if (chart) chart.resize()
      })
    })

    onUnmounted(() => {
      if (chart) {
        chart.dispose()
      }
      if (realtimeInterval) {
        clearInterval(realtimeInterval)
      }
    })

    return {
      device,
      deviceType,
      activeTab,
      selectedChannel,
      realtimeRead,
      showLocationPicker,
      show3DViewer,
      latestValue,
      measurements,
      chartContainer,
      hasModel,
      autoSetup,
      resetDevice,
      onLocationUpdated,
      goBack
    }
  }
}
</script>

<style scoped>
.device-detail-page {
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

.btn-back {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-back:hover {
  border-color: var(--color-primary);
  background: rgba(59, 130, 246, 0.1);
}

.title {
  font-size: 20px;
  font-weight: 600;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 设备信息卡片 */
.device-info-card {
  margin-bottom: 24px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item.clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}

.info-item.clickable:hover {
  opacity: 0.8;
}

.info-item .label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-item .value {
  font-size: 16px;
  color: var(--text-primary);
  font-weight: 500;
}

.info-item .value.location {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-primary);
}

.action-buttons {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

/* 监控卡片 */
.monitoring-card {
  min-height: 500px;
}

.monitoring-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tab {
  padding: 8px 20px;
  border: 1px solid var(--border-color);
  background: none;
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 500;
}

.tab.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.controls-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.channel-select {
  padding: 8px 12px;
  min-width: 120px;
}

.realtime-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.realtime-toggle input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.chart-container {
  width: 100%;
  height: 400px;
  margin: 20px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--text-secondary);
  text-align: center;
}

.empty-state svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 8px 0;
  font-size: 16px;
}

.empty-state .hint {
  font-size: 14px;
  opacity: 0.7;
}

.current-value {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
}

.value-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.value-number {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
}

.value-change {
  font-size: 16px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 20px;
}

.value-change.positive {
  background: rgba(16, 185, 129, 0.2);
  color: var(--color-success);
}

.value-change.negative {
  background: rgba(239, 68, 68, 0.2);
  color: var(--color-danger);
}

code {
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--color-primary);
}
</style>
