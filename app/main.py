from fastapi import FastAPI
import os

from .routers import items

app = FastAPI()

app.include_router(items.router)


@app.get("/")
async def root():
    return {"message": "nyaa5"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/env")
async def get_env():
    """
    環境変数をすべてJSON形式で出力するエンドポイント
    """
    return dict(os.environ)
