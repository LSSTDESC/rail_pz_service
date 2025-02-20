"""pz-rail-service specific error types"""

from typing import Any, TypeVar

from sqlalchemy.exc import IntegrityError

T = TypeVar("T")

class CMIDMismatchError(ValueError):
    """Raised when there is an ID mismatch between row IDs"""

class CMIntegrityError(IntegrityError):
    """Raise when catching a sqlalchemy.exc.IntegrityError"""

class CMMissingIDError(KeyError):
    """Raised when no row matches the requested ID"""

class CMMissingNameError(KeyError):
    """Raised when no row matches the requested name"""
    
    
