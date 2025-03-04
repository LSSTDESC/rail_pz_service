******************
Creating A Request
******************

From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.request.PZRailRequestClient.create
    :noindex:

.. autoclass:: rail_pz_service.models.RequestCreate
    :noindex:
    :members:
    :member-order: bysource


From client CLI
---------------

.. click:: rail_pz_service.client.cli.request:create
    :prog: pz-rail-service-client request create
    :nested: none


From python on server side
--------------------------

.. autofunction:: rail_pz_service.db.cache.Cache.create_request
    :noindex:


From server CLI
---------------

.. click:: rail_pz_service.db.cli.request:create
    :prog: pz-rail-service-admin request create
    :nested: none
