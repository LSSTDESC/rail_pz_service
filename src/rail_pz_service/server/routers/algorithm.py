"""http routers for managing Step tables"""

from fastapi import APIRouter

from ... import db, models
from . import wrappers

# Template specialization
# Specify the pydantic model for the table
ResponseModelClass = models.Algorithm
# Specify the associated database table
DbClass = db.Algorithm
# Specify the tag in the router documentation
TAG_STRING = "Algorithm"


# Build the router
router = APIRouter(
    prefix=f"/{DbClass.class_string}",
    tags=[TAG_STRING],
)


# Attach functions to the router
get_rows = wrappers.get_list_function(router, ResponseModelClass, DbClass)
get_row = wrappers.get_row_function(router, ResponseModelClass, DbClass)
get_row_by_name = wrappers.get_row_by_name_function(router, ResponseModelClass, DbClass)

get_estimators = wrappers.get_row_attribute_list_function(
    router, ResponseModelClass, DbClass, "estimators_", models.Estimator
)
get_models = wrappers.get_row_attribute_list_function(
    router, ResponseModelClass, DbClass, "models_", models.Estimator
)
