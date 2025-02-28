import os
import traceback
from typing import Any

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


async def _parse_request(
    session: async_scoped_session,
    request: Request,
    *,
    use_form: bool = False,
) -> dict:
    id_lookup_dict: dict[str, type[db.RowMixin]] = {
        "algo": db.Algorithm,
        "catalog_tag": db.CatalogTag,
        "dataset": db.Dataset,
        "model": db.Model,
        "estimator": db.Estimator,
        "request": db.Request,
    }

    extra_properties = ["display_type", "skip_estimator", "data"]

    properties = []
    properties += extra_properties
    properties += [f"{field_}_id" for field_ in id_lookup_dict.keys()]
    properties += [f"{field_}_name" for field_ in id_lookup_dict.keys()]

    params: dict[str, Any] = {}

    orig_context: dict[str, Any] = {}
    
    if use_form:
        form_data = await request.form()
        orig_context= {
            field_: form_data.get(field_, request.query_params.get(field_)) for field_ in properties
        }
        if "fileToUpload" in form_data:
            params["file_to_load"] = form_data["fileToUpload"]
        params["form_keys"] = list(form_data.keys())
    else:
        orig_context = {field_: request.query_params.get(field_) for field_ in properties}

    for id_field_, lookup_class in id_lookup_dict.items():
        the_id_ = orig_context.get(f"{id_field_}_id")
        if the_id_ is not None:
            params[id_field_] = await lookup_class.get_row(session, the_id_)
        the_name_ = orig_context.get(f"{id_field_}_name")
        if the_name_ is not None:
            params[f"{id_field_}_name"] = the_name_

    for prop_ in extra_properties:
        val = orig_context.get(prop_)
        if val is not None:
            params[prop_] = val

    return params


async def _make_request_context(
    session: async_scoped_session,
    **kwargs: Any,
) -> dict:
    cache = db.Cache.shared_cache()

    the_tree = await cache.get_catalog_tag_tree(session, rebuild=kwargs.get("rebuild_tree", False))
    catalog_tag_ = kwargs.get("catalog_tag")
    dataset_id = kwargs.get("dataset_id")

    if catalog_tag_ is not None:
        catalog_tag_leaf = the_tree.catalog_tags[catalog_tag_.id]
    else:
        catalog_tag_leaf = models.CatalogTagLeaf(
            algos={},
            datasets={},
            catalog_tag=None,
        )

    catalog_tag_dataset_tree = catalog_tag_leaf.filter_for_dataset(
        dataset_id,
    )
    
    context = {
        "all_catalog_tags": the_tree.catalog_tags,
        "all_algos": the_tree.algos,
        "selected_datasets": catalog_tag_leaf.datasets,
        "selected_algos": catalog_tag_dataset_tree.algos,
    }

    return context


async def _get_request_context(
    session: async_scoped_session,
    request: Request,
    *,
    use_form: bool = False,
    rebuild_tree: bool = False,
) -> dict:
    params = await _parse_request(session, request, use_form=use_form)

    extra_context = await _make_request_context(session, **params, rebuild_tree=rebuild_tree)

    context = params.copy()
    context.update(**extra_context)
    return context


async def _load_dataset(
    request: Request,
    session: async_scoped_session = Depends(db_session_dependency),
) -> db.Dataset:
    request_params = await _parse_request(session, request, use_form=True)

    # Upload the file to the import area
    file_to_load = request_params["file_to_load"]
    dataset_name = request_params["dataset_name"]
    catalog_tag_ = request_params["catalog_tag"]

    contents = await file_to_load.read()

    temp_filename = os.path.join(config.storage.import_area, file_to_load.filename)
    os.makedirs(config.storage.import_area, exist_ok=True)
    with open(temp_filename, "wb") as f:
        f.write(contents)

    # Now validate the model and register it
    load_dataset_query = models.LoadDatasetQuery(
        name=dataset_name,
        catalog_tag_name=catalog_tag_.name,
        path=temp_filename,
    )
    try:
        new_dataset = await routers.load.load_dataset(
            load_dataset_query,
            session,
        )
        return new_dataset
    except Exception as e:
        print(e)
        print(f"Failed to load dataset, removing temp file {temp_filename}")
        os.remove(temp_filename)
        raise e


async def _load_dataset_from_values(
    request: Request,
    session: async_scoped_session = Depends(db_session_dependency),
) -> db.Dataset:
    request_params = await _parse_request(session, request, use_form=True)

    dataset_name = request_params["dataset_name"]
    dataset_data = request_params["data"]
    catalog_tag_ = request_params["catalog_tag"]

    # Now validate the model and register it
    load_dataset_query = models.LoadDatasetQuery(
        name=dataset_name,
        catalog_tag_name=catalog_tag_.name,
        path=None,
        data=dataset_data,
    )
    try:
        new_dataset = await routers.load.load_dataset(
            load_dataset_query,
            session,
        )
        return new_dataset
    except Exception as e:
        print(e)
        print(f"Failed to load dataset {dataset_name}")
        raise e

