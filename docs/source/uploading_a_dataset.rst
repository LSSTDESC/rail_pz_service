*******************
Uploading a Dataset
*******************


From Web-App
------------

You can easily load a dataset using the web app.

You will first need to select a CatalogTag.

Use the `load` button in the `Dataset` section of the sidebar and
the use the control panel to provide a name and file to upload.

The currently selected CatalogTag will be
associated with the Dataset.

Alternatively, you can use the `create` button in the `Dataset`
section of the sidebar and the use the control panel to provide a
name and data values.


From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.load.PZRailLoadClient.dataset
    :noindex:



From client CLI
---------------

.. click:: rail_pz_service.client.cli.load:dataset_command
    :prog: pz-rail-service-client load dataset
    :nested: none



From python on server side
--------------------------

.. autofunction:: rail_pz_service.db.cache.Cache.load_dataset_from_file
    :noindex:


From server CLI
---------------

.. click:: rail_pz_service.db.cli.load:dataset_command
    :prog: pz-rail-service-admin load dataset
    :nested: none
