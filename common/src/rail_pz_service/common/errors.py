"""pz-rail-service specific error types"""


class RAILIDMismatchError(ValueError):
    """Raised when there is an ID mismatch between row IDs"""


class RAILIntegrityError(RuntimeError):
    """Raise when catching a sqlalchemy.exc.IntegrityError"""


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
