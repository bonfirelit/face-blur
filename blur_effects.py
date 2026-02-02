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

    def __init__(self, kernel_size=31, sigma=None, mask_scale=1.0):
        super().__init__(blur_type='gaussian', size=kernel_size)
        self.kernel_size = max(1, kernel_size | 1)  # 确保是奇数
        self.sigma = sigma if sigma is not None else self.kernel_size // 3
        self.mask_scale = max(1.0, mask_scale)

    def apply(self, region):
        """应用高斯模糊"""
        return cv2.GaussianBlur(region, (self.kernel_size, self.kernel_size), self.sigma)

    def apply_ellipse(self, region):
        """应用椭圆遮罩的高斯模糊"""
        h, w = region.shape[:2]

        # 创建椭圆遮罩（椭圆大小由传入的 region 决定，这里不再缩放）
        center_x, center_y = w // 2, h // 2
        axes_x = w // 2 - 2
        axes_y = h // 2 - 2
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(mask, (center_x, center_y), (axes_x, axes_y), 0, 0, 360, 255, -1)

        # 应用高斯模糊
        blurred = cv2.GaussianBlur(region, (self.kernel_size, self.kernel_size), self.sigma)

        # 使用遮罩混合
        mask_float = mask.astype(np.float32) / 255.0
        if len(region.shape) == 3:
            mask_float = cv2.merge([mask_float] * 3)

        result = (region * (1 - mask_float) + blurred * mask_float).astype(np.uint8)

        return result


class MosaicBlur(BlurEffect):
    """马赛克效果"""

    def __init__(self, block_size=15, mask_scale=1.0):
        super().__init__(blur_type='mosaic', size=block_size)
        self.block_size = max(1, int(block_size))
        self.mask_scale = max(1.0, mask_scale)

    def apply(self, region):
        """应用马赛克效果"""
        h, w = region.shape[:2]
        # 缩小再放大实现马赛克
        small_w = max(1, w // self.block_size)
        small_h = max(1, h // self.block_size)
        small = cv2.resize(region, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
        mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        return mosaic

    def apply_ellipse(self, region):
        """应用椭圆遮罩的马赛克效果（椭圆外应用模糊）"""
        h, w = region.shape[:2]

        # 创建椭圆遮罩（椭圆大小由传入的 region 决定，这里不再缩放）
        center_x, center_y = w // 2, h // 2
        axes_x = w // 2 - 2
        axes_y = h // 2 - 2
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(mask, (center_x, center_y), (axes_x, axes_y), 0, 0, 360, 255, -1)

        # 应用马赛克（椭圆内）
        small_w = max(1, w // self.block_size)
        small_h = max(1, h // self.block_size)
        small = cv2.resize(region, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
        mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

        # 椭圆外应用高斯模糊
        kernel_size = max(3, self.block_size | 1)
        blurred = cv2.GaussianBlur(region, (kernel_size, kernel_size), kernel_size // 3)

        # 使用遮罩混合：椭圆内马赛克，椭圆外模糊
        mask_float = mask.astype(np.float32) / 255.0
        if len(region.shape) == 3:
            mask_float = cv2.merge([mask_float] * 3)

        result = (blurred * (1 - mask_float) + mosaic * mask_float).astype(np.uint8)

        return result


def create_blur_effect(blur_type='gaussian', size=31, mask_scale=1.0):
    """工厂函数：创建打码效果对象"""
    if blur_type == 'gaussian':
        return GaussianBlur(kernel_size=size, mask_scale=mask_scale)
    elif blur_type == 'mosaic':
        return MosaicBlur(block_size=size, mask_scale=mask_scale)
    else:
        raise ValueError(f"Unknown blur type: {blur_type}")
