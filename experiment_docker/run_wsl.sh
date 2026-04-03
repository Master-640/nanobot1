#!/bin/bash
# WSL 环境下启动 LLM 对比实验

set -e  # 遇到错误立即退出

echo "========================================"
echo "LLM Backend 对比实验 - WSL 启动脚本"
echo "========================================"
echo ""

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装或未启动"
    exit 1
fi

echo "✅ Docker 版本：$(docker --version)"
echo ""

# 检查 Python3 是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "✅ Python 版本：$(python3 --version)"
echo ""

# 检查 API Key 环境变量
echo "检查环境变量..."

# 尝试从 config.json 读取 API keys（如果环境变量未设置）
echo "尝试从 config.json 读取 API keys..."
CONFIG_FILES=("/mnt/c/Users/24478/.nanobot/config.json" "$HOME/.nanobot/config.json")
CONFIG_FILE=""

for f in "${CONFIG_FILES[@]}"; do
    if [ -f "$f" ]; then
        CONFIG_FILE="$f"
        echo "📄 找到 config.json: $f"
        break
    fi
done

if [ -n "$CONFIG_FILE" ]; then
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        DEEPSEEK_API_KEY=$(python3 -c "import json,sys; c=json.load(open('$CONFIG_FILE')); print(c.get('providers',{}).get('deepseek',{}).get('apiKey',''))" 2>/dev/null || echo "")
        [ -n "$DEEPSEEK_API_KEY" ] && echo "  ✅ DEEPSEEK_API_KEY from config.json"
    fi
    
    if [ -z "$DASHSCOPE_API_KEY" ]; then
        DASHSCOPE_API_KEY=$(python3 -c "import json,sys; c=json.load(open('$CONFIG_FILE')); print(c.get('providers',{}).get('dashscope',{}).get('apiKey',''))" 2>/dev/null || echo "")
        [ -n "$DASHSCOPE_API_KEY" ] && echo "  ✅ DASHSCOPE_API_KEY from config.json"
    fi
    
    if [ -z "$KIMI_API_KEY" ]; then
        KIMI_API_KEY=$(python3 -c "import json,sys; c=json.load(open('$CONFIG_FILE')); print(c.get('providers',{}).get('moonshot',{}).get('apiKey',''))" 2>/dev/null || echo "")
        [ -n "$KIMI_API_KEY" ] && echo "  ✅ KIMI_API_KEY from config.json"
    fi
    
    if [ -z "$MINIMAX_API_KEY" ]; then
        MINIMAX_API_KEY=$(python3 -c "import json,sys; c=json.load(open('$CONFIG_FILE')); print(c.get('providers',{}).get('minimax',{}).get('apiKey',''))" 2>/dev/null || echo "")
        [ -n "$MINIMAX_API_KEY" ] && echo "  ✅ MINIMAX_API_KEY from config.json"
    fi
else
    echo "⚠️  config.json 未找到"
fi

# 导出环境变量
export DEEPSEEK_API_KEY
export DASHSCOPE_API_KEY
export KIMI_API_KEY
export MINIMAX_API_KEY

missing_vars=()
for var in "DEEPSEEK_API_KEY" "DASHSCOPE_API_KEY" "KIMI_API_KEY" "MINIMAX_API_KEY"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "⚠️  以下环境变量未设置："
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "请在运行前设置这些变量，例如："
    echo "  export DEEPSEEK_API_KEY='sk-xxx'"
    echo "  export DASHSCOPE_API_KEY='sk-xxx'"
    echo "  export KIMI_API_KEY='sk-xxx'"
    echo "  export MINIMAX_API_KEY='sk-xxx'"
    echo ""
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查数据文件
echo "检查数据文件..."
data_dir="shared/data"
required_files=("sales.csv" "user_behavior.csv" "financial.csv" "reviews.csv")

for file in "${required_files[@]}"; do
    if [ ! -f "$data_dir/$file" ]; then
        echo "❌ 数据文件缺失：$data_dir/$file"
        exit 1
    fi
done
echo "✅ 数据文件检查通过"
echo ""

# 切换到脚本目录
cd "$(dirname "$0")"

# 运行实验
echo "开始运行实验..."
echo "========================================"
python3 run_experiments.py

echo ""
echo "========================================"
echo "实验完成！"
echo "结果保存在：results/"
echo "========================================"
