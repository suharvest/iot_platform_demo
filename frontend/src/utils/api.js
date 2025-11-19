import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API错误:', error)
    return Promise.reject(error)
  }
)

// 设备API
export const deviceApi = {
  // 获取设备列表
  getDevices: (params) => api.get('/devices', { params }),

  // 获取设备详情
  getDevice: (sn) => api.get(`/devices/${sn}`),

  // 创建设备
  createDevice: (data) => api.post('/devices', data),

  // 更新设备
  updateDevice: (sn, data) => api.put(`/devices/${sn}`, data),

  // 删除设备
  deleteDevice: (sn) => api.delete(`/devices/${sn}`),

  // 复位设备
  resetDevice: (sn) => api.post(`/devices/${sn}/reset`),

  // 自动配置
  autoSetup: (sn) => api.post(`/devices/${sn}/autosetup`),

  // 执行测量
  measure: (sn, data) => api.post(`/devices/${sn}/measure`, data),

  // 获取测量历史
  getMeasurements: (sn, params) => api.get(`/devices/${sn}/measurements`, { params }),

  // 更新位置配置
  updateLocation: (sn, data) => api.put(`/devices/${sn}/location`, data),

  // 获取位置信息
  getLocation: (sn) => api.get(`/devices/${sn}/location`)
}

// 3D模型API
export const modelApi = {
  // 获取模型列表
  getModels: () => api.get('/models'),

  // 获取模型文件URL
  getModelUrl: (modelName) => `/api/models/${modelName}.glb`
}

// MQTT配置API
export const mqttApi = {
  // 获取MQTT配置
  getConfig: () => api.get('/mqtt/config'),

  // 更新MQTT配置
  updateConfig: (data) => api.put('/mqtt/config', data)
}

export default api
