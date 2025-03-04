*****************
Uploading a Model
*****************

From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.load.PZRailLoadClient.model
    :noindex:

.. autoclass:: rail_pz_service.models.LoadModelQuery
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: model_config


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
