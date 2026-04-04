from PIL import Image, ImageEnhance, ImageFilter


def _preprocess_image(image, group_index=None):
    """
    图像预处理
    Args:
        image: 原始图像
        group_index: OCR组索引（可选）

    Returns:
        Image: 处理后的图像
    """
    try:
        # 转换为灰度图像以提高识别率
        image = image.convert('L')

        # 添加图像预处理，提高识别精度

        # 提高对比度
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # 锐化图像
        image = image.filter(ImageFilter.SHARPEN)

        # 添加阈值处理，增强文字与背景的对比度
        image = image.point(lambda p: p > 128 and 255)

        return image
    except Exception as e:
        # 如果提供了group_index，则记录错误
        if group_index is not None:
            from modules.ocr import OCRModule
            # 注意：这里不应该直接调用app.log_message，因为这是一个工具函数
            # 应该让调用者处理异常
            pass
        return None
