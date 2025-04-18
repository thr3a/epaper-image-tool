from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from .routers import items
from .routers import image

app = FastAPI()

# 静的ファイル配信
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# テンプレート
templates = Jinja2Templates(directory="app/templates")

app.include_router(items.router)
app.include_router(image.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/env")
async def get_env():
    """
    環境変数をすべてJSON形式で出力するエンドポイント
    """
    return dict(os.environ)
