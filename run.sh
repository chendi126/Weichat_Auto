#!/bin/bash

# AI 科技新闻自动发布 - 运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置 PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR"

# 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装依赖（如果需要）
if [ ! -d "node_modules" ] && [ -f "requirements.txt" ]; then
    echo "安装依赖..."
    pip install -r requirements.txt
fi

# 解析参数
MODE=""
TYPE=""

while getopts "ndgGfh" opt; do
    case "$opt" in
        n)
            MODE="now"
            TYPE="news"
            ;;
        d)
            MODE="daemon"
            ;;
        g)
            MODE="now"
            TYPE="github"
            ;;
        G)
            MODE="github"
            ;;
        f)
            MODE="feishu"
            ;;
        h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -n    立即执行AI新闻（手动模式）"
            echo "  -g    立即执行GitHub热门（手动模式）"
            echo "  -d    以守护进程模式运行AI新闻定时任务"
            echo "  -G    以守护进程模式运行GitHub热门定时任务"
            echo "  -f    启动飞书机器人服务（接收消息）"
            echo "  -h    显示帮助"
            echo ""
            echo "示例:"
            echo "  $0 -n          # 手动执行AI新闻"
            echo "  $0 -g          # 手动执行GitHub热门"
            echo "  $0 -d          # 启动AI新闻定时任务"
            echo "  $0 -G          # 启动GitHub热门定时任务"
            echo "  $0 -f          # 启动飞书机器人服务"
            exit 0
            ;;
    esac
done

if [ -z "$MODE" ]; then
    echo "请指定运行模式: -n (AI新闻) 或 -g (GitHub热门) 或 -d/-G (定时) 或 -f (飞书)"
    echo "使用 -h 查看帮助"
    exit 1
fi

# 执行
if [ "$MODE" = "feishu" ]; then
    echo "启动飞书机器人服务..."
    export PYTHONPATH="$SCRIPT_DIR"
    python3 src/feishu_server.py
elif [ "$TYPE" = "github" ]; then
    python3 src/github_main.py --now
else
    python3 src/main.py --$MODE
fi
