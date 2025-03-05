"""rail_pz_service is a tool-kit to stand up a web service to
provide on-the-fly estimates of per-object photometric redshifts.

It consists of several python sub-packages:

`rail_pz_service.common`: some common utilites such as configuration management.

`rail_pz_service.client`: a client-side python interface to access a server.

`rail_pz_service.db`: the database model and some utilities to mangage it.

`rail_pz_service.server`: the web service and associated routers.


And a few command line tools:

`pz-rail-service-client`: a client-side CLI to access a server

`pz-rail-service-admin`: a server-side CLI to manage the underlying database

`pz-rail-service-server`: the web-server API

`pz-rail-service-worker`: a worker process to handle request on the server
"""

from ._version import __version__
from . import client, common, config, db, models, server

__all__ = ["__version__", "client", "common", "config", "db", "models", "server"]
