import os
import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import numpy as np
from anyio import open_file
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from safir.dependencies.db_session import db_session_dependency
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_uvicorn_logging
from sqlalchemy.ext.asyncio import async_scoped_session

from .. import db, models
from ..config import config
from .logging import LOGGER
from .routers.load import load_dataset, load_estimator, load_model
from .routers.request import create as create_request
from .routers.request import run_request

configure_uvicorn_logging(config.logging.level)

logger = LOGGER.bind(module=__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    """Hook FastAPI init/cleanups."""
    # Dependency inits before app starts running
    await db_session_dependency.initialize(config.db.url, config.db.password)
    assert db_session_dependency._engine is not None  # pylint: disable=protected-access
    db_session_dependency._engine.echo = (  # pylint: disable=protected-access
        config.db.echo
    )

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
    catalog_tag_id: int | None = None,
    use_form: bool = False,
) -> dict:
    field_names: list[str] = [
        "algo",
        "catalog_tag",
        "dataset",
        "model",
        "estimator",
        "request",
    ]

    extra_properties = [
        "display_type",
        "control_type",
        "plot_type",
        "skip_estimator",
        "data",
    ]

    properties = []
    properties += extra_properties
    properties += [f"{field_}_id" for field_ in field_names]
    properties += [f"{field_}_name" for field_ in field_names]

    params: dict[str, Any] = {}

    orig_context: dict[str, Any] = {
        "catalog_tag_id": catalog_tag_id,
    }

    if use_form:
        form_data = await request.form()
        for field_ in properties:
            test_val = form_data.get(field_, request.query_params.get(field_))
            if test_val is not None:
                orig_context.setdefault(field_, test_val)
        if "fileToUpload" in form_data:
            params["file_to_load"] = form_data["fileToUpload"]
        params["form_keys"] = list(form_data.keys())
    else:
        for field_ in properties:
            test_val = request.query_params.get(field_)
            if test_val is not None:
                orig_context.setdefault(field_, test_val)

    request_id = orig_context.get("request_id")
    if request_id is not None:
        request_ = await db.Request.get_row(session, request_id)
        params["my_request"] = request_
        orig_context["dataset_id"] = request_.dataset_id
        orig_context["estimator_id"] = request_.estimator_id

    dataset_id = orig_context.get("dataset_id")
    if dataset_id is not None:
        dataset_ = await db.Dataset.get_row(session, dataset_id)
        params["dataset"] = dataset_
        orig_context["catalog_tag_id"] = dataset_.catalog_tag_id

    estimator_id = orig_context.get("estimator_id")
    if estimator_id is not None:
        estimator_ = await db.Estimator.get_row(session, estimator_id)
        params["estimator"] = estimator_
        orig_context["catalog_tag_id"] = estimator_.catalog_tag_id
        orig_context["algo_id"] = estimator_.algo_id
        orig_context["model_id"] = estimator_.model_id

    model_id = orig_context.get("model_id")
    if model_id is not None:
        model_ = await db.Model.get_row(session, model_id)
        params["model"] = model_
        orig_context["catalog_tag_id"] = model_.catalog_tag_id
        orig_context["algo_id"] = model_.algo_id

    algo_id = orig_context.get("algo_id")
    if algo_id is not None:
        algo_ = await db.Algorithm.get_row(session, algo_id)
        params["algo"] = algo_

    catalog_tag_id = orig_context.get("catalog_tag_id")
    if catalog_tag_id is not None:
        catalog_tag_ = await db.CatalogTag.get_row(session, catalog_tag_id)
        params["catalog_tag"] = catalog_tag_

    for id_field_ in field_names:
        the_name_ = orig_context.get(f"{id_field_}_name")
        if the_name_ is not None:
            params[f"{id_field_}_name"] = the_name_

    for prop_ in extra_properties:
        val = orig_context.get(prop_)
        if val is not None:
            params[prop_] = val

    return params


