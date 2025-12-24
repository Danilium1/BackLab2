from typing import Annotated
from fastapi import (
    APIRouter,
    Form,
)
from fastapi.responses import FileResponse
from config import settings
from pydantic import BaseModel
from pathlib import Path
import os

router = APIRouter(
    tags=["Test"],
    prefix=settings.url.test,
)


@router.get("")
def index():
    return {"message": "Hello, World!"}


@router.post("/login/")
def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}


class Post(BaseModel):
    title: str
    content: str


@router.post("/create-item/")
def create_item(post: Post):
    return post


@router.put("/create-item/")
def create_item_put(post: Post):
    return post


@router.get("/download-pdf/")
def download_pdf():

    BASE_DIR = Path(__file__).resolve().parent.parent
    file_path = os.path.join(BASE_DIR, "media", "sample.pdf")
    if not os.path.exists(file_path):
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="File not found")

    # return FileResponse(
    #     path=file_path,
    #     media_type="application/pdf",
    #     filename="sample.pdf",
    #     headers={"X-File-Name": "sample.pdf"},
    # )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={
            "X-File-Name": "sample.pdf",
            "Content-Disposition": "inline; filename=sample.pdf",
        },
    )
