Directory Structure:
```
.
├── app
│   ├── __init__.py
│   ├── main.py
│   └── routers
│       ├── __init__.py
│       └── items.py
└── pyproject.toml

```

---
File: app/main.py
---
from fastapi import FastAPI

from .routers import items

app = FastAPI()

app.include_router(items.router)


@app.get("/")
async def root() -> dict[str, str]:
    """トップページ"""
    return {"message": "turai.work"}


@app.get("/health")
async def health() -> dict[str, str]:
    """ヘルスチェック用エンドポイント。"""
    return {"status": "ok"}

---
File: app/__init__.py
---

---
File: app/routers/items.py
---
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field


class Item(BaseModel):
    """アイテムの基本情報"""

    name: str = Field(..., description="アイテム名")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "Plumbus"},
                {"name": "Portal Gun"},
            ]
        }
    }


class ItemWithId(Item):
    """アイテムの詳細情報（ID を含む）"""

    item_id: str = Field(..., description="アイテムの識別子（Path パラメータ）")


class ErrorResponse(BaseModel):
    """エラーレスポンスの共通形式"""

    detail: str = Field(..., description="エラーメッセージの詳細")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"detail": "Item not found"},
                {"detail": "You can only update the item: plumbus"},
            ]
        }
    }


router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)
fake_items_db: dict[str, Item] = {"plumbus": Item(name="Plumbus"), "gun": Item(name="Portal Gun")}


@router.get(
    "/",
    summary="アイテム一覧の取得",
    description=("登録されているすべてのアイテムを返します。返却値はキーが item_id、値が Item モデルのオブジェクトである連想配列です。"),
    response_model=dict[str, Item],
    response_description="キーが item_id、値が Item モデルのオブジェクト",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "plumbus": {"name": "Plumbus"},
                        "gun": {"name": "Portal Gun"},
                    }
                }
            }
        }
    },
)
async def read_items() -> dict[str, Item]:
    """アイテムを全件取得します。"""
    return fake_items_db


@router.get(
    "/{item_id}",
    summary="アイテム詳細の取得",
    description="指定した item_id のアイテムを返します。存在しない場合は 404 を返します。",
    response_model=ItemWithId,
    response_description="指定した item_id のアイテム詳細",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "指定したアイテムが存在しません",
            "content": {"application/json": {"example": {"detail": "Item not found"}}},
        }
    },
)
async def read_item(item_id: str = Path(..., description="取得するアイテムID", example="plumbus")) -> ItemWithId:
    """単一アイテムを取得します。"""
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemWithId(name=fake_items_db[item_id].name, item_id=item_id)


@router.put(
    "/{item_id}",
    tags=["custom"],
    summary="アイテムの更新（サンプル）",
    description="plumbus のみ更新可能なサンプル実装です。それ以外は 403 を返します。",
    response_model=ItemWithId,
    response_description="更新後のアイテム",
    responses={
        403: {
            "model": ErrorResponse,
            "description": "plumbus 以外の更新は禁止されています",
            "content": {"application/json": {"example": {"detail": "You can only update the item: plumbus"}}},
        }
    },
)
async def update_item(item_id: str = Path(..., description="更新するアイテムID", example="plumbus")) -> ItemWithId:
    """アイテムを更新します（デモ用の制限あり）"""
    if item_id != "plumbus":
        raise HTTPException(status_code=403, detail="You can only update the item: plumbus")
    return ItemWithId(item_id=item_id, name="The great Plumbus")

---
File: app/routers/__init__.py
---

---
File: pyproject.toml
---
[project]
name = "fastapi-template"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "fastapi[standard]",
    "ruff",
    "pytest"
]

[tool.ruff]
line-length = 300
target-version = "py313"
exclude = [".git", ".ruff_cache", ".venv", ".vscode"]

[tool.ruff.lint]
preview = true
select = [
    "ANN", # type annotation
    "B",   # flake8-bugbear
    "D",   # pydocstyle
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "PTH", # use `pathlib.Path` instead of `os.path`
    "RUF", # ruff specific rules
    "SIM", # flake8-simplify
    "UP",  # pyupgrade
    "W",   # pycodestyle warnings
]
ignore = [
    "RUF001", # 文字列内の曖昧なUnicode文字を許容
    "ANN401", # 関数引数の型アノテーションがAnyでも許容
    "B007",   # ループ変数の未使用を許容
    "B008",   # デフォルト引数での関数呼び出しを許容
    "B905",   # strict=Trueなしのzip()使用を許容
    "COM812", # カンマの付け忘れを許容
    "COM819", # カンマ禁止違反を許容
    "D1",     # 公開モジュール・クラス・関数・メソッドのdocstring省略を許容
    "D203",   # クラスdocstring前の空行数（GoogleスタイルではD211優先のため無視）
    "D205",   # docstringの要約行と説明の間の空行数を無視
    "D212",   # 複数行docstringの要約行の位置（1行目開始）を無視
    "D213",   # 複数行docstringの要約行の位置（2行目開始）を無視
    "D400",   # docstringの1行目の末尾ピリオドを無視
    "D415",   # docstringの1行目の末尾句読点（ピリオド等）を無視
    "E114",   # コメント行のインデントが4の倍数でない場合を許容
    "G004",   # ログ出力でのf-string使用を許容
    "ISC001", # 1行での暗黙的な文字列連結を許容
    "ISC002", # 複数行での暗黙的な文字列連結を許容
    "PTH123", # open()のPath.open()置き換えを強制しない
    # "Q000",   # シングルクォート使用を許容（ダブルクォート推奨違反）
    "Q001",   # 複数行文字列でのシングルクォート使用を許容
    "Q002",   # docstringでのシングルクォート使用を許容
    "RUF002", # docstring内の曖昧なUnicode文字を許容
    "RUF003", # コメント内の曖昧なUnicode文字を許容
    "SIM105", # try-except-passをcontextlib.suppressで置き換えなくても許容
    "SIM108", # if-elseブロックを三項演算子にしなくても許容
    "SIM116", # 連続したif文を辞書にしなくても許容
    "UP038",  # isinstanceの(X, Y)をX | Yにしなくても許容（非推奨）
]
unfixable = [
    "F401", # unused import
    "F841", # unused variable
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.lint.pydocstyle]
convention = "google"

