#########################################################################
rail_projects: a toolkit for managing `RAIL`-based data analysis projects
#########################################################################

***********
Description
***********

`rail_pz_serivce` is a web service to manage produce redshift estimates with RAIL.


RAIL is a flexible open-source software library providing tools to produce at-scale photometric redshift data products, including uncertainties and summary statistics, and stress-test them under realistically complex systematics.

RAIL serves as the infrastructure supporting many extragalactic applications of `the Legacy Survey of Space and Time (LSST) <https://www.lsst.org/>`_ on `the Vera C. Rubin Observatory <https://rubinobservatory.org/>`_, including Rubin-wide commissioning activities.
RAIL was initiated by the Photometric Redshifts (PZ) Working Group (WG) of the `LSST Dark Energy Science Collaboration (DESC) <https://lsstdesc.org/>`_ as a result of the lessons learned from the `Data Challenge 1 (DC1) experiment <https://academic.oup.com/mnras/article/499/2/1587/5905416>`_ to enable the PZ WG Deliverables in the `LSST-DESC Science Roadmap (see Sec. 5.18) <https://lsstdesc.org/assets/pdf/docs/DESC_SRM_latest.pdf>`_, aiming to guide the selection and implementation of redshift estimators in DESC analysis pipelines.

RAIL is developed and maintained by a diverse team comprising DESC Pipeline Scientists (PSs), international in-kind contributors, LSST Interdisciplinary Collaboration for Computing (LINCC) Frameworks software engineers, and other volunteers, but all are welcome to join the team regardless of LSST data rights.
To get involved, chime in on the issues in any of the RAIL repositories described in the Overview section.

See `guideline for citing RAIL
<https://rail-hub.readthedocs.io/en/latest/source/citing.html>`_ for
guidance on citing RAIL and the underlying algorithms.


.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   source/overview
   source/installation

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   source/concepts

.. toctree::
   :maxdepth: 2
   :caption: Uploading

   source/initalizing_db
   source/uploading_a_model
   source/uploading_an_estimator
   source/uploading_a_dataset

.. toctree::
   :maxdepth: 2
   :caption: Requests

   source/creating_a_request
   source/running_a_request
   source/exploring_request_results


.. toctree::
   :maxdepth: 2
   :caption: Contributing

   source/contributing

.. toctree::
   :maxdepth: 2
   :caption: CLI Usage

   source/pz_rail_service_admin_cli
   source/pz_rail_service_client_cli
   source/pz_rail_service_server
   source/pz_rail_service_worker


.. toctree::
   :maxdepth: 6
   :caption: API

   api/rail_pz_service
