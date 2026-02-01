"""Streamlit 主界面"""
import streamlit as st
import os
from io import BytesIO
from detector import FaceDetector
from processor import VideoProcessor
from utils import get_video_info, format_duration


# 页面配置
st.set_page_config(
    page_title="视频人脸打码工具",
    page_icon="🎭",
    layout="wide"
)

st.title("🎭 视频人脸打码工具")
st.markdown("---")

# 侧边栏设置
with st.sidebar:
    st.header("设置")

    # 打码方式选择
    blur_type = st.radio(
        "打码方式",
        options=["高斯模糊", "马赛克"],
        index=0,
        help="选择人脸打码的方式"
    )

    blur_type_value = "gaussian" if blur_type == "高斯模糊" else "mosaic"

    # 根据打码方式显示不同的滑块
    if blur_type == "高斯模糊":
        blur_size = st.slider(
            "模糊程度",
            min_value=5,
            max_value=101,
            value=31,
            step=2,
            help="值越大，模糊效果越强（必须是奇数）"
        )
    else:  # 马赛克
        blur_size = st.slider(
            "马赛克大小",
            min_value=5,
            max_value=50,
            value=15,
            help="值越大，马赛克块越大"
        )

    # 检测置信度
    confidence = st.slider(
        "检测敏感度",
        min_value=0.1,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="值越高，检测越严格（减少误检）"
    )

    st.markdown("---")
    st.subheader("性能优化")

    # 优化模式开关
    use_optimization = st.checkbox(
        "启用优化模式",
        value=True,
        help="使用跟踪优化，大幅提升处理速度（推荐）"
    )

    # 检测间隔
    detect_interval = st.slider(
        "检测间隔（帧）",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        disabled=not use_optimization,
        help="每隔多少帧检测一次人脸，中间使用跟踪"
    )

    st.markdown("---")
    st.markdown("### 说明")
    if use_optimization:
        st.markdown(f"""
        - **高斯模糊**: 默认方式，平滑模糊效果
        - **马赛克**: 像素块效果
        - **优化模式**: 每 {detect_interval} 帧检测一次，中间使用跟踪
        - 预计提速 5-10 倍
        - 输出视频将保留原视频的音频、分辨率和帧率
        """)
    else:
        st.markdown("""
        - **高斯模糊**: 默认方式，平滑模糊效果
        - **马赛克**: 像素块效果
        - **标准模式**: 每帧都检测，精度最高但速度较慢
        - 输出视频将保留原视频的音频、分辨率和帧率
        """)

# 主界面
col1, col2 = st.columns(2)

with col1:
    st.subheader("上传视频")
    uploaded_file = st.file_uploader(
        "选择视频文件",
        type=["mp4", "avi", "mov", "mkv"],
        help="支持 MP4, AVI, MOV, MKV 格式"
    )

with col2:
    st.subheader("视频信息")
    if uploaded_file:
        # 显示视频预览
        st.video(uploaded_file)

# 处理视频
if uploaded_file is not None:
    # 保存上传的文件
    input_path = f"temp_input_{uploaded_file.name}"
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    # 获取视频信息
    video_info = get_video_info(input_path)

    st.markdown("---")
    st.subheader("📊 视频信息")
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("分辨率", f"{video_info['width']} x {video_info['height']}")
    with col_info2:
        st.metric("帧率", f"{video_info['fps']:.2f} FPS")
    with col_info3:
        st.metric("时长", format_duration(video_info['duration']))

    # 处理按钮
    st.markdown("---")
    col_btn1, col_btn2 = st.columns([1, 4])

    with col_btn1:
        if st.button("开始处理", type="primary", use_container_width=True):
            output_path = f"output_{uploaded_file.name}"

            # 创建进度条
            progress_bar = st.progress(0, text="初始化...")
            status_text = st.empty()

            # 进度回调函数
            def progress_callback(current, total, message):
                if total > 0:
                    progress = current / total
                else:
                    progress = 0
                progress_bar.progress(progress)
                status_text.text(message)

            try:
                # 处理视频
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
                st.success("✅ 处理完成！")
                progress_bar.progress(1.0)
                status_text.text("完成!")

                # 显示结果
                st.markdown("---")
                st.subheader("📤 下载结果")
                st.video(output_path)

                # 提供下载
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="下载处理后的视频",
                        data=f,
                        file_name=f"blurred_{uploaded_file.name}",
                        mime="video/mp4",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ 处理失败: {str(e)}")

            # 清理临时文件
            if os.path.exists(input_path):
                os.remove(input_path)