async def _make_plot_context(
    session: async_scoped_session,
    request: Request,
    **kwargs: Any,
) -> dict:
    cache = db.Cache.shared_cache(logger)

    request_ = kwargs["my_request"]
    qp_dist = await cache.get_qp_dist(session, request_.id)

    plot_type = request.query_params.get("plot_type")

    if plot_type == "zmode_hist":
        the_hist = np.histogram(qp_dist.ancil["zmode"], bins=np.linspace(0.0, 3.0, 301))
        x_vals = 0.5 * (the_hist[1][0:-1] + the_hist[1][1:])
        y_vals = the_hist[0]
        return dict(
            hist_x_values=x_vals,
            hist_y_values=y_vals,
        )
    if plot_type == "pdf":
        index_param = request.query_params.get("index")
        assert index_param is not None
        index = int(index_param)
        x_vals = np.linspace(0.0, 3.0, 301)
        y_vals = np.squeeze(qp_dist[index].pdf(x_vals))
        return dict(
            hist_x_values=x_vals,
            hist_y_values=y_vals,
        )
    return {}


async def _make_request_context(
    session: async_scoped_session,
    **kwargs: Any,
) -> dict:
    all_catalog_tags = await db.CatalogTag.get_rows(session)
    all_algos = await db.Algorithm.get_rows(session)
    all_models = await db.Model.get_rows(session)

    catalog_tag_ = kwargs.get("catalog_tag")
    model_ = kwargs.get("model")
    dataset_ = kwargs.get("dataset")

    found_request: db.Request | None = None

    if dataset_ is not None:
        await session.refresh(dataset_, attribute_names=["requests_"])
        selected_request_map: dict[str, db.Request] = {}
        for request_ in dataset_.requests_:
            estimator_ = await db.Estimator.get_row(session, request_.estimator_id)
            selected_request_map[estimator_.name] = request_
            if "my_request" not in kwargs:
                if "estimator" in kwargs and kwargs["estimator"].id == estimator_.id:
                    found_request = request_
    else:
        selected_request_map = {}

    if catalog_tag_ is not None:
        await session.refresh(catalog_tag_, attribute_names=["estimators_", "models_", "datasets_"])
        selected_datasets = catalog_tag_.datasets_
        selected_models = catalog_tag_.models_
        if model_ is not None:
            await session.refresh(model_, attribute_names=["estimators_"])
            selected_estimators = model_.estimators_
        else:
            selected_estimators = catalog_tag_.estimators_
    else:
        selected_datasets = []
        selected_models = []
        selected_estimators = []

    context = dict(
        all_catalog_tags=all_catalog_tags,
        all_algos=all_algos,
        all_models=all_models,
        selected_datasets=selected_datasets,
        selected_models=selected_models,
        selected_estimators=selected_estimators,
        selected_request_map=selected_request_map,
    )

    if found_request:
        context["my_request"] = found_request

    return context


async def _get_request_context(
    session: async_scoped_session,
    request: Request,
    *,
    catalog_tag_id: int | None = None,
    use_form: bool = False,
) -> dict:
    params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=use_form)

    extra_context = await _make_request_context(session, **params)

    context = params.copy()
    context.update(**extra_context)
    return context


async def _load_dataset(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> dict:
    request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=True)

    # Upload the file to the import area
    file_to_load = request_params["file_to_load"]
    dataset_name = request_params["dataset_name"]
    catalog_tag_ = request_params["catalog_tag"]

    contents = await file_to_load.read()

    temp_filename = os.path.join(config.storage.import_area, file_to_load.filename)
    os.makedirs(config.storage.import_area, exist_ok=True)
    async with await open_file(temp_filename, "wb") as f:
        await f.write(contents)

    # Now validate the model and register it
    load_dataset_query = models.LoadDatasetQuery(
        name=dataset_name,
        catalog_tag_name=catalog_tag_.name,
        path=temp_filename,
    )
    try:
        new_dataset = await load_dataset(
            load_dataset_query,
            session,
        )
        return dict(dataset=new_dataset)
    except Exception as e:
        logger.info(e)
        logger.warn(f"Failed to load dataset, removing temp file {temp_filename}")
        os.remove(temp_filename)
        raise e


