from fastapi import APIRouter, UploadFile, File, Response, HTTPException, Form
from PIL import Image
import io
import tempfile
import os

router = APIRouter()


def apply_dithering(image):
    """
    誤差拡散法（Floyd–Steinberg）を用いて、画像をカスタムパレットに変換します。
    電子ペーパーで利用可能な色は、red, green, blue, yellow, black, white です。
    """
    custom_palette = [
        255,
        0,
        0,  # red
        0,
        255,
        0,  # green
        0,
        0,
        255,  # blue
        255,
        255,
        0,  # yellow
        0,
        0,
        0,  # black
        255,
        255,
        255,  # white
    ]
    custom_palette.extend([0] * (768 - len(custom_palette)))
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(custom_palette)
    dithered = image.convert("RGB").convert(
        "P", palette=palette_image, dither=Image.FLOYDSTEINBERG
    )
    return dithered.convert("RGB")


# 一時ファイルのパス（本番運用ではユーザーごとに分けるべき）
TEMP_IMAGE_PATH = os.path.join(tempfile.gettempdir(), "epaper_last.bmp")


@router.post("/process")
async def process_image(
    image: UploadFile = File(...), width: int = Form(...), height: int = Form(...)
):
    if width <= 0 or height <= 0:
        raise HTTPException(
            status_code=400, detail="幅と高さは正の整数である必要があります"
        )

    try:
        contents = await image.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")  # RGBに変換しておく
    except Exception:
        raise HTTPException(status_code=400, detail="画像の読み込みに失敗しました")

    original_width, original_height = img.size
    target_width, target_height = width, height
    target_aspect_ratio = target_width / target_height

    # 回転判定 (アスペクト比が逆転する場合)
    rotate = False
    if (original_width > original_height and target_width < target_height) or (
        original_width < original_height and target_width > target_height
    ):
        rotate = True

    if rotate:
        img = img.rotate(90, expand=True)
        original_width, original_height = img.size  # 回転後のサイズ

    # アスペクト比を維持してリサイズ (指定解像度に収まるように)
    img_aspect_ratio = original_width / original_height

    if img_aspect_ratio > target_aspect_ratio:
        # 画像の方が横長 -> 高さに合わせる
        new_height = target_height
        new_width = int(new_height * img_aspect_ratio)
    else:
        # 画像の方が縦長または同じ -> 幅に合わせる
        new_width = target_width
        new_height = int(new_width / img_aspect_ratio)

    # Pillowのresizeメソッドを使用 (thumbnailはインプレース変更のため避ける)
    # Image.LANCZOS は高品質なリサイズフィルタ
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)

    # 中央からトリミング
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = (new_width + target_width) / 2
    bottom = (new_height + target_height) / 2
    img_cropped = img_resized.crop((left, top, right, bottom))

    # 誤差拡散
    dithered = apply_dithering(img_cropped)

    buf = io.BytesIO()
    dithered.save(buf, format="BMP")
    buf.seek(0)
    # 一時ファイルにも保存
    with open(TEMP_IMAGE_PATH, "wb") as f:
        f.write(buf.getbuffer())
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/bmp")
