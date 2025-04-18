from fastapi import APIRouter, UploadFile, File, Response, HTTPException, Query
from fastapi.responses import StreamingResponse
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
TEMP_IMAGE_PATH = os.path.join(tempfile.gettempdir(), "epaper_last.png")


@router.post("/process")
async def process_image(image: UploadFile = File(...)):
    try:
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="画像の読み込みに失敗しました")

    dithered = apply_dithering(img)
    buf = io.BytesIO()
    dithered.save(buf, format="PNG")
    buf.seek(0)
    # 一時ファイルにも保存
    with open(TEMP_IMAGE_PATH, "wb") as f:
        f.write(buf.getbuffer())
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.get("/download")
async def download_image(format: str = Query("png", pattern="^(png|jpg|bmp)$")):
    # 一時ファイルから読み込み
    if not os.path.exists(TEMP_IMAGE_PATH):
        raise HTTPException(
            status_code=404, detail="画像がありません。先に処理を行ってください。"
        )
    img = Image.open(TEMP_IMAGE_PATH)
    buf = io.BytesIO()
    fmt = "PNG" if format == "png" else "JPEG" if format == "jpg" else "BMP"
    img.save(buf, format=fmt)
    buf.seek(0)
    media_type = (
        "image/png"
        if format == "png"
        else "image/jpeg"
        if format == "jpg"
        else "image/bmp"
    )
    filename = f"epaper_image.{format}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(buf, media_type=media_type, headers=headers)
