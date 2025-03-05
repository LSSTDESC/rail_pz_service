**********
Components
**********


================
Component basics
================

There are a few basic components that underpin `rail_pz_service`
functionality.

Generating a `Request` requires `CatalogTag` that specifies which
columns to expect in the `Dataset` that the request in being run on,
and an `Estimator` to run the analysis using a `Model` trained for
the `Algorithm` that underlies that `Estimator` running the request,
and which is compatible with the `CatalogTag` of the `Dataset`.


=======
Request
=======

.. autoclass:: rail_pz_service.db.Request
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: get_create_kwargs


=======
Dataset
=======

.. autoclass:: rail_pz_service.db.Dataset
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: get_create_kwargs


=========
Estimator
=========

.. autoclass:: rail_pz_service.db.Estimator
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: get_create_kwargs


=====
Model
=====

.. autoclass:: rail_pz_service.db.Model
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: get_create_kwargs


=========
Algorithm
=========

.. autoclass:: rail_pz_service.db.Algorithm
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: get_create_kwargs


==========
CatalogTag
==========

.. autoclass:: rail_pz_service.db.CatalogTag
    :noindex:
    :members:
    :member-order: bysource
    :exclude-members: get_create_kwargs
