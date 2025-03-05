************
Installation
************


`rail_pz_service` requires `rail`, and at least some of the RAIL algorithms
to be installs.

Some of the RAIL algorithms have dependencies that are sensitive to out-of-date code versions, therefore it is strongly recommended that you create a new dedicated virtual environment for RAIL to avoid problems with pip/conda failing to update some packages that you have previously installed during installation of RAIL.  Also, having multiple version of RAIL in your path can cause difficult to diagnose problems, so we encourage you to make sure that you don't have an existing version of RAIL installed in your `.local` area or in your base conda environment.



=======================
Production Installation
=======================

Here we will be installing ``rail_pz_service`` into an existing conda environment "[env]".

.. code-block:: bash

    conda activate [env]
    pip install pz-rail-projects


======================
Developer Installation
======================

Here we will be installing the source code from `rail
<https://github.com/LSSTDESC/rail_projects>`_ to be able to develop
the source code.


.. tabs::

   .. group-tab:: General

      .. code-block:: bash

	  conda activate [env]
          git clone https://github.com/LSSTDESC/rail_pz_service.git
          cd rail_pz_service
          pip install -e .[dev]


   .. group-tab:: zsh (e.g., Mac M1+ default)

      .. code-block:: bash

	  conda activate [env]
          git clone https://github.com/LSSTDESC/rail_pz_service.git
          cd rail_pz_service
          pip install -e '.[dev]'


=============
RAIL packages
=============

Depending on how you want to use RAIL you will be installing one or
more `RAIL packages <https://rail-hub.readthedocs.io/en/latest/source/installation.html#rail-packages>`_
