from fastapi import APIRouter, UploadFile, File, Response, HTTPException, Form
from PIL import Image, ImageOps, ImageEnhance
import io

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
    # 誤差拡散法(Floyd–Steinberg)を利用してパレット変換
    dithered = image.convert("RGB").convert(
        "P", palette=palette_image, dither=Image.FLOYDSTEINBERG
    )
    return dithered.convert("RGB")


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
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="画像の読み込みに失敗しました")

    original_width, original_height = img.size
    target_width, target_height = width, height

    # 回転判定 (アスペクト比が逆転する場合)
    rotate = False
    if (original_width > original_height and target_width < target_height) or (
        original_width < original_height and target_width > target_height
    ):
        rotate = True

    if rotate:
        img = img.rotate(90, expand=True)
        original_width, original_height = img.size  # 回転後のサイズ

    # アスペクト比を維持しつつ中央クロップ＆リサイズ
    img = ImageOps.fit(
        img, (target_width, target_height), method=Image.Resampling.LANCZOS
    )
    # 自動コントラストで画像のコントラストを調整
    img = ImageOps.autocontrast(img)
    # 彩度を強調（3倍）
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(3.0)

    # 誤差拡散
    dithered = apply_dithering(img)

    buf = io.BytesIO()
    dithered.save(buf, format="BMP")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/bmp")
