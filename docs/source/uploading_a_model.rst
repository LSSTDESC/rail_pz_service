*****************
Uploading a Model
*****************

From Web-App
------------

You can easily load a model using the web app.

You will first need to select a CatalogTag and Algorithm.

Use the `load` button in the `Model` section of the sidebar and
the use the control panel to provide a name and file to upload.

The currently selected Algorithm and CatalogTag will be
associated with the Model.

The Model pickle file metadata will be checked to ensure that
the Algorithm and CatalogTag are consistent.

Note that by default an estimator with the same name and
default values of the configuration parameters will be
created at the same time.


From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.load.PZRailLoadClient.model
    :noindex:


From client CLI
---------------

.. click:: rail_pz_service.client.cli.load:model_command
    :prog: pz-rail-service-client load model
    :nested: none



From python on server side
--------------------------

.. autofunction:: rail_pz_service.db.cache.Cache.load_model_from_file
    :noindex:


From server CLI
---------------

.. click:: rail_pz_service.db.cli.load:model_command
    :prog: pz-rail-service-admin load model
    :nested: none
