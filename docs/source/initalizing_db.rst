**************
Database setup
**************

The database setup needs to happen on the server.  It can
either be done with the server CLI, or in python.


Intializing the database
------------------------

.. click:: rail_pz_service.db.cli.admin:init
    :prog: pz-rail-service-admin init
    :nested: none


Loading basic content from RailEnv using the Server CLI
-------------------------------------------------------

.. click:: rail_pz_service.db.cli.load:algos_from_env_command
    :prog: pz-rail-service-admin load algos-from-env
    :nested: none

.. click:: rail_pz_service.db.cli.load:catalog_tags_from_env_command
    :prog: pz-rail-service-admin load catalog-tags-from-env
    :nested: none


Loading basic content from RailEnv using python on server side
--------------------------------------------------------------

.. autofunction:: rail_pz_service.db.cache.Cache.load_algorithms_from_rail_env
    :noindex:


.. autofunction:: rail_pz_service.db.cache.Cache.load_catalog_tags_from_rail_env
    :noindex:
