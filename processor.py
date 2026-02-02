"""视频处理器模块"""
import cv2
import subprocess
import os
import numpy as np
from tqdm import tqdm
from detector import FaceDetector
from blur_effects import create_blur_effect


class KalmanFaceTracker:
    """带卡尔曼滤波预测的人脸跟踪器"""

    def __init__(self, tracker_type='KCF'):
        """
        初始化跟踪器

        Args:
            tracker_type: 跟踪器类型 ('KCF', 'CSRT', 'MOSSE')
        """
        self.tracker_type = tracker_type
        self.tracker = None
        self.bbox = None
        self.is_initialized = False

        # 初始化卡尔曼滤波器
        # 状态向量: [x, y, vx, vy, w, h]
        # x, y: 人脸框中心坐标
        # vx, vy: 速度
        # w, h: 人脸框宽高
        self.kalman = cv2.KalmanFilter(6, 4)

        # 状态转移矩阵 (匀速运动模型)
        self.kalman.transitionMatrix = np.array([
            [1, 0, 1, 0, 0, 0],  # x = x + vx
            [0, 1, 0, 1, 0, 0],  # y = y + vy
            [0, 0, 1, 0, 0, 0],  # vx = vx
            [0, 0, 0, 1, 0, 0],  # vy = vy
            [0, 0, 0, 0, 1, 0],  # w = w
            [0, 0, 0, 0, 0, 1],  # h = h
        ], dtype=np.float32)

        # 测量矩阵 (测量 x, y, w, h)
        self.kalman.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0],  # 测量 x
            [0, 1, 0, 0, 0, 0],  # 测量 y
            [0, 0, 0, 0, 1, 0],  # 测量 w
            [0, 0, 0, 0, 0, 1],  # 测量 h
        ], dtype=np.float32)

        # 过程噪声协方差
        self.kalman.processNoiseCov = np.eye(6, dtype=np.float32) * 0.03

        # 测量噪声协方差
        self.kalman.measurementNoiseCov = np.eye(4, dtype=np.float32) * 0.1

        # 初始误差协方差
        self.kalman.errorCovPost = np.eye(6, dtype=np.float32) * 1

    def init(self, frame, bbox):
        """
        初始化跟踪器

        Args:
            frame: 当前帧
            bbox: 边界框 (x, y, w, h)
        """
        self.bbox = bbox

        # 初始化 KCF 跟踪器
        if self.tracker_type == 'KCF':
            self.tracker = cv2.TrackerKCF.create()
        elif self.tracker_type == 'CSRT':
            self.tracker = cv2.TrackerCSRT.create()
        elif self.tracker_type == 'MOSSE':
            self.tracker = cv2.TrackerMOSSE.create()
        else:
            self.tracker = cv2.TrackerKCF.create()

        self.tracker.init(frame, bbox)

        # 初始化卡尔曼滤波器状态
        x, y, w, h = bbox
        center_x = x + w / 2
        center_y = y + h / 2

        # 初始状态: [x, y, vx, vy, w, h]
        self.kalman.statePost = np.array([
            [center_x],
            [center_y],
            [0],  # 初始速度为0
            [0],
            [w],
            [h]
        ], dtype=np.float32)

        self.is_initialized = True

    def update(self, frame):
        """
        更新跟踪

        Returns:
            (success, bbox): 是否成功，边界框 (x, y, w, h)
        """
        if not self.is_initialized or self.tracker is None:
            return False, None

        # 预测阶段
        predicted = self.kalman.predict()

        # 尝试跟踪
        success, bbox = self.tracker.update(frame)

        if success:
            # 跟踪成功，用跟踪结果校正卡尔曼滤波器
            x, y, w, h = bbox
            center_x = x + w / 2
            center_y = y + h / 2

            # 测量向量: [x, y, w, h]
            measurement = np.array([
                [center_x],
                [center_y],
                [w],
                [h]
            ], dtype=np.float32)

            # 校正
            self.kalman.correct(measurement)
            self.bbox = bbox
            return True, bbox
        else:
            # 跟踪失败，使用卡尔曼滤波器预测
            pred_x = predicted[0, 0]
            pred_y = predicted[1, 0]
            pred_w = predicted[4, 0]
            pred_h = predicted[5, 0]

            # 转换为 x, y, w, h 格式
            pred_bbox = (
                pred_x - pred_w / 2,
                pred_y - pred_h / 2,
                pred_w,
                pred_h
            )

            self.bbox = tuple(map(float, pred_bbox))

            # 只有当预测结果合理时才返回成功
            if pred_w > 10 and pred_h > 10:
                return True, pred_bbox
            else:
                return False, None


