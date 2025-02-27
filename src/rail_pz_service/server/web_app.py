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

from .. import db, models
from ..config import config


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


async def get_request_context(
    session: async_scoped_session,
    catalog_tag_name: str | None = None,
    dataset_name: str | None = None,
) -> dict:
    cache = db.Cache.shared_cache()

    the_tree = await cache.get_catalog_tag_tree(session)
    if catalog_tag_name is not None:
        catalog_tag_leaf = the_tree.catalog_tags[catalog_tag_name]
    else:
        catalog_tag_leaf = models.CatalogTagLeaf(
            algos={},
            datasets={},
            catalog_tag=None,
        )

    selected_dataset_id: int | None = None
    if dataset_name is not None:
        selected_dataset = await db.Dataset.get_row_by_name(session, dataset_name)
        selected_dataset_id = selected_dataset.id
    catalog_tag_dataset_tree = catalog_tag_leaf.filter_for_dataset(
        selected_dataset_id,
    )

    context = {
        "catalog_tag_name": catalog_tag_name,
        "dataset_name": dataset_name,
        "catalog_tags": the_tree.catalog_tags,
        "datasets": catalog_tag_leaf.datasets,
        "algos": catalog_tag_dataset_tree.algos,
    }
    return context


@web_app.get("/load_dataset/{catalog_tag_name}", response_class=HTMLResponse)
async def load_dataset(
    request: Request,
    catalog_tag_name: str | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    try:
        context = await get_request_context(
            session,
            catalog_tag_name=catalog_tag_name,
            dataset_name=None,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_catalog_tag_tree:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/load_dataset.html",
            request=request,
            context=context,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/load_dataset_from_values/{catalog_tag_name}", response_class=HTMLResponse)
async def load_dataset_from_values(
    request: Request,
    catalog_tag_name: str | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    try:
        context = await get_request_context(
            session,
            catalog_tag_name=catalog_tag_name,
            dataset_name=None,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_catalog_tag_tree:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/load_dataset_from_values.html",
            request=request,
            context=context,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/load_model/{algo_name}", response_class=HTMLResponse)
@web_app.get("/load_model/{algo_name}/{catalog_tag_name}", response_class=HTMLResponse)
@web_app.get("/load_model/{algo_name}/{catalog_tag_name}/{dataset_name}", response_class=HTMLResponse)
async def load_model(
    request: Request,
    algo_name: str,
    catalog_tag_name: str | None = None,
    dataset_name: str | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    context = await get_request_context(
        session,
        catalog_tag_name=catalog_tag_name,
        dataset_name=dataset_name,
    )

    try:
        return templates.TemplateResponse(
            name="pages/load_model.html",
            request=request,
            context=context,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/load_estimator/{model_name}", response_class=HTMLResponse)
@web_app.get("/load_estimator/{model_name}/{dataset_name}", response_class=HTMLResponse)
async def load_estimator(
    request: Request,
    model_name: str,
    dataset_name: str | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    model_ = await db.Model.get_row_by_name(session, model_name)
    await session.refresh(model_, attribute_names=["algo_", "catalog_tag_"])

    try:
        context = await get_request_context(
            session,
            catalog_tag_name=model_.catalog_tag_.name,
            dataset_name=dataset_name,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_catalog_tag_tree:  {e}")

    context.update(
        model_name=model_name,
        algo_name=model_.algo_.name,
    )

    try:
        return templates.TemplateResponse(
            name="pages/load_model.html",
            request=request,
            context=context,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/tree/", response_class=HTMLResponse)
@web_app.get("/tree/{catalog_tag_name}", response_class=HTMLResponse)
@web_app.get("/tree/{catalog_tag_name}/{dataset_name}", response_class=HTMLResponse)
async def get_tree(
    request: Request,
    catalog_tag_name: str | None = None,
    dataset_name: str | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    try:
        context = await get_request_context(
            session,
            catalog_tag_name=catalog_tag_name,
            dataset_name=dataset_name,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong with get_catalog_tag_tree:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/tree.html",
            request=request,
            context=context,
        )
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)
        return templates.TemplateResponse(f"Something went wrong:  {e}")


@web_app.get("/layout/", response_class=HTMLResponse)
async def test_layout(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("pages/nested_list.html", {"request": request})


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
