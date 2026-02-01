"""Streamlit 主界面"""
import streamlit as st
import os
from io import BytesIO
from detector import FaceDetector
from processor import VideoProcessor
from utils import get_video_info, format_duration


# 自定义 CSS
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }

    /* 隐藏 Streamlit 默认的菜单和页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 标题样式 */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #e94560, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
    }

    /* 卡片容器 */
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    /* Metric 样式 */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(233, 69, 96, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    /* 侧边栏样式 */
    .css-1d391kg {
        background: rgba(22, 33, 62, 0.95) !important;
        backdrop-filter: blur(10px);
    }

    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #e94560, #ff6b6b) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(233, 69, 96, 0.4) !important;
    }

    /* 文件上传区域 */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 2px dashed rgba(233, 69, 96, 0.5) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
    }

    /* 进度条 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #e94560, #ff6b6b) !important;
    }

    /* 下载按钮 */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #4facfe, #00f2fe) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }

    /* 标签样式 */
    [data-testid="stSelectLabel"], [data-testid="stSliderLabel"] {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600 !important;
    }

    /* 分割线 */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(233, 69, 96, 0.3), transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)


# 页面配置
st.set_page_config(
    page_title="FaceBlur Pro",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题区域
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1>🎭 FaceBlur Pro</h1>
    <p style="color: rgba(255, 255, 255, 0.7); font-size: 1.1rem;">
        智能视频人脸打码工具 · 高精度检测 · 极速处理
    </p>
</div>
""", unsafe_allow_html=True)

# 侧边栏设置
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #e94560; margin: 0;">⚙️ 参数设置</h2>
    </div>
    """, unsafe_allow_html=True)

    # 打码方式选择
    st.markdown("### 🎨 打码效果")
    blur_type = st.radio(
        "选择打码效果",
        options=["🌫️ 高斯模糊", "🧊 马赛克"],
        index=0,
        label_visibility="collapsed"
    )

    blur_type_value = "gaussian" if "高斯" in blur_type else "mosaic"

    # 根据打码方式显示不同的滑块
    st.markdown("### 🎛️ 强度调节")
    if "高斯" in blur_type:
        blur_size = st.slider(
            "模糊程度",
            min_value=5,
            max_value=101,
            value=31,
            step=2,
            help="值越大，模糊效果越强"
        )
    else:
        blur_size = st.slider(
            "马赛克大小",
            min_value=5,
            max_value=50,
            value=15,
            help="值越大，马赛克块越大"
        )

    # 检测置信度
    st.markdown("### 🔍 检测精度")
    confidence = st.slider(
        "置信度阈值",
        min_value=0.1,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="值越高，检测越严格"
    )

    st.markdown("---")

    # 性能设置
    st.markdown("### ⚡ 性能优化")
    use_optimization = st.checkbox(
        "🚀 启用智能跟踪",
        value=True,
        help="大幅减少检测次数，提升速度"
    )

    detect_interval = st.slider(
        "检测间隔（帧）",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        disabled=not use_optimization,
        help="每隔多少帧重新检测，间隔越大越快"
    )

    st.markdown("---")

    # 配置摘要
    speed_multiplier = detect_interval if use_optimization else 1
    st.markdown(f"""
    <div style="background: rgba(233, 69, 96, 0.1); border: 1px solid rgba(233, 69, 96, 0.3);
         border-radius: 12px; padding: 1rem;">
        <div style="color: #e94560; font-weight: 700; font-size: 1.5rem; text-align: center;">
            预计提速 {speed_multiplier}x
        </div>
        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.85rem; text-align: center; margin-top: 0.5rem;">
            {'智能跟踪' if use_optimization else '全帧检测'} · 每 {detect_interval} 帧检测一次
        </div>
    </div>
    """, unsafe_allow_html=True)

# 主界面
col_upload, col_preview = st.columns([1, 1])

with col_upload:
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.03);
               border: 2px dashed rgba(233, 69, 96, 0.5);
               border-radius: 16px; padding: 2rem; text-align: center;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📤</div>
        <h3 style="color: #e94560; margin: 0;">上传视频</h3>
        <p style="color: rgba(255, 255, 255, 0.6);">支持 MP4, AVI, MOV, MKV</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "选择视频文件",
        type=["mp4", "avi", "mov", "mkv"],
        label_visibility="collapsed"
    )