class FaceTracker:
    """人脸跟踪器封装"""

    def __init__(self, tracker_type='KCF'):
        """
        初始化跟踪器

        Args:
            tracker_type: 跟踪器类型 ('KCF', 'CSRT', 'MOSSE')
        """
        self.tracker_type = tracker_type
        self.tracker = None
        self.bbox = None
        self.is_initialized = False

    def init(self, frame, bbox):
        """初始化跟踪器"""
        self.bbox = bbox
        if self.tracker_type == 'KCF':
            self.tracker = cv2.TrackerKCF.create()
        elif self.tracker_type == 'CSRT':
            self.tracker = cv2.TrackerCSRT.create()
        elif self.tracker_type == 'MOSSE':
            self.tracker = cv2.TrackerMOSSE.create()
        else:
            self.tracker = cv2.TrackerKCF.create()

        self.tracker.init(frame, bbox)
        self.is_initialized = True

    def update(self, frame):
        """更新跟踪"""
        if not self.is_initialized or self.tracker is None:
            return False, None

        success, bbox = self.tracker.update(frame)
        if success:
            self.bbox = bbox
        return success, bbox


class VideoProcessor:
    """视频处理器"""

    def __init__(self, detector=None, use_tracking=True, detect_interval=5):
        """
        初始化视频处理器

        Args:
            detector: FaceDetector 实例，如果为 None 则创建默认检测器
            use_tracking: 是否使用跟踪优化
            detect_interval: 检测间隔（每隔多少帧检测一次）
        """
        self.detector = detector or FaceDetector()
        self.use_tracking = use_tracking
        self.detect_interval = detect_interval
        self.trackers = []

    def _apply_blur_to_faces(self, frame, bboxes, blur_effect, mask_scale=1.0):
        """
        对帧中的人脸区域应用打码效果

        Args:
            frame: 输入帧
            bboxes: 人脸边界框列表 [[x1, y1, x2, y2], ...] 或 (x, y, w, h) 格式
            blur_effect: 打码效果对象
            mask_scale: 遮罩缩放比例

        Returns:
            处理后的帧
        """
        for bbox in bboxes:
            # 处理不同格式
            if len(bbox) == 4:
                if bbox[2] > bbox[0] and bbox[2] - bbox[0] < bbox[2]:  # x1,y1,x2,y2
                    x1, y1, x2, y2 = map(int, bbox)
                else:  # x,y,w,h
                    x, y, w, h = map(int, bbox)
                    x1, y1, x2, y2 = x, y, x + w, y + h

            # 根据 mask_scale 扩大人脸框
            w_box = x2 - x1
            h_box = y2 - y1
            x1 = max(0, int(x1 - (w_box * (mask_scale - 1) / 2)))
            y1 = max(0, int(y1 - (h_box * (mask_scale - 1) / 2)))
            x2 = min(frame.shape[1], int(x2 + (w_box * (mask_scale - 1) / 2)))
            y2 = min(frame.shape[0], int(y2 + (h_box * (mask_scale - 1) / 2)))

            if x2 <= x1 or y2 <= y1:
                continue

            # 提取人脸区域
            face_region = frame[y1:y2, x1:x2]

            # 应用椭圆遮罩的打码效果
            blurred = blur_effect.apply_ellipse(face_region)

            # 写回原帧
            frame[y1:y2, x1:x2] = blurred

        return frame

    def _update_trackers(self, frame):
        """更新所有跟踪器"""
        active_trackers = []
        bboxes = []

        for tracker in self.trackers:
            success, bbox = tracker.update(frame)
            if success:
                # 转换为 x1,y1,x2,y2 格式
                x, y, w, h = bbox
                x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)

                # 检查边界框是否有效
                h_img, w_img = frame.shape[:2]
                if x1 >= 0 and y1 >= 0 and x2 <= w_img and y2 <= h_img and x2 > x1 and y2 > y1:
                    active_trackers.append(tracker)
                    bboxes.append([x1, y1, x2, y2])

        self.trackers = active_trackers
        return bboxes

    def _initialize_trackers(self, frame, bboxes):
        """用新检测到的人脸初始化跟踪器"""
        self.trackers = []
        use_kalman = self.detect_interval >= 5  # 检测间隔>=5时启用卡尔曼滤波

        for bbox in bboxes:
            if use_kalman:
                tracker = KalmanFaceTracker(tracker_type='KCF')
            else:
                tracker = FaceTracker(tracker_type='KCF')

            # 转换为 x,y,w,h 格式
            x1, y1, x2, y2 = bbox
            tracker.init(frame, (x1, y1, x2 - x1, y2 - y1))
            self.trackers.append(tracker)

    def _merge_audio(self, video_path, audio_path, output_path):
        """
        使用 ffmpeg 合并视频和音频

        Args:
            video_path: 无音频的视频路径
            audio_path: 原视频路径（含音频）
            output_path: 输出路径
        """
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-map', '0:v:0',
            '-map', '1:a?',
            '-y',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg error: {e.stderr.decode()}")
            raise
        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg not found. Please install ffmpeg:\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  macOS: brew install ffmpeg\n"
                "  Windows: Download ffmpeg.exe and add to PATH"
            )

    def process(
        self,
        input_path,
        output_path,
        blur_type='gaussian',
        blur_size=31,
        mask_scale=1.0,
        confidence_threshold=0.5,
        progress_callback=None
    ):
        """
        处理视频

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            blur_type: 打码类型 ('gaussian', 'mosaic')
            blur_size: 打码大小（高斯模糊核大小或马赛克块大小）
            mask_scale: 遮罩形状调整，1.0为标准椭圆
            confidence_threshold: 人脸检测置信度阈值
            progress_callback: 进度回调函数 callback(current, total, message)
        """
        # 加载人脸检测模型
        if progress_callback:
            progress_callback(0, 0, "加载人脸检测模型...")
        self.detector.load_model()

        # 打开视频文件
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {input_path}")

        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 创建打码效果
        blur_effect = create_blur_effect(blur_type, blur_size, mask_scale)

        # 创建临时视频文件（无音频）
        temp_video_path = "temp_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

        # 逐帧处理
        if progress_callback:
            progress_callback(0, total_frames, "开始处理视频...")

        # 构建处理模式信息
        if self.use_tracking:
            if self.detect_interval >= 5:
                process_mode = f"智能跟踪+轨迹预测 (每{self.detect_interval}帧检测)"
            else:
                process_mode = f"智能跟踪 (每{self.detect_interval}帧检测)"
        else:
            process_mode = "标准模式 (每帧检测)"

        # 逐帧处理
        for frame_idx in tqdm(range(total_frames), desc="Processing video"):
            ret, frame = cap.read()
            if not ret:
                break

            # 判断是否需要检测
            need_detect = False
            if self.use_tracking:
                if frame_idx == 0:
                    need_detect = True
                elif frame_idx % self.detect_interval == 0:
                    need_detect = True
                elif len(self.trackers) == 0:
                    need_detect = True
            else:
                need_detect = True

            # 检测或跟踪人脸
            if need_detect:
                bboxes = self.detector.detect(frame, confidence_threshold)
                self._initialize_trackers(frame, bboxes)
            else:
                bboxes = self._update_trackers(frame)

            # 应用打码
            frame = self._apply_blur_to_faces(frame, bboxes, blur_effect, mask_scale)

            # 写入输出
            out.write(frame)

            # 进度回调
            if progress_callback and frame_idx % 10 == 0:
                progress_callback(frame_idx, total_frames, f"{process_mode}... {frame_idx}/{total_frames}")

        # 清理
        cap.release()
        out.release()

        # 合并音频
        if progress_callback:
            progress_callback(total_frames, total_frames, "合并音频...")

        self._merge_audio(temp_video_path, input_path, output_path)

        # 删除临时文件
        os.remove(temp_video_path)

        if progress_callback:
            progress_callback(total_frames, total_frames, "完成!")

        return output_path