async def _load_model(
    request: Request,
    session: async_scoped_session = Depends(db_session_dependency),
) -> db.Model:
    request_params = await _get_request_context(session, request, use_form=True)

    # Upload the file to the import area
    file_to_load = request_params["file_to_load"]
    model_name = request_params["model_name"]
    catalog_tag_ = request_params["catalog_tag"]
    algo_ = request_params["algo"]

    contents = await file_to_load.read()

    temp_filename = os.path.join(config.storage.import_area, file_to_load.filename)
    os.makedirs(config.storage.import_area, exist_ok=True)
    with open(temp_filename, "wb") as f:
        f.write(contents)

    # Now validate the model and register it
    load_model_query = models.LoadModelQuery(
        name=model_name,
        path=temp_filename,
        algo_name=algo_.name,
        catalog_tag_name=catalog_tag_.name,
    )
    try:
        new_model = await routers.load.load_model(
            load_model_query,
            session,
        )
        skip_estimator = request_params.get("skip_estimator", None)
        if skip_estimator is None:
            load_estimator_query = models.LoadEstimatorQuery(
                name=model_name,
                model_name=model_name,
            )
            _new_estimator = await routers.load.load_estimator(
                load_estimator_query,
                session,
            )
        return new_model
    except Exception as e:
        print(e)
        print(f"Failed to load model, removing temp file {temp_filename}")
        os.remove(temp_filename)
        model_name = None
        raise e


async def _load_estimator(
    request: Request,
    session: async_scoped_session = Depends(db_session_dependency),
) -> db.Estimator:
    request_params = await _parse_request(session, request, use_form=True)

    model_ = request_params["model"]
    estimator_name = request_params["estimator_name"]

    model_ = await db.Model.get_row_by_name(session, model_.name)
    await session.refresh(model_, attribute_names=["algo_", "catalog_tag_"])

    # Now validate the model and register it
    load_estimator_query = models.LoadEstimatorQuery(
        name=estimator_name,
        model_name=model_.name,
    )
    try:
        new_estimator = await routers.load.load_estimator(
            load_estimator_query,
            session,
        )
        return new_estimator
    except Exception as e:
        print(e)
        print(f"Failed to load estimator {estimator_name}")
        raise e

@web_app.post("/tree/", response_class=HTMLResponse)
async def post_tree(
    request: Request,
    catalog_tag_name: str | None = None,
    dataset_name: str | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    # get info from request
    request_params = await _parse_request(session, request, use_form=True)

    rebuild_tree: bool = False

    form_keys = request_params["form_keys"]

    if "submit_model" in form_keys:
        try:
            new_model = await _load_model(
                request=request,
                session=session,
            )
            request_params["model"] = new_model
            rebuild_tree = True
        except Exception as e:
            print(e)
            traceback.print_tb(e.__traceback__)
            return templates.TemplateResponse(f"Something went wrong with get_catalog_tag_tree:  {e}")

    elif "submit_dataset" in form_keys:
        try:
            new_dataset = await _load_dataset(
                request=request,
                session=session,
            )
            request_params["dataset"] = new_dataset
            rebuild_tree = True
        except Exception as e:
            print(e)
            traceback.print_tb(e.__traceback__)
            return templates.TemplateResponse(f"Something went wrong with get_catalog_tag_tree:  {e}")

    elif "run_request" in form_keys:
        create_request_query = models.RequestCreate(
            estimator_name=request_params["estimator_name"],
            dataset_name=request_params["dataset_name"],
        )
        try:
            new_request = await routers.request.create(
                create_request_query,
                session,
            )
            request_params["request"] = new_request
            rebuild_tree = True
        except Exception as e:
            print(e)

    try:
        extra_context = await _make_request_context(
            session,
            **request_params,
            rebuild_tree=rebuild_tree,
        )
        context = request_params.copy()
        context.update(**extra_context)

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


@web_app.get("/tree/", response_class=HTMLResponse)
async def get_tree(
    request: Request,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    # get info from request
    request_params = await _parse_request(session, request, use_form=False)

    display_type = request_params.get("display_type")
    if display_type == 'algo_form':
        if "show_algo" in request.query_params:
            request_params["display_type"] = "show_algorithm"
        elif "load_model" in request.query_params:
            request_params["display_type"] = "load_model"
    elif display_type == 'model_form':
        if "show_model" in request.query_params:
            request_params["display_type"] = "show_model"
        elif "load_estimator" in request.query_params:
            request_params["display_type"] = "load_estimator"
    elif display_type == 'estimator_form':
        if "show_estimator" in request.query_params:
            request_params["display_type"] = "show_estimator"

    try:
        extra_context = await _make_request_context(
            session,
            **request_params,
        )
        context = request_params.copy()
        context.update(**extra_context)
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
