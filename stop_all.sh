#!/bin/bash

# 四川物联网平台 V2.0 - 一键停止脚本

echo "🛑 停止四川物联网平台 V2.0"
echo "================================"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 停止后端
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null
        # 等待进程结束
        for i in {1..5}; do
            if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        # 如果还没停止，强制结束
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}强制停止后端...${NC}"
            kill -9 $BACKEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  后端服务未运行${NC}"
    fi
    rm -f .backend.pid
else
    echo -e "${YELLOW}⚠️  未找到后端PID文件${NC}"
fi

# 停止前端
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null
        # 等待进程结束
        for i in {1..5}; do
            if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        # 如果还没停止，强制结束
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}强制停止前端...${NC}"
            kill -9 $FRONTEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务未运行${NC}"
    fi
    rm -f .frontend.pid
else
    echo -e "${YELLOW}⚠️  未找到前端PID文件${NC}"
fi

# 清理可能残留的Vite进程（备用）
echo -e "${YELLOW}🔍 检查残留进程...${NC}"
VITE_PIDS=$(pgrep -f "vite" 2>/dev/null)
if [ ! -z "$VITE_PIDS" ]; then
    echo -e "${YELLOW}发现Vite进程，正在清理...${NC}"
    pkill -f "vite" 2>/dev/null
fi

UV_PIDS=$(pgrep -f "uv run python -m backend.main" 2>/dev/null)
if [ ! -z "$UV_PIDS" ]; then
    echo -e "${YELLOW}发现后端进程，正在清理...${NC}"
    pkill -f "uv run python -m backend.main" 2>/dev/null
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ 所有服务已停止！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "提示："
echo -e "  重新启动: ${YELLOW}./start_all.sh${NC}"
echo ""