async def _load_dataset_from_values(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> dict:
    request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=True)

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
        new_dataset = await load_dataset(
            load_dataset_query,
            session,
        )
        return dict(dataset=new_dataset)
    except Exception as e:
        logger.info(e)
        logger.warn(f"Failed to load dataset {dataset_name}")
        raise e


async def _load_model(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> dict:
    request_params = await _get_request_context(
        session, request, catalog_tag_id=catalog_tag_id, use_form=True
    )

    # Upload the file to the import area
    file_to_load = request_params["file_to_load"]
    model_name = request_params["model_name"]
    catalog_tag_ = request_params["catalog_tag"]
    algo_ = request_params["algo"]

    contents = await file_to_load.read()

    temp_filename = os.path.join(config.storage.import_area, file_to_load.filename)
    os.makedirs(config.storage.import_area, exist_ok=True)
    async with await open_file(temp_filename, "wb") as f:
        await f.write(contents)

    # Now validate the model and register it
    load_model_query = models.LoadModelQuery(
        name=model_name,
        path=temp_filename,
        algo_name=algo_.name,
        catalog_tag_name=catalog_tag_.name,
    )
    try:
        new_model = await load_model(
            load_model_query,
            session,
        )
        ret_dict: dict[str, Any] = dict(model=new_model)
        skip_estimator = request_params.get("skip_estimator", None)
        if skip_estimator is None:
            load_estimator_query = models.LoadEstimatorQuery(
                name=model_name,
                model_name=model_name,
            )
            new_estimator = await load_estimator(
                load_estimator_query,
                session,
            )
            ret_dict["estimator"] = new_estimator
        return ret_dict
    except Exception as e:
        logger.info(e)
        logger.warn(f"Failed to load model, removing temp file {temp_filename}")
        os.remove(temp_filename)
        model_name = None
        raise e


async def _load_estimator(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> dict:
    request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=True)

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
        new_estimator = await load_estimator(
            load_estimator_query,
            session,
        )
        return dict(estimator=new_estimator)
    except Exception as e:
        logger.info(e)
        logger.warn(f"Failed to load estimator {estimator_name}")
        raise e


async def _create_request(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> dict:
    request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=True)

    dataset_ = request_params["dataset"]
    estimator_ = request_params["estimator"]

    # Now validate the model and register it
    create_request_query = models.RequestCreate(
        dataset_name=dataset_.name,
        estimator_name=estimator_.name,
    )
    try:
        new_request = await create_request(
            create_request_query,
            session,
        )
        return dict(my_request=new_request)
    except Exception as e:
        logger.info(e)
        logger.warn(f"Failed to create_request {create_request_query}")
        raise e


async def _run_request(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> dict:
    request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=True)

    request_ = request_params["my_request"]

    try:
        check_request = await run_request(
            request_.id,
            session,
        )
        return dict(my_request=check_request)
    except Exception as e:
        logger.info(e)
        logger.warn(f"Failed to run_request {request_}")
        raise e


async def _explore_request(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> dict:
    _request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=True)
    return dict(control_type="explore")


@web_app.post("/", response_class=HTMLResponse)
@web_app.post("/{catalog_tag_id:int}", response_class=HTMLResponse)
async def post_tree(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    # get info from request
    request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=True)

    form_keys = request_params["form_keys"]
    func_dict = dict(
        submit_model=_load_model,
        submit_estimator=_load_estimator,
        submit_dataset=_load_dataset,
        create_request=_create_request,
        run_request=_run_request,
        explore_request=_explore_request,
    )

    the_func = None
    for func_name, a_func in func_dict.items():
        if func_name in form_keys:
            try:
                the_func = a_func
                update_pars = await the_func(request=request, catalog_tag_id=catalog_tag_id, session=session)
                request_params.update(**update_pars)
                break
            except Exception as e:
                logger.warn(e)
                logger.warn("\n".join(traceback.format_tb(e.__traceback__)))
                return templates.TemplateResponse(f"Something went wrong with post_tree {func_name}:  {e}")
    if the_func is None:
        return templates.TemplateResponse(f"Cound not the a function to run {form_keys}")

    try:
        extra_context = await _make_request_context(
            session,
            **request_params,
        )
        context = request_params.copy()
        context.update(**extra_context)
    except Exception as e:
        logger.warn(e)
        logger.warn("\n".join(traceback.format_tb(e.__traceback__)))
        return templates.TemplateResponse(f"Something went wrong with post_tree _make_request_context:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/tree.html",
            request=request,
            context=context,
        )
    except Exception as e:
        logger.warn(e)
        logger.warn("\n".join(traceback.format_tb(e.__traceback__)))
        return templates.TemplateResponse(f"Something went wrong with template formating:  {e}")


@web_app.get("/", response_class=HTMLResponse)
@web_app.get("/{catalog_tag_id:int}", response_class=HTMLResponse)
async def get_tree(
    request: Request,
    catalog_tag_id: int | None = None,
    session: async_scoped_session = Depends(db_session_dependency),
) -> HTMLResponse:
    # get info from request
    request_params = await _parse_request(session, request, catalog_tag_id=catalog_tag_id, use_form=False)

    context: dict = {}

    control_type = request_params.get("control_type")
    if control_type == "dataset_form":
        if "select_dataset" in request.query_params:
            request_params["control_type"] = "select_dataset"
        elif "load_dataset" in request.query_params:
            request_params["control_type"] = "load_dataset"
        elif "load_dataset_from_values" in request.query_params:
            request_params["control_type"] = "load_dataset_from_values"
    elif control_type == "estimator_form":
        if "select_estimator" in request.query_params:
            request_params["control_type"] = "select_estimator"
        elif "load_estimator" in request.query_params:
            request_params["control_type"] = "load_estimator"
    elif control_type == "model_form":
        if "select_model" in request.query_params:
            request_params["control_type"] = "select_model"
        elif "load_model" in request.query_params:
            request_params["control_type"] = "load_model"
    elif control_type == "request_form":
        if "select_request" in request.query_params:
            request_params["control_type"] = "select_request"
        elif "run_request" in request.query_params:
            request_params["control_type"] = "run_request"
    elif control_type == "explore":
        plot_context = await _make_plot_context(
            session,
            request,
            **request_params,
        )
        context.update(**plot_context)

    try:
        extra_context = await _make_request_context(
            session,
            **request_params,
        )
        context.update(**request_params)
        context.update(**extra_context)
    except Exception as e:
        logger.warn(e)
        logger.warn("\n".join(traceback.format_tb(e.__traceback__)))
        return templates.TemplateResponse(f"Something went wrong with _make_request_context:  {e}")

    try:
        return templates.TemplateResponse(
            name="pages/tree.html",
            request=request,
            context=context,
        )
    except Exception as e:
        logger.warn(e)
        logger.warn("\n".join(traceback.format_tb(e.__traceback__)))
        return templates.TemplateResponse(f"Something went wrong with template formating:  {e}")


@web_app.get("/layout/", response_class=HTMLResponse)
async def test_layout(request: Request) -> HTMLResponse:
    # make info from request
    context: dict = dict(
        all_catalog_tags=[],
    )

    return templates.TemplateResponse(
        name="pages/tree.html",
        request=request,
        context=context,
    )


class ReadScriptLogRequest(BaseModel):
    """Request to read a log file"""

    log_path: str


@web_app.post("/read-script-log")
async def read_script_log(request: ReadScriptLogRequest) -> dict[str, str]:
    file_path = Path(request.log_path)

    # Check if the file exists
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Read the content of the file
        content = file_path.read_text(encoding="utf-8")
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}") from e
