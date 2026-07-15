#!/bin/bash
set -e

echo ""
echo "  📐 净排 启动中..."
echo "  ────────────────────────────────"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "  ❌ 未找到 Node.js，请先安装: https://nodejs.org"
    exit 1
fi
echo "  ✅ Node.js 已就绪: $(node -v)"

# 选择包管理器
if command -v pnpm &> /dev/null; then
    PKG="pnpm"
elif command -v yarn &> /dev/null; then
    PKG="yarn"
else
    PKG="npm"
fi

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "  📦 首次运行，正在安装依赖..."
    $PKG install
else
    echo "  📦 依赖已安装，跳过"
fi

echo "  🚀 正在启动开发服务器..."
echo "  ────────────────────────────────"
echo ""
echo "  👉 浏览器打开 http://localhost:3000 即可使用"
echo "  👉 按 Ctrl+C 停止服务"
echo ""

# 自动打开浏览器
if command -v open &> /dev/null; then
    open http://localhost:3000 2>/dev/null &
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 2>/dev/null &
fi

$PKG run dev
