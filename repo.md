Directory Structure:
```
.
├── app
│   ├── __init__.py
│   ├── main.py
│   └── routers
│       ├── __init__.py
│       └── image.py
└── pyproject.toml

```

---
File: app/main.py
---
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import image

app = FastAPI()

# 静的ファイル配信
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(image.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}

---
File: app/__init__.py
---

---
File: app/routers/image.py
---
from fastapi import APIRouter, UploadFile, File, Response, HTTPException, Form
from PIL import Image, ImageOps, ImageEnhance
import io

router = APIRouter()


def apply_dithering(image: Image.Image) -> Image.Image:
    """
    誤差拡散法（Floyd-Steinberg）を用いて、画像をカスタムパレットに変換します。

    Args:
        image (Image.Image): 入力画像

    Returns:
        Image.Image: カスタムパレットでディザリングされた画像
    """
    # 公式サンプル準拠の6色パレット（順序・値厳守）
    custom_palette: list[int] = [
        0,
        0,
        0,  # 0: 黒
        255,
        255,
        255,  # 1: 白
        255,
        243,
        56,  # 2: 黄
        191,
        0,
        0,  # 3: 赤
        100,
        64,
        255,  # 4: 青
        67,
        138,
        28,  # 5: 緑
    ]
    # PILパレットは256色(768要素)必要なので残りは0埋め
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
    image: UploadFile = File(...),
    width: int = Form(...),
    height: int = Form(...),
) -> Response:
    """
    画像を受け取り、指定サイズにリサイズ・ディザリングしてBMP画像として返却します。

    Args:
        image (UploadFile): アップロード画像
        width (int): 出力画像の幅
        height (int): 出力画像の高さ

    Returns:
        Response: BMP画像のバイナリレスポンス

    回転→リサイズ→彩度調整→シャープネス強調→減色処理
    """
    try:
        contents: bytes = await image.read()
        img: Image.Image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="画像の読み込みに失敗しました")

    original_width, original_height = img.size
    target_width, target_height = width, height

    # 回転判定 (アスペクト比が逆転する場合)
    rotate: bool = (
        original_width > original_height and target_width < target_height
    ) or (original_width < original_height and target_width > target_height)

    if rotate:
        img = img.rotate(90, expand=True)
        original_width, original_height = img.size  # 回転後のサイズ

    # リサイズ(中央クロップ)
    img = ImageOps.fit(
        img, (target_width, target_height), method=Image.Resampling.LANCZOS
    )
    # 自動コントラストで画像のコントラストを調整
    # img = ImageOps.autocontrast(img)
    # 彩度を強調（3倍）
    # img = ImageEnhance.Color(img).enhance(3.0)
    # シャープネスを強調
    img = ImageEnhance.Sharpness(img).enhance(2.0)

    # 誤差拡散
    dithered: Image.Image = apply_dithering(img)

    buf = io.BytesIO()
    dithered.save(buf, format="BMP")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/bmp")

---
File: app/routers/__init__.py
---

---
File: pyproject.toml
---
[project]
name = "epaper-image-tool"
version = "0.1.0"
description = "電子ペーパー用に画像を加工するサイト"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115.6",
    "jinja2>=3.1.4",
    "numpy>=2.2.4",
    "pillow>=11.2.1",
    "ruff>=0.8.4",
    "uvicorn>=0.34.0",
]

