#!/bin/bash

# 四川物联网平台 - 停止脚本

echo "正在停止服务..."

# 停止后端服务
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✓ 后端服务已停止"
    else
        echo "⚠  后端服务未运行"
    fi
    rm .backend.pid
else
    # 备用方法：通过进程名停止
    pkill -f "uvicorn backend.main"
    echo "✓ 已尝试停止后端服务"
fi

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 如果启用了本地MQTT，也停止它
if [ "$START_LOCAL_MQTT" = "true" ]; then
    if pgrep -x "mosquitto" > /dev/null; then
        pkill -x mosquitto
        echo "✓ 本地Mosquitto已停止"
    fi
fi

echo "✓ 服务已全部停止"
