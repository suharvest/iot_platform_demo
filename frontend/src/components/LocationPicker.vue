<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal location-picker-modal">
      <div class="modal-header">
        <h3 class="modal-title">配置设备位置</h3>
        <button class="modal-close" @click="close">×</button>
      </div>

      <div class="modal-body">
        <p class="description">
          关联位置追踪器的MQTT主题，该主题将提供设备的位置信息
        </p>

        <div class="form-group">
          <label>MQTT主题</label>
          <input
            v-model="locationTopic"
            type="text"
            placeholder="例如：location/desk1"
            class="input-field"
          />
          <span class="hint">例如：location/desk1</span>
        </div>

        <div v-if="locationPreview" class="preview-box">
          <div class="preview-label">当前位置值预览</div>
          <div class="preview-value">{{ locationPreview }}</div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">取消</button>
        <button class="btn btn-primary" @click="save" :disabled="!locationTopic">
          保存
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { deviceApi } from '../utils/api'

export default {
  name: 'LocationPicker',
  props: {
    device: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'updated'],
  setup(props, { emit }) {
    const locationTopic = ref(props.device.location_topic || '')
    const locationPreview = ref(props.device.location || '')

    const close = () => {
      emit('close')
    }

    const save = async () => {
      try {
        await deviceApi.updateLocation(props.device.sn, {
          location_topic: locationTopic.value
        })
        alert('位置配置已更新')
        emit('updated')
        close()
      } catch (error) {
        console.error('保存位置配置失败:', error)
        alert('保存失败')
      }
    }

    // 加载位置预览
    const loadLocationPreview = async () => {
      if (!locationTopic.value) return

      try {
        const response = await deviceApi.getLocation(props.device.sn)
        locationPreview.value = response.location || '暂无数据'
      } catch (error) {
        console.error('加载位置预览失败:', error)
      }
    }

    onMounted(() => {
      loadLocationPreview()
    })

    return {
      locationTopic,
      locationPreview,
      close,
      save
    }
  }
}
</script>

<style scoped>
.location-picker-modal {
  width: 500px;
  max-width: 90vw;
}

.modal-body {
  margin: 20px 0;
}

.description {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.input-field {
  width: 100%;
}

.hint {
  display: block;
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 6px;
}

.preview-box {
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  padding: 16px;
  margin-top: 20px;
}

.preview-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.preview-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}
</style>
