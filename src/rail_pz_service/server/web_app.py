import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from safir.dependencies.db_session import db_session_dependency
from safir.dependencies.http_client import http_client_dependency
from sqlalchemy.ext.asyncio import async_scoped_session

from ..config import config
from . import routers


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    """Hook FastAPI init/cleanups."""
    # Dependency inits before app starts running
    await db_session_dependency.initialize(config.db.url, config.db.password)
    assert db_session_dependency._engine is not None
    db_session_dependency._engine.echo = config.db.echo

    # App runs here...
    yield

    # Dependency cleanups after app is finished
    await db_session_dependency.aclose()
    await http_client_dependency.aclose()


web_app = FastAPI(lifespan=lifespan, title="RAIL p(z) service")

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

router = APIRouter(
    prefix="/web_app",
    tags=["Web Application"],
)

web_app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, "static"))), name="static")


@web_app.get("/catalog_tags/", response_class=HTMLResponse)
async def get_catalog_tags(
    request: Request,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    try:
        catalog_tags = await routers.catalog_tag.get_rows(session=session)
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_rows:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/catalog_tags.html",
            request=request,
            context={
                "catalog_tags": catalog_tags,
            },
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/models/{catalog_tag_id}", response_class=HTMLResponse)
async def get_models(
    request: Request,
    catalog_tag_id: int,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    try:
        models = await routers.catalog_tag.get_models(catalog_tag_id, session)
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_rows:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/models.html",
            request=request,
            context={
                "catalog_tag_id": catalog_tag_id,
                "models": models,
            },
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/estimators/{catalog_tag_id}", response_class=HTMLResponse)
async def get_estimators(
    request: Request,
    catalog_tag_id: int,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    try:
        estimators = await routers.catalog_tag.get_estimators(catalog_tag_id, session)
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_rows:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/estimators.html",
            request=request,
            context={
                "catalog_tag_id": catalog_tag_id,
                "estimators": estimators,
            },
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/datasets/{catalog_tag_id}", response_class=HTMLResponse)
async def get_datasets(
    request: Request,
    catalog_tag_id: int,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    try:
        datasets = await routers.catalog_tag.get_datasets(catalog_tag_id, session)
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_rows:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/datasets.html",
            request=request,
            context={
                "catalog_tag_id": catalog_tag_id,
                "datasets": datasets,
            },
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/layout/", response_class=HTMLResponse)
async def test_layout(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("pages/mockup.html", {"request": request})


class ReadScriptLogRequest(BaseModel):
    log_path: str


@web_app.post("/read-script-log")
async def read_script_log(request: ReadScriptLogRequest) -> dict[str, str]:
    file_path = Path(request.log_path)

    # Check if the file exists
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Read the content of the file
        content = file_path.read_text()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