with col_preview:
    if uploaded_file:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.03);
                   border: 1px solid rgba(255, 255, 255, 0.1);
                   border-radius: 16px; padding: 1.5rem;">
            <h3 style="color: #e94560; margin: 0 0 1rem 0;">👁️ 视频预览</h3>
        </div>
        """, unsafe_allow_html=True)
        st.video(uploaded_file)

# 处理视频
if uploaded_file is not None:
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    input_path = os.path.join("uploads", uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    video_info = get_video_info(input_path)

    # 视频信息卡片
    st.markdown("---")
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.03);
               border: 1px solid rgba(255, 255, 255, 0.1);
               border-radius: 16px; padding: 1.5rem;">
        <h3 style="color: #e94560; margin: 0 0 1rem 0;">📊 视频信息</h3>
    </div>
    """, unsafe_allow_html=True)

    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("📐 分辨率", f"{video_info['width']} x {video_info['height']}")
    with col_info2:
        st.metric("🎬 帧率", f"{video_info['fps']:.2f} FPS")
    with col_info3:
        st.metric("⏱️ 时长", format_duration(video_info['duration']))

    # 处理按钮
    st.markdown("---")
    col_btn_left, col_btn_right = st.columns([1, 4])

    with col_btn_left:
        if st.button("🚀 开始处理", type="primary", use_container_width=True):
            output_path = os.path.join("outputs", uploaded_file.name)

            # 进度显示
            progress_container = st.container()
            with progress_container:
                st.markdown("""
                <div style="background: rgba(255, 255, 255, 0.03);
                           border: 1px solid rgba(255, 255, 255, 0.1);
                           border-radius: 16px; padding: 2rem;">
                """, unsafe_allow_html=True)
                progress_bar = st.progress(0)
                status_text = st.empty()
                st.markdown("</div>", unsafe_allow_html=True)

            def progress_callback(current, total, message):
                if total > 0:
                    progress = current / total
                else:
                    progress = 0
                progress_bar.progress(progress)
                status_text.markdown(f"""
                <div style="text-align: center; color: rgba(255, 255, 255, 0.9);
                           font-size: 0.95rem; padding: 0.5rem;">
                    {message}
                </div>
                """, unsafe_allow_html=True)

            try:
                detector = FaceDetector()
                processor = VideoProcessor(
                    detector=detector,
                    use_tracking=use_optimization,
                    detect_interval=detect_interval
                )

                processor.process(
                    input_path=input_path,
                    output_path=output_path,
                    blur_type=blur_type_value,
                    blur_size=blur_size,
                    confidence_threshold=confidence,
                    progress_callback=progress_callback
                )

                # 处理完成
                progress_container.markdown("""
                <div style="background: rgba(76, 175, 80, 0.2);
                           border: 2px solid #4caf50;
                           border-radius: 16px; padding: 2rem; text-align: center;">
                    <div style="font-size: 4rem;">✅</div>
                    <h3 style="color: #4caf50; margin: 1rem 0;">处理完成！</h3>
                </div>
                """, unsafe_allow_html=True)

                # 显示结果
                st.markdown("---")
                st.markdown("""
                <div style="background: rgba(255, 255, 255, 0.03);
                           border: 1px solid rgba(255, 255, 255, 0.1);
                           border-radius: 16px; padding: 1.5rem;">
                    <h3 style="color: #e94560; margin: 0 0 1rem 0;">📥 下载结果</h3>
                </div>
                """, unsafe_allow_html=True)
                st.video(output_path)

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="💾 下载处理后的视频",
                        data=f,
                        file_name=f"blurred_{uploaded_file.name}",
                        mime="video/mp4",
                        use_container_width=True
                    )

            except Exception as e:
                st.markdown(f"""
                <div style="background: rgba(244, 67, 54, 0.2);
                           border: 2px solid #f44336;
                           border-radius: 16px; padding: 2rem; text-align: center;">
                    <div style="font-size: 4rem;">❌</div>
                    <h3 style="color: #f44336; margin: 1rem 0;">处理失败</h3>
                    <p style="color: rgba(255, 255, 255, 0.8);">{str(e)}</p>
                </div>
                """, unsafe_allow_html=True)

            if os.path.exists(input_path):
                os.remove(input_path)

# 底部
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255, 255, 255, 0.4); font-size: 0.85rem;">
    <p>FaceBlur Pro · SCRFD 高精度人脸检测 · KCF 智能跟踪</p>
</div>
""", unsafe_allow_html=True)
