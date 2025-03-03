"""pz-rail-service specific error types"""


class RAILIDMismatchError(ValueError):
    """Raised when there is an ID mismatch between row IDs"""


class RAILIntegrityError(RuntimeError):
    """Raised when catching a sqlalchemy.exc.IntegrityError"""


class RAILStatementError(RuntimeError):
    """Raised when catching a sqlalchemy.exc.StatementError"""


class RAILMissingIDError(KeyError):
    """Raised when no row matches the requested ID"""


class RAILMissingNameError(KeyError):
    """Raised when no row matches the requested name"""


class RAILMissingRowCreateInputError(AttributeError):
    """Raised when call to create a row is missing required information"""


class RAILImportError(ImportError):
    """Raised when RAIL failed to import a module"""


class RAILRequestError(RuntimeError):
    """Raised when a RAIL request failed"""


class RAILFileNotFoundError(FileNotFoundError):
    """Raised when a requested input file is not found"""


class RAILBadDatasetError(RuntimeError):
    """Raised when a requested input dataset fails validation checks"""


class RAILBadModelError(RuntimeError):
    """Raised when a requested input model fails validation checks"""


class RAILMissingInputError(FileNotFoundError):
    """Raised when a function is missing a required input"""


class RAILBadInputError(FileNotFoundError):
    """Raised when a functions input is not what is expected"""
