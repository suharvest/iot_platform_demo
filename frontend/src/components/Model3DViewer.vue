<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal model-viewer-modal">
      <div class="modal-header">
        <h3 class="modal-title">3D设备模型</h3>
        <button class="modal-close" @click="close">×</button>
      </div>

      <div class="modal-body">
        <div ref="viewerContainer" class="viewer-container"></div>

        <div class="controls-hint">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 16V12M12 8H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          右键旋转 | Shift+右键平移 | 滚轮缩放
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { modelApi } from '../utils/api'

export default {
  name: 'Model3DViewer',
  props: {
    modelName: {
      type: String,
      required: true
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const viewerContainer = ref(null)
    let scene, camera, renderer, controls, model
    let handleKeyDown, handleKeyUp, handleResize

    const close = () => {
      emit('close')
    }

    const initScene = () => {
      if (!viewerContainer.value) return

      const width = viewerContainer.value.clientWidth
      const height = viewerContainer.value.clientHeight

      // 创建场景
      scene = new THREE.Scene()
      scene.background = new THREE.Color(0x0a0e27)

      // 创建相机
      camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
      camera.position.set(0, 2, 5)

      // 创建渲染器
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
      renderer.setSize(width, height)
      renderer.setPixelRatio(window.devicePixelRatio)
      renderer.shadowMap.enabled = true
      renderer.shadowMap.type = THREE.PCFSoftShadowMap
      viewerContainer.value.appendChild(renderer.domElement)

      // 添加灯光 - 科技感灯光系统
      // 环境光
      const ambientLight = new THREE.AmbientLight(0x404040, 1.5)
      scene.add(ambientLight)

      // 主定向光（冷蓝色）
      const directionalLight = new THREE.DirectionalLight(0x60a5fa, 2)
      directionalLight.position.set(5, 5, 5)
      directionalLight.castShadow = true
      scene.add(directionalLight)

      // 补光（暖色）
      const fillLight = new THREE.DirectionalLight(0xffffff, 0.5)
      fillLight.position.set(-5, 3, -5)
      scene.add(fillLight)

      // 点光源（动态科技感）
      const pointLight = new THREE.PointLight(0x3b82f6, 1, 50)
      pointLight.position.set(0, 3, 0)
      scene.add(pointLight)

      // 半球光（天地光）
      const hemisphereLight = new THREE.HemisphereLight(0x60a5fa, 0x0a0e27, 0.6)
      scene.add(hemisphereLight)

      // 添加网格地面
      const gridHelper = new THREE.GridHelper(10, 20, 0x3b82f6, 0x151932)
      gridHelper.material.opacity = 0.3
      gridHelper.material.transparent = true
      scene.add(gridHelper)

      // 添加坐标轴辅助（可选，调试用）
      // const axesHelper = new THREE.AxesHelper(5)
      // scene.add(axesHelper)

      // 创建轨道控制器
      controls = new OrbitControls(camera, renderer.domElement)
      controls.enableDamping = true
      controls.dampingFactor = 0.05
      controls.enablePan = true // 启用平移
      controls.enableZoom = true // 启用缩放
      controls.minDistance = 2
      controls.maxDistance = 10

      // 默认鼠标按钮配置
      controls.mouseButtons = {
        RIGHT: THREE.MOUSE.ROTATE, // 右键旋转
        MIDDLE: THREE.MOUSE.DOLLY, // 中键缩放
        LEFT: -1 // 禁用左键
      }

      // 添加Shift+右键平移功能 - 使用鼠标事件监听
      const canvas = renderer.domElement

      const handleMouseDown = (e) => {
        // 检测右键 (button 2) + Shift键
        if (e.button === 2 && e.shiftKey) {
          // 切换到平移模式
          controls.mouseButtons.RIGHT = THREE.MOUSE.PAN
        }
      }

      const handleMouseUp = (e) => {
        // 鼠标释放时恢复旋转模式
        if (e.button === 2) {
          controls.mouseButtons.RIGHT = THREE.MOUSE.ROTATE
        }
      }

      // 监听canvas的鼠标事件
      canvas.addEventListener('mousedown', handleMouseDown)
      canvas.addEventListener('mouseup', handleMouseUp)

      // 保存引用用于清理
      handleKeyDown = handleMouseDown
      handleKeyUp = handleMouseUp

      // 窗口resize处理
      handleResize = () => {
        if (!viewerContainer.value) return
        const width = viewerContainer.value.clientWidth
        const height = viewerContainer.value.clientHeight

        camera.aspect = width / height
        camera.updateProjectionMatrix()
        renderer.setSize(width, height)
      }

      window.addEventListener('resize', handleResize)

      // 动画循环
      const animate = () => {
        requestAnimationFrame(animate)
        controls.update()
        renderer.render(scene, camera)
      }

      animate()
    }

    const loadModel = () => {
      const loader = new GLTFLoader()
      const modelUrl = modelApi.getModelUrl(props.modelName)

      loader.load(
        modelUrl,
        (gltf) => {
          model = gltf.scene

          // 计算模型边界
          const box = new THREE.Box3().setFromObject(model)
          const center = box.getCenter(new THREE.Vector3())
          const size = box.getSize(new THREE.Vector3())

          // 居中模型
          model.position.sub(center)

          // 缩放模型以适配视图
          const maxDim = Math.max(size.x, size.y, size.z)
          const scale = 2 / maxDim
          model.scale.multiplyScalar(scale)

          // 启用阴影
          model.traverse((child) => {
            if (child.isMesh) {
              child.castShadow = true
              child.receiveShadow = true

              // 增强材质（科技感）
              if (child.material) {
                child.material.metalness = 0.3
                child.material.roughness = 0.6
              }
            }
          })

          scene.add(model)

          // 调整相机位置
          const distance = maxDim * 2
          camera.position.set(distance, distance * 0.5, distance)
          camera.lookAt(0, 0, 0)
          controls.target.set(0, 0, 0)
        },
        (progress) => {
          console.log('加载进度:', (progress.loaded / progress.total * 100).toFixed(2) + '%')
        },
        (error) => {
          console.error('模型加载失败:', error)
          alert('3D模型加载失败，请检查模型文件是否存在')
        }
      )
    }

    onMounted(() => {
      initScene()
      loadModel()
    })

    onUnmounted(() => {
      // 清理事件监听器
      if (renderer && renderer.domElement) {
        if (handleKeyDown) {
          renderer.domElement.removeEventListener('mousedown', handleKeyDown)
        }
        if (handleKeyUp) {
          renderer.domElement.removeEventListener('mouseup', handleKeyUp)
        }
      }
      if (handleResize) {
        window.removeEventListener('resize', handleResize)
      }

      // 清理资源
      if (renderer) {
        renderer.dispose()
        if (viewerContainer.value && renderer.domElement) {
          viewerContainer.value.removeChild(renderer.domElement)
        }
      }
      if (controls) {
        controls.dispose()
      }
      if (model) {
        scene.remove(model)
      }
    })

    return {
      viewerContainer,
      close
    }
  }
}
</script>

<style scoped>
.model-viewer-modal {
  width: 80vw;
  height: 80vh;
  max-width: 1200px;
  padding: 0;
  overflow: hidden;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-body {
  position: relative;
  height: calc(100% - 64px);
  padding: 0;
}

.viewer-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(180deg, #0a0e27 0%, #000000 100%);
}

.viewer-container canvas {
  display: block;
  border-radius: 0 0 12px 12px;
}

.controls-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(21, 25, 50, 0.9);
  border: 1px solid var(--border-glow);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  backdrop-filter: blur(10px);
}

.controls-hint svg {
  color: var(--color-primary);
}
</style>
