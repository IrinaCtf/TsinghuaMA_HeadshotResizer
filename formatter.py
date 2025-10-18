# requirements: pip install pillow
import io
import os
from PIL import Image

TARGET_W, TARGET_H = 150, 200
MAX_BYTES = 50 * 1024

def resize_to_target_cover(img: Image.Image, w=TARGET_W, h=TARGET_H) -> Image.Image:
    """等比放大后居中裁剪到 w×h（不变形）。"""
    src_w, src_h = img.size
    scale = max(w / src_w, h / src_h)
    new_size = (int(src_w * scale), int(src_h * scale))
    img_resized = img.resize(new_size, Image.LANCZOS)
    # 居中裁剪
    left = (img_resized.width - w) // 2
    top = (img_resized.height - h) // 2
    return img_resized.crop((left, top, left + w, top + h))

def resize_to_target_contain(img: Image.Image, w=TARGET_W, h=TARGET_H, bg=(255,255,255)) -> Image.Image:
    """等比缩放后“留白填充”（contain），不裁剪主体；但会有边框。"""
    canvas = Image.new("RGB", (w, h), color=bg)
    src_w, src_h = img.size
    scale = min(w / src_w, h / src_h)
    new_size = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
    img_resized = img.resize(new_size, Image.LANCZOS)
    x = (w - img_resized.width) // 2
    y = (h - img_resized.height) // 2
    canvas.paste(img_resized, (x, y))
    return canvas

def save_jpg_under_size(img: Image.Image, out_path: str, max_bytes=MAX_BYTES) -> None:
    """用二分搜索 JPEG 质量，在不超过 max_bytes 的前提下尽量保真。"""
    # 注意：设置 subsampling=2（4:2:0），optimize/progressive 有助减小体积
    lo, hi = 15, 95
    best_bytes = None
    best_buf = None

    while lo <= hi:
        q = (lo + hi) // 2
        buf = io.BytesIO()
        img.save(
            buf, format="JPEG", quality=q, optimize=True, progressive=True,
            subsampling=2
        )
        size = buf.tell()
        # print(f"try q={q}, {size} bytes")
        if size <= max_bytes:
            best_bytes = size
            best_buf = buf
            lo = q + 1  # 试更高质量
        else:
            hi = q - 1  # 降低质量

    if best_buf is None:
        # 质量 15 仍然超限，再降一点做兜底
        q = 10
        best_buf = io.BytesIO()
        img.save(
            best_buf, format="JPEG", quality=q, optimize=True, progressive=True,
            subsampling=2
        )
        best_bytes = best_buf.tell()

    with open(out_path, "wb") as f:
        f.write(best_buf.getvalue())
    print(f"Saved: {out_path} ({best_bytes} bytes)")

def process_image(input_path: str, output_path: str, mode: str = "cover"):
    """
    mode:
      - 'cover'  : 等比放大后居中裁剪到 150×200（默认，适合证件照/不怕四周略裁）。
      - 'contain': 等比缩放并留白填充到 150×200（不裁主体，四周可能有白边）。
    """
    with Image.open(input_path) as im:
        # 统一转为 RGB（去 Alpha）
        im = im.convert("RGB")
        if mode == "contain":
            im_out = resize_to_target_contain(im, TARGET_W, TARGET_H)
        else:
            im_out = resize_to_target_cover(im, TARGET_W, TARGET_H)
        save_jpg_under_size(im_out, output_path, MAX_BYTES)

if __name__ == "__main__":
    # 用法示例（把 input.jpg 处理为 out.jpg）：
    # python script.py
    in_path = "input.jpg"   # 改成你的输入图片路径（任意格式都可）
    out_path = "out.jpg"    # 输出 JPG
    process_image(in_path, out_path, mode="cover")
