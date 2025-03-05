**********************
Uploading an Estimator
**********************


From Web-App
------------

You can easily load an estimator using the web app.

You will first need to select a CatalogTag, Algorithm and Model.

Use the `load` button in the `Algorithm` section of the sidebar and
the use the control panel to provide a name, model and set any
parameter overrides.

The currently selected Algorithm, Model and CatalogTag will be
associated with the Estimator.


From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.load.PZRailLoadClient.estimator
    :noindex:


From client CLI
---------------

.. click:: rail_pz_service.client.cli.load:estimator_command
    :prog: pz-rail-service-client load estimator
    :nested: none



From python on server side
--------------------------

.. autofunction:: rail_pz_service.db.cache.Cache.load_estimator
    :noindex:


From server CLI
---------------

.. click:: rail_pz_service.db.cli.load:estimator_command
    :prog: pz-rail-service-admin load estimator
    :nested: none
