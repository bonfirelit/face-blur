# FaceBlur Pro 打包说明

## 文件夹结构

```
build/
├── build.spec           # PyInstaller 配置文件
├── build_windows.bat    # Windows 打包脚本
├── build_linux.sh       # Linux 打包脚本
├── README_打包说明.md    # 本文件
└── release/             # 打包后的发布文件（生成后）
    ├── FaceBlur-Pro.exe # 主程序（Windows）
    ├── 启动程序.bat      # 启动脚本
    └── README.md        # 用户说明
```

## 使用步骤

### Windows 下打包

1. **准备环境**
   - 安装 Python 3.9 或更高版本
   - 确保 Python 已添加到系统 PATH

2. **运行打包脚本**
   ```cmd
   cd build
   build_windows.bat
   ```

3. **获取发布文件**
   - 打包完成后，`release` 文件夹包含所有需要分发的文件
   - 将整个 `release` 文件夹压缩成 ZIP 分发给用户

### Linux 下打包

1. **运行打包脚本**
   ```bash
   cd build
   chmod +x build_linux.sh
   ./build_linux.sh
   ```

## 用户使用说明

### Windows 用户

1. 解压下载的 ZIP 文件
2. 双击 `启动程序.bat`
3. 浏览器会自动打开界面

### Linux 用户

1. 解压下载的 ZIP 文件
2. 在终端执行：
   ```bash
   cd 解压目录
   ./启动程序.sh
   ```

## 注意事项

### 模型文件问题

InsightFace 首次运行时会自动下载模型文件到用户目录：
- Windows: `C:\Users\用户名\.insightface\models\`
- Linux: `~/.insightface/models/`

**建议：** 让应用首次运行时自动下载，或预先打包模型文件

### 打包大小

- 预计打包后大小：**200-400 MB**
- 主要占用：OpenCV、ONNX Runtime、InsightFace

### 兼容性

- 支持 Windows 7/10/11（64位）
- 支持主流 Linux 发行版

### 已排除的依赖

为减小体积，已排除以下不需要的库：
- tkinter
- matplotlib
- scipy
- pandas
- test
- unittest

如果后续需要这些库，请修改 `build.spec` 中的 `excludes` 列表

## 常见问题

### Q: 打包失败，提示找不到模块
A: 在 `build.spec` 的 `hiddenimports` 中添加缺失的模块

### Q: 运行时提示缺少 DLL
A: 某些依赖需要手动复制 DLL 文件，检查 `build.spec` 的 `binaries` 配置

### Q: 程序运行很慢
A: 首次运行会解压临时文件，后续运行会快很多

### Q: 能否打包成单文件？
A: 当前配置已经是单文件模式（`onefile`），所有内容打包进一个 EXE

## 进阶优化

### 减小体积

1. 使用 UPX 压缩（已启用）
2. 排除更多不需要的依赖
3. 使用 `--strip` 去除符号表（已启用）

### 添加图标

1. 准备一个 `.ico` 文件（Windows）或 `.png`（Linux）
2. 修改 `build.spec` 中的 `icon='icon.ico'`

### 隐藏控制台窗口

如果不想显示控制台，修改 `build.spec`：
```python
console=False,
```

注意：隐藏控制台后，将无法看到错误信息，调试时建议开启。
