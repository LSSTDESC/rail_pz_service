*******************
Uploading a Dataset
*******************


From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.load.PZRailLoadClient.dataset
    :noindex:

.. autoclass:: rail_pz_service.models.LoadDatasetQuery
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: model_config


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
