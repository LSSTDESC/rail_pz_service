*****************
Running a Request
*****************

From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.request.PZRailRequestClient.run
    :noindex:


From client CLI
---------------

.. click:: rail_pz_service.client.cli.request:run
    :prog: pz-rail-service-client request run
    :nested: none



From python on server side
--------------------------

.. autofunction:: rail_pz_service.db.Cache.run_request
    :noindex:


From server CLI
---------------

.. click:: rail_pz_service.db.cli.request:run
    :prog: pz-rail-service-admin request run
    :nested: none
