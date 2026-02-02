# Linux → Windows 交叉打包指南

## 问题说明

PyInstaller 生成的可执行文件是**平台特定**的：
- Linux 上打包 → Linux 可执行文件（不能在 Windows 运行）
- Windows 上打包 → Windows 可执行文件（不能在 Linux 运行）

要从 Linux 打包 Windows 程序，有以下方案：

---

## 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **GitHub Actions** | 免费、稳定、真正的 Windows 环境 | 需要推送代码到 GitHub | ⭐⭐⭐⭐⭐ |
| **Wine** | 本地完成，不需要外部服务 | 可能有问题、配置复杂 | ⭐⭐⭐ |
| **虚拟机** | 完全控制 | 占用资源大、需要 Windows 许可证 | ⭐⭐⭐ |
| **找 Windows 电脑** | 最简单 | 需要额外设备 | ⭐⭐⭐⭐ |

---

## 方案 1：GitHub Actions（推荐）

### 优点
- ✅ 完全免费
- ✅ 真正的 Windows 环境
- ✅ 可以在 Linux 上触发
- ✅ 自动生成下载链接

### 使用步骤

#### 1. 推送代码到 GitHub

```bash
cd /home/toge/workspace/fb
git init
git add .
git commit -m "Initial commit"

# 创建 GitHub 仓库后
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin master
```

#### 2. 配置 GitHub Actions

将 `.github/workflows/build-windows.yml` 复制到你的仓库根目录：

```bash
mkdir -p .github/workflows
cp build/.github/workflows/build-windows.yml .github/workflows/
```

#### 3. 触发构建

1. 打开 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 选择 **Build Windows Package** 工作流
4. 点击 **Run workflow**
5. 输入版本号（如 `1.0.0`）
6. 点击 **Run workflow** 开始构建

#### 4. 下载构建产物

1. 等待构建完成（约 5-10 分钟）
2. 进入 Actions 页面的构建记录
3. 滚动到底部 **Artifacts** 区域
4. 下载 `windows-package` ZIP 文件
5. 解压后就是可分发的 Windows 程序

### 图示流程

```
你在 Linux 上修改代码
        ↓
    git push
        ↓
GitHub 仓库
        ↓
点击 Actions → Run workflow
        ↓
GitHub 的 Windows 服务器自动打包
        ↓
下载 ZIP → 分发给用户
```

---

## 方案 2：使用 Wine（本地打包）

### 步骤

#### 1. 安装 Wine

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install wine

# 验证安装
wine --version
```

#### 2. 运行打包脚本

```bash
cd build
./build_with_wine.sh
```

#### 3. 获取发布包

```bash
# 打包完成后
ls FaceBlur-Pro-v*/
```

### Wine 方案的局限性

⚠️ **可能出现的问题：**
- OpenCV 的某些 DLL 可能不兼容
- InsightFace 的模型加载可能有问题
- GUI 应用可能无法正常显示

✅ **适合的情况：**
- 命令行程序
- 纯计算类应用
- 没有复杂 GUI 的应用

**你的项目使用 Streamlit（Web GUI），Wine 方案可能不稳定，建议使用 GitHub Actions。**

---

## 方案 3：使用虚拟机

### 步骤

#### 1. 在 Linux 上安装 Windows 虚拟机

```bash
# 安装 VirtualBox
sudo apt install virtualbox

# 下载 Windows 10 ISO（从微软官网）
# 创建虚拟机并安装 Windows
```

#### 2. 在虚拟机中打包

1. 将项目文件复制到虚拟机
2. 在虚拟机中安装 Python
3. 运行 `build_windows.bat`

---

## 方案 4：使用真实 Windows 电脑

如果身边有 Windows 电脑：
1. U 盘复制项目文件
2. 双击 `build_windows.bat`
3. 完成

---

## 推荐方案总结

```
┌──────────────────────────────────────────────────────┐
│                    选择建议                           │
├──────────────────────────────────────────────────────┤
│                                                      │
│  有 GitHub 账号？                                    │
│  ├─ 是 → 使用 GitHub Actions（方案 1）               │
│  │        最稳定、完全免费、自动化                    │
│  │                                                    │
│  └─ 否 → 可以：                                       │
│      1. 注册 GitHub 账号（5 分钟）                   │
│      2. 或使用 Wine（方案 2，可能有问题）             │
│      3. 或借用 Windows 电脑（方案 4）                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 快速开始（推荐流程）

### 第一次使用 GitHub Actions

```bash
# 1. 在 GitHub 创建新仓库（比如叫 faceblur-pro）

# 2. 在项目目录初始化 Git
cd /home/toge/workspace/fb
git init
git add .
git commit -m "Ready for build"

# 3. 推送到 GitHub
git remote add origin https://github.com/你的用户名/faceblur-pro.git
git branch -M master
git push -u origin master

# 4. 把 GitHub Actions 文件复制到正确位置
mkdir -p .github/workflows
cp build/.github/workflows/build-windows.yml .github/workflows/
git add .github/workflows/build-windows.yml
git commit -m "Add GitHub Actions workflow"
git push

# 5. 打开 GitHub 仓库页面，点击 Actions → Run workflow
```

### 后续更新代码后

```bash
# 修改代码
# ...

# 推送更新
git add .
git commit -m "Update code"
git push

# 打开 GitHub Actions 页面，点击 Run workflow
# 输入新版本号（如 1.0.1）
# 下载新的构建产物
```

---

## 常见问题

### Q: GitHub Actions 免费吗？
A: 是的，公开仓库完全免费。私有仓库每月有 2000 分钟免费额度。

### Q: 构建需要多久？
A: 通常 5-10 分钟，主要是下载依赖的时间。

### Q: 能自动构建吗？
A: 可以修改 workflow 配置为 `push` 触发，每次推送代码自动构建。

### Q: Wine 方案不能用吗？
A: 可以尝试，但你的项目使用 Streamlit（Web 界面），Wine 可能无法正确启动浏览器。GitHub Actions 更可靠。
