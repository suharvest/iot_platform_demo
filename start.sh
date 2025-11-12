#!/bin/bash

# 四川物联网平台 - 启动脚本

set -e

echo "========================================="
echo "  四川物联网平台 - 产线设备实时监控系统"
echo "========================================="
echo ""

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ 已加载环境变量"
else
    echo "⚠  未找到 .env 文件，使用默认配置"
fi

# 检查是否需要启动本地MQTT
if [ "$START_LOCAL_MQTT" = "true" ]; then
    echo ""
    echo "检查本地Mosquitto服务..."

    if pgrep -x "mosquitto" > /dev/null; then
        echo "✓ Mosquitto已在运行"
    else
        echo "启动本地Mosquitto..."

        # 检查mosquitto是否安装
        if command -v mosquitto &> /dev/null; then
            mosquitto -d
            sleep 2

            if pgrep -x "mosquitto" > /dev/null; then
                echo "✓ Mosquitto已启动"
            else
                echo "✗ Mosquitto启动失败"
                exit 1
            fi
        else
            echo "✗ 未找到mosquitto命令"
            echo "  请先安装: brew install mosquitto"
            exit 1
        fi
    fi
else
    echo "✓ 使用外部MQTT Broker: $MQTT_BROKER:$MQTT_PORT"
fi

# 同步Python依赖
echo ""
echo "同步Python依赖..."
if command -v uv &> /dev/null; then
    uv sync
    echo "✓ 依赖同步完成"
else
    echo "✗ 未找到uv命令"
    echo "  请先安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 初始化数据库
echo ""
echo "初始化数据库..."
uv run python -c "from backend.database import init_db; init_db()"

# 启动后端服务
echo ""
echo "启动后端服务..."
echo "地址: http://${API_HOST:-0.0.0.0}:${API_PORT:-8000}"
echo ""

# 保存PID以便停止
uv run uvicorn backend.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --reload &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid

# 等待服务启动
sleep 3

# 检查服务是否启动成功
if ps -p $BACKEND_PID > /dev/null; then
    echo ""
    echo "========================================="
    echo "✓ 服务已启动成功！"
    echo "========================================="
    echo ""
    echo "📱 前端访问地址:"
    echo "   http://localhost:${API_PORT:-8000}"
    echo ""
    echo "📡 API文档:"
    echo "   http://localhost:${API_PORT:-8000}/docs"
    echo ""
    echo "🔌 WebSocket地址:"
    echo "   ws://localhost:${API_PORT:-8000}/ws"
    echo ""
    echo "⚙️  MQTT Broker:"
    echo "   ${MQTT_BROKER:-localhost}:${MQTT_PORT:-1883}"
    echo ""
    echo "========================================="
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo "或运行: ./stop.sh"
    echo ""

    # 尝试打开浏览器
    if command -v open &> /dev/null; then
        sleep 2
        open "http://localhost:${API_PORT:-8000}"
    fi

    # 等待进程
    wait $BACKEND_PID
else
    echo "✗ 后端服务启动失败"
    exit 1
fi
