**********************
Uploading an Estimator
**********************

From python on client side
--------------------------

.. autofunction:: rail_pz_service.client.load.PZRailLoadClient.estimator
    :noindex:

.. autoclass:: rail_pz_service.models.LoadEstimatorQuery
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: model_config


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
