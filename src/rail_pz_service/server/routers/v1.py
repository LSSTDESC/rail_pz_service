from fastapi import APIRouter

from . import (
    algorithm,
    catalog_tag,
    dataset,
    estimator,
    load,
    model,
    request,
)

router = APIRouter(
    prefix="/v1",
)

router.include_router(load.router)
router.include_router(request.router)

router.include_router(algorithm.router)
router.include_router(catalog_tag.router)
router.include_router(dataset.router)
router.include_router(estimator.router)
router.include_router(model.router)
