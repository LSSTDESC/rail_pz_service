"""Common options for pz-rail-service CLIs"""

from collections.abc import Callable
from enum import Enum, auto
from functools import partial
from typing import Any

import click
from click.decorators import FC


class DictParamType(click.ParamType):  # pragma: no cover
    """Represents the dictionary type of a CLI parameter.

    Validates and converts values from the command line string or Python into
    a Python dict.

    - All key-value pairs must be separated by one semicolon.
    - Key and value must be separated by one colon
    - Converts sequences separeted by dots into a list: list value items
        must be separated by commas.
    - Converts numbers to int.


    Usage
        >>> @click.option("--param", default=None, type=DictParamType())
        ... def command(param):
        ...     ...

        CLI: command --param='page:1; name:Items; rules:1, 2, three; extra:A,;'

    Example
    -------
        >>> param_value = 'page:1; name:Items; rules:1, 2, three; extra:A,;'
        >>> DictParamType().convert(param_value, None, None)
        {'page': 1, 'name': 'Items', 'rules': [1, 2, 'three'], 'extra': ['A']}`

    """

    name = "dictionary"

    def convert(  # pylint:  disable=inconsistent-return-statements
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> dict:
        """Converts CLI value to the dictionary structure.

        Parameters
        ----------
        value: Any
            The value to convert.
        param: (click.Parameter | None)
            The parameter that is using this type to convert its value.
        ctx:  (click.Context | None)
            The current context that arrived at this value.

        Returns
        -------
            dict: The validated and converted dictionary.

        Raises
        ------
            click.BadParameter: If the validation is failed.
        """
        if isinstance(value, dict):
            return value
        try:
            keyvalue_pairs = value.rstrip(";").split(";")
            result_dict = {}
            for pair in keyvalue_pairs:
                key, value = (item.strip() for item in pair.split(":"))
                result_dict[key] = value
            return result_dict
        except ValueError:
            self.fail(
                "All key-value pairs must be separated by one semicolon. "
                "Key and value must be separated by one colon. "
                "List value items must be separated by one comma. "
                f"Key-value: {pair}.",
                param,
                ctx,
            )


class EnumChoice(click.Choice):
    """A version of click.Choice specialized for enum types."""

    def __init__(self: "EnumChoice", enum: type[Enum], *, case_sensitive: bool = True) -> None:
        self._enum = enum
        super().__init__(list(enum.__members__.keys()), case_sensitive=case_sensitive)

    def convert(
        self: "EnumChoice",
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Enum:
        converted_str = super().convert(value, param, ctx)
        return self._enum.__members__[converted_str]


class OutputEnum(Enum):
    """Options for output format"""

    yaml = auto()  # pylint: disable=invalid-name
    json = auto()  # pylint: disable=invalid-name


class PartialOption:
    """Wrap partially specified click.option decorator for convenient reuse."""

    def __init__(self: "PartialOption", *param_decls: str, **attrs: Any) -> None:
        self._partial = partial(click.option, *param_decls, cls=click.Option, **attrs)

    def __call__(self: "PartialOption", *param_decls: str, **attrs: Any) -> Callable[[FC], FC]:
        return self._partial(*param_decls, **attrs)


config = PartialOption(
    "--config",
    type=DictParamType(),
    help="Estimator configuration parameters",
)


data = PartialOption(
    "--data",
    type=DictParamType(),
    help="Dict of magnitudes",
)


row_id = PartialOption(
    "--row-id",
    type=int,
    help="ID of object in database table",
)


output = PartialOption(
    "--output",
    "-o",
    type=EnumChoice(OutputEnum),
    help="Output format.  Summary table if not specified.",
)


name = PartialOption(
    "--name",
    type=str,
    help="Name for a particular DB row",
)


algo_name = PartialOption(
    "--algo-name",
    type=str,
    help="Name of associated algorithm",
)


class_name = PartialOption(
    "--class-name",
    type=str,
    help="Name of python class to associate to a particular DB object",
)


dataset_name = PartialOption(
    "--dataset-name",
    type=str,
    help="Name of associated dataset",
)


estimator_name = PartialOption(
    "--estimator-name",
    type=str,
    help="Name of associated estimator",
)


catalog_tag_name = PartialOption(
    "--catalog-tag-name",
    type=str,
    help="Name of associated catalog tag",
)


filename = PartialOption(
    "--filename",
    type=click.Path(),
    help="Filename for downloaded files",
)


model_name = PartialOption(
    "--model-name",
    type=str,
    help="Name of associated model",
)


index = PartialOption(
    "--index",
    type=int,
    help="Index of object inside dataset",
)


n_objects = PartialOption(
    "--n-objects",
    type=int,
    help="Number of object in dataset",
)


path = PartialOption(
    "--path",
    type=click.Path(),
    help="Name for a particular DB row",
)

validate_file = PartialOption(
    "--validate-file",
    is_flag=True,
    default=False,
    help="Validate files when uploading",
)
