#!/bin/bash

# 四川物联网平台 V2.0 - 一键启动脚本

echo "🚀 启动四川物联网平台 V2.0"
echo "================================"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查后端依赖
echo -e "${YELLOW}📦 检查后端依赖...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv未安装，请先安装: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi

# 检查前端依赖
echo -e "${YELLOW}📦 检查前端依赖...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm未安装，请先安装Node.js${NC}"
    exit 1
fi

# 安装后端依赖
echo -e "${YELLOW}📦 安装后端依赖...${NC}"
uv sync
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 后端依赖安装失败${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 后端依赖安装完成${NC}"

# 安装前端依赖
echo -e "${YELLOW}📦 安装前端依赖...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 前端依赖安装失败${NC}"
        exit 1
    fi
fi
cd ..
echo -e "${GREEN}✅ 前端依赖安装完成${NC}"

# 创建必要的目录
echo -e "${YELLOW}📁 创建数据目录...${NC}"
mkdir -p data
mkdir -p logs
mkdir -p backend/static/models
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到.env文件，使用默认配置${NC}"
fi

# 检查并停止已有进程
echo -e "${YELLOW}🔍 检查已运行的服务...${NC}"
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  后端服务已在运行 (PID: $BACKEND_PID)，正在停止...${NC}"
        kill $BACKEND_PID 2>/dev/null
        sleep 1
    fi
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  前端服务已在运行 (PID: $FRONTEND_PID)，正在停止...${NC}"
        kill $FRONTEND_PID 2>/dev/null
        sleep 1
    fi
    rm -f .frontend.pid
fi

# 检查MQTT Broker
echo -e "${YELLOW}🔌 检查MQTT Broker...${NC}"
if ! nc -z localhost 1883 2>/dev/null; then
    echo -e "${RED}⚠️  MQTT Broker未运行！${NC}"
    echo -e "${YELLOW}启动方法:${NC}"
    echo "  brew services start mosquitto  (macOS)"
    echo "  sudo systemctl start mosquitto  (Linux)"
    echo "  docker run -d -p 1883:1883 eclipse-mosquitto  (Docker)"
    echo ""
    read -p "是否继续启动？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ 准备就绪！开始启动服务...${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# 启动后端
echo -e "${YELLOW}🚀 启动后端服务...${NC}"
cd "$SCRIPT_DIR"
nohup uv run python -m backend.main > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid
echo -e "${GREEN}✅ 后端已启动 (PID: $BACKEND_PID)${NC}"
echo -e "   日志文件: logs/backend.log"
sleep 2

# 启动前端
echo -e "${YELLOW}🚀 启动前端服务...${NC}"
cd "$SCRIPT_DIR/frontend"
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.frontend.pid
cd "$SCRIPT_DIR"
echo -e "${GREEN}✅ 前端已启动 (PID: $FRONTEND_PID)${NC}"
echo -e "   日志文件: logs/frontend.log"
sleep 3

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 所有服务已启动！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
# 获取本机IP地址
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
echo "访问地址："
echo -e "  前端 (本机):   ${GREEN}http://localhost:5173${NC}"
if [ ! -z "$LOCAL_IP" ]; then
echo -e "  前端 (局域网): ${GREEN}http://${LOCAL_IP}:5173${NC}"
fi
echo -e "  后端API (本机):   ${GREEN}http://localhost:9099${NC}"
if [ ! -z "$LOCAL_IP" ]; then
echo -e "  后端API (局域网): ${GREEN}http://${LOCAL_IP}:9099${NC}"
fi
echo -e "  API文档: ${GREEN}http://localhost:9099/docs${NC}"
echo ""
echo "日志文件："
echo "  后端日志: logs/backend.log"
echo "  前端日志: logs/frontend.log"
echo ""
echo "管理命令："
echo -e "  查看后端日志: ${YELLOW}tail -f logs/backend.log${NC}"
echo -e "  查看前端日志: ${YELLOW}tail -f logs/frontend.log${NC}"
echo -e "  停止所有服务: ${YELLOW}./stop_all.sh${NC}"
echo ""
echo "提示："
echo "  - MQTT Broker: localhost:1883"
echo "  - 3D模型文件放在 backend/static/models/ 目录"
echo "  - 详细文档: README_V2.md"
echo ""

# 等待3秒后自动打开浏览器（可选）
echo -e "${YELLOW}3秒后自动打开浏览器...${NC}"
sleep 3
if command -v open &> /dev/null; then
    open http://localhost:5173
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
fi
