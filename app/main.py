import uvicorn
from fastapi import FastAPI
from starlette.responses import HTMLResponse

from config import settings
from contextlib import asynccontextmanager

from models import db_helper, Base
from api import router as api_router

from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination





@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # shutdown
    await db_helper.dispose()


main_app = FastAPI(
    lifespan=lifespan,
)
main_app.include_router(
    api_router,
)
main_app.mount("/static", StaticFiles(directory="static"), name="static")

# Add pagination support
add_pagination(main_app)

# @main_app.post("/items/{item_id}") ##примерчик 1
# async def read_item(item_id: int, q: str | None = None):
#     print(item_id)
#     print(q)
#     return {"item_id": item_id}
#
# @main_app.get("/html/") #тест какойто
# async def read_html():
#     data = """
#     <html>
#          <h1>Hello World а это бади</h1>
#     </html>
#     """
#     return HTMLResponse(content=data, media_type="text/html")




if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )





