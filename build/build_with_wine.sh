#!/bin/bash
# ========================================
# 使用 Wine 在 Linux 上打包 Windows 程序
# ========================================

set -e

VERSION="1.0.0"
BUILD_DATE=$(date +%Y%m%d)
RELEASE_NAME="FaceBlur-Pro-v${VERSION}-${BUILD_DATE}"

echo "========================================"
echo "  Wine 交叉打包工具"
echo "========================================"
echo ""

# 检查 Wine 是否安装
if ! command -v wine &> /dev/null; then
    echo "[错误] 未安装 Wine"
    echo ""
    echo "请先安装 Wine："
    echo "  Ubuntu/Debian: sudo apt install wine"
    echo "  CentOS/RHEL:   sudo yum install wine"
    echo ""
    exit 1
fi

echo "[1/6] 检查 Wine 版本..."
wine --version

echo ""
echo "[2/6] 安装 Windows 版 Python..."
# 下载 Windows 版 Python
PYTHON_URL="https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"
PYTHON_INSTALLER="python-installer.exe"

if [ ! -f "$PYTHON_INSTALLER" ]; then
    echo "下载 Windows 版 Python..."
    wget -O "$PYTHON_INSTALLER" "$PYTHON_URL" || {
        echo "[错误] 下载失败"
        exit 1
    }
fi

# 静默安装 Python 到 Wine
echo "安装 Python 到 Wine 环境（可能需要几分钟）..."
wine "$PYTHON_INSTALLER" /quiet InstallAllUsers=0 PrependPath=0 TargetDir=C:\\Python311 > /dev/null 2>&1 || true

echo ""
echo "[3/6] 安装 PyInstaller..."
wine C:\\Python311\\python.exe -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ""
echo "[4/6] 安装项目依赖..."
wine C:\\Python311\\python.exe -m pip install -r ../requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ""
echo "[5/6] 开始打包（使用 Windows 版 PyInstaller）..."
wine C:\\Python311\\Scripts\\pyinstaller.exe build.spec

echo ""
echo "[6/6] 复制文件到发布目录..."
mkdir -p "${RELEASE_NAME}"
cp dist/FaceBlur-Pro.exe "${RELEASE_NAME}/"
cp release_template/README_用户使用说明.md "${RELEASE_NAME}/使用说明.md" 2>/dev/null || true

# 创建版本信息
cat > "${RELEASE_NAME}/版本信息.txt" << EOF
FaceBlur Pro v${VERSION}
构建日期: ${BUILD_DATE}
构建环境: Linux + Wine

版本历史:
- v${VERSION} (${BUILD_DATE})
EOF

# 创建 Windows 启动脚本
cat > "${RELEASE_NAME}/启动程序.bat" << 'EOF'
@echo off
title FaceBlur Pro
echo 启动 FaceBlur Pro...
echo.
start "" "FaceBlur-Pro.exe"
EOF

echo ""
echo "========================================"
echo "  打包完成！"
echo "========================================"
echo ""
echo "版本: v${VERSION}"
echo "构建日期: ${BUILD_DATE}"
echo "发布位置: $(pwd)/${RELEASE_NAME}/"
echo ""
echo "⚠️  重要提示："
echo "  - 这是使用 Wine 生成的 Windows 程序"
echo "  - 建议在真实 Windows 环境中测试"
echo "  - 如果有问题，请使用方案 2（GitHub Actions）"
echo ""
