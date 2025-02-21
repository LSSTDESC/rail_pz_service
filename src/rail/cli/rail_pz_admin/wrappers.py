

def output_pydantic_object(
    model: BaseModel,
    output: admin_options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a single object as requested

    Parameters
    ----------
    model:
        Object in question

    output:
        Output format

    col_names:
        Names for columns in tabular representation
    """
    match output:
        case options.OutputEnum.json:
            click.echo(json.dumps(model.model_dump(), cls=CustomJSONEncoder, indent=4))
        case options.OutputEnum.yaml:
            click.echo(yaml.dump(model.model_dump()))
        case _:
            the_table = [[getattr(model, col_) for col_ in col_names]]
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))


def output_pydantic_list(
    models: Sequence[BaseModel],
    output: options.OutputEnum | None,
    col_names: list[str],
) -> None:
    """Render a sequences of objects as requested

    Parameters
    ----------
    models:
        Objects in question

    output:
        Output format

    col_names:
        Names for columns in tabular representation
    """
    json_list = []
    yaml_list = []
    the_table = []
    for model_ in models:
        match output:
            case options.OutputEnum.json:
                json_list.append(model_.model_dump())
            case options.OutputEnum.yaml:
                yaml_list.append(model_.model_dump())
            case _:
                the_table.append([str(getattr(model_, col_)) for col_ in col_names])
    match output:
        case options.OutputEnum.json:
            click.echo(json.dumps(json_list, cls=CustomJSONEncoder, indent=4))
        case options.OutputEnum.yaml:
            click.echo(yaml.dump(yaml_list))
        case _:
            click.echo(tabulate(the_table, headers=col_names, tablefmt="plain"))

            
def output_dict(
    the_dict: dict,
    output: options.OutputEnum | None,
) -> None:
    """Render a python dict as requested

    Parameters
    ----------
    the_dict:
        The dict in question

    output:
        Output format
    """
    match output:
        case options.OutputEnum.json:
            click.echo(json.dumps(the_dict, cls=CustomJSONEncoder, indent=4))
        case options.OutputEnum.yaml:
            click.echo(yaml.dump(the_dict))
        case _:
            for key, val in the_dict.items():
                click.echo(f"{key}: {val}")

def get_list_command(
    group_command: Callable,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets all the rows from a table
    and attaches that function to the cli.

    This version will provide a function that always returns
    all the rows

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    Callable
        Function that return all the rows for the table in question
    """

    @group_command(name="list", help="list rows in table")
    @admin_options.db()
    @admin_options.output()
    def get_rows(
        db: db,
        output: options.OutputEnum | None,
    ) -> None:
        """List the existing rows"""
        result = db_class.get_rows(db.session())
        output_pydantic_list(result, output, db_class.col_names_for_table)

def get_row_command(
    group_command: Callable,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    Callable
        Function that returns the row for the table in question
    """

    @group_command(name="all")
    @options.db()
    @options.row_id()
    @options.output()
    def get_row(
        db: db,
        row_id: int,
        output: options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        result = db_class.get_row(db.session(), row_id)
        output_pydantic_object(result, output, db_class.col_names_for_table)
        
    return get_row


def get_row_by_name_command(
    group_command: Callable,
    db_class: TypeAlias,
) -> Callable:
    """Return a function that gets a row from a table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    Returns
    -------
    the_function: Callable
        Function that returns the row for the table in question
    """

    @group_command(name="by_name")
    @options.db()
    @options.name()
    @options.output()
    def get_row_by_name(
        db: db,
        name: str,
        output: options.OutputEnum | None,
    ) -> None:
        """Get a single row"""
        result = db_class.get_row_by_name(db.session(), name)
        output_pydantic_object(result, output, db_class.col_names_for_table)
        
    return get_row_by_name


def get_create_command(
    group_command: Callable,
    db_class: TypeAlias,
    create_options: list[Callable],
) -> Callable:
    """Return a function that creates a new row in the table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    db_class: TypeAlias = db.RowMixin
        Underlying database class

    create_options: list[Callable]
        Command line options for the create function

    Returns
    -------
    Callable
        Function that creates a row in the table
    """

    def create(
        db: db,
        output: options.OutputEnum | None,
        **kwargs: Any,
    ) -> None:
        """Create a new row"""
        result = db_class.create_row(db.session(), **kwargs)
        output_pydantic_object(result, output, db_class.col_names_for_table)

    for option_ in create_options:
        create = option_(create)

    create = group_command(name="create")(create)
    return create


def get_delete_command(
    group_command: Callable,
) -> Callable:
    """Return a function that delets a row in the table
    and attaches that function to the cli.

    Parameters
    ----------
    group_command: Callable
        CLI decorator from the CLI group to attach to

    Returns
    -------
    Callable
        Function that deletes a row in the table
    """

    @group_command(name="delete")
    @options.db()
    @options.row_id()
    def delete(
        db: db,
        row_id: int,
    ) -> None:
        """Delete a row"""
        db_class.delete_row(db.session(), **kwargs)

    return delete
