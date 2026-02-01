"""打码效果实现模块"""
import cv2
import numpy as np


class BlurEffect:
    """打码效果基类"""

    def __init__(self, blur_type='gaussian', size=31):
        self.blur_type = blur_type
        self.size = size

    def apply(self, region):
        """对指定区域应用打码效果"""
        raise NotImplementedError


class GaussianBlur(BlurEffect):
    """高斯模糊效果"""

    def __init__(self, kernel_size=31, sigma=None):
        super().__init__(blur_type='gaussian', size=kernel_size)
        self.kernel_size = max(1, kernel_size | 1)  # 确保是奇数
        self.sigma = sigma if sigma is not None else self.kernel_size // 3

    def apply(self, region):
        """应用高斯模糊"""
        return cv2.GaussianBlur(region, (self.kernel_size, self.kernel_size), self.sigma)


class MosaicBlur(BlurEffect):
    """马赛克效果"""

    def __init__(self, block_size=15):
        super().__init__(blur_type='mosaic', size=block_size)
        self.block_size = max(1, int(block_size))

    def apply(self, region):
        """应用马赛克效果"""
        h, w = region.shape[:2]
        # 缩小再放大实现马赛克
        small_w = max(1, w // self.block_size)
        small_h = max(1, h // self.block_size)
        small = cv2.resize(region, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
        mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        return mosaic


def create_blur_effect(blur_type='gaussian', size=31):
    """工厂函数：创建打码效果对象"""
    if blur_type == 'gaussian':
        return GaussianBlur(kernel_size=size)
    elif blur_type == 'mosaic':
        return MosaicBlur(block_size=size)
    else:
        raise ValueError(f"Unknown blur type: {blur_type}")
