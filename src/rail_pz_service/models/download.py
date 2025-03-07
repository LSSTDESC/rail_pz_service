"""Pydantic model for the Algorithm"""

from pydantic import BaseModel


class DownloadQuery(BaseModel):
    """Parameters needed to ask for a file download"""

    #: filename for output
    filename: str
