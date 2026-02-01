"""人脸检测模块"""
import numpy as np
from insightface.app import FaceAnalysis


class FaceDetector:
    """人脸检测器封装"""

    def __init__(self, det_name='SCRFD_500M', providers=['CPUExecutionProvider']):
        """
        初始化人脸检测器

        Args:
            det_name: 检测模型名称 ('SCRFD_500M', 'SCRFD_1G', 'SCRFD_2G')
            providers: onnxruntime 执行提供者
        """
        self.det_name = det_name
        self.providers = providers
        self.app = None

    def load_model(self):
        """加载模型"""
        if self.app is None:
            self.app = FaceAnalysis(
                det_name=self.det_name,
                providers=self.providers
            )
            self.app.prepare(ctx_id=-1, det_size=(640, 640))

    def detect(self, frame, confidence_threshold=0.5):
        """
        检测人脸

        Args:
            frame: 输入图像帧
            confidence_threshold: 置信度阈值

        Returns:
            list: 人脸边界框列表，每个元素为 [x1, y1, x2, y2]
        """
        if self.app is None:
            self.load_model()

        faces = self.app.get(frame)

        bboxes = []
        for face in faces:
            if face.det_score < confidence_threshold:
                continue
            bbox = face.bbox.astype(int)
            # 边界框格式: [x1, y1, x2, y2]
            bboxes.append(bbox)

        return bboxes

    def detect_with_progress(self, frame, progress_callback=None, **kwargs):
        """
        带进度回调的人脸检测

        Args:
            frame: 输入图像帧
            progress_callback: 进度回调函数
            **kwargs: 传递给 detect 的其他参数

        Returns:
            list: 人脸边界框列表
        """
        if progress_callback:
            progress_callback("正在检测人脸...")
        return self.detect(frame, **kwargs)
