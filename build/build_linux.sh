#!/bin/bash
# ========================================
# FaceBlur Pro Linux 打包脚本
# ========================================

# 设置版本号（修改这里来发布新版本）
VERSION="1.0.0"

# 使用日期作为构建号
BUILD_DATE=$(date +%Y%m%d)

RELEASE_NAME="FaceBlur-Pro-v${VERSION}-${BUILD_DATE}"

echo "========================================"
echo "  FaceBlur Pro 打包工具 v${VERSION}"
echo "  构建日期: ${BUILD_DATE}"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装"
    exit 1
fi

echo "[1/5] 检查 Python 环境..."
python3 --version

echo ""
echo "[2/5] 安装 PyInstaller..."
pip3 install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ""
echo "[3/5] 安装项目依赖..."
pip3 install -r ../requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ""
echo "[4/5] 开始打包 (这可能需要几分钟)..."
pyinstaller build.spec

echo ""
echo "[5/5] 复制文件到发布目录..."
mkdir -p "${RELEASE_NAME}"
cp dist/FaceBlur-Pro "${RELEASE_NAME}/"
cp release_template/README_用户使用说明.md "${RELEASE_NAME}/使用说明.md" 2>/dev/null || true

# 创建版本信息文件
cat > "${RELEASE_NAME}/版本信息.txt" << EOF
FaceBlur Pro v${VERSION}
构建日期: ${BUILD_DATE}

版本历史:
- v${VERSION} (${BUILD_DATE})
EOF

# 创建启动脚本
cat > "${RELEASE_NAME}/启动程序.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "启动 FaceBlur Pro..."
echo ""
./FaceBlur-Pro
EOF

chmod +x "${RELEASE_NAME}/启动程序.sh"
chmod +x "${RELEASE_NAME}/FaceBlur-Pro"

echo ""
echo "========================================"
echo "  打包完成！"
echo "========================================"
echo ""
echo "版本: v${VERSION}"
echo "构建日期: ${BUILD_DATE}"
echo "发布文件位置: $(pwd)/${RELEASE_NAME}/"
echo ""
echo "下一步:"
echo "1. 将 ${RELEASE_NAME} 文件夹压缩成 ZIP"
echo "2. 分发给用户"
echo "3. 用户解压后执行 ./启动程序.sh 即可使用"
echo ""
