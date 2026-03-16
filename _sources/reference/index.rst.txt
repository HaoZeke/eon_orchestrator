=======================
Configuration Reference
=======================

    :Date: 2026-03-14


1 Configuration Reference
-------------------------

Complete parameter reference for ``config.yaml``.

2 System Definitions
--------------------

.. code:: yaml

    systems:
      my_reaction:
        reactant: /path/to/reactant.con
        product: /path/to/product.con
        use_ira: true  # Enable IRA alignment

.. table::

    +--------------+------+----------+--------------------------------------+
    | Parameter    | Type | Required | Description                          |
    +==============+======+==========+======================================+
    | ``reactant`` | path | Yes      | Reactant structure (.con or .xyz)    |
    +--------------+------+----------+--------------------------------------+
    | ``product``  | path | Yes      | Product structure (.con or .xyz)     |
    +--------------+------+----------+--------------------------------------+
    | ``use_ira``  | bool | No       | Enable IRA alignment (default: true) |
    +--------------+------+----------+--------------------------------------+

3 Model Configuration
---------------------

.. code:: yaml

    model:
      name: pet-mad-xs-v1.5.0
      version: v1.5.0
      type: pet-mad-xs

.. table::

    +-------------+--------+-----------------------+---------------------+
    | Parameter   | Type   | Default               | Description         |
    +=============+========+=======================+=====================+
    | ``name``    | string | ``pet-mad-xs-v1.5.0`` | Model name          |
    +-------------+--------+-----------------------+---------------------+
    | ``version`` | string | ``v1.5.0``            | HuggingFace version |
    +-------------+--------+-----------------------+---------------------+
    | ``type``    | string | ``pet-mad-xs``        | Model type          |
    +-------------+--------+-----------------------+---------------------+

3.1 Available Models
~~~~~~~~~~~~~~~~~~~~

.. table::

    +----------------+-------------+----------+---------------+
    | Model          | Size        | Accuracy | Use Case      |
    +================+=============+==========+===============+
    | ``pet-mad-xs`` | Extra small | Good     | Quick testing |
    +----------------+-------------+----------+---------------+
    | ``pet-mad-s``  | Small       | Better   | Production    |
    +----------------+-------------+----------+---------------+
    | ``pet-mad``    | Medium      | Best     | High accuracy |
    +----------------+-------------+----------+---------------+

4 Compute Settings
------------------

.. code:: yaml

    compute:
      device: cuda  # or cpu, mps

.. table::

    +------------+--------+----------+----------------+
    | Parameter  | Type   | Default  | Description    |
    +============+========+==========+================+
    | ``device`` | string | ``cuda`` | Compute device |
    +------------+--------+----------+----------------+

5 Alignment Parameters
----------------------

.. code:: yaml

    alignment:
      kmax: 1.8  # Å⁻¹

.. table::

    +-----------+-------+---------+---------------------+
    | Parameter | Type  | Default | Description         |
    +===========+=======+=========+=====================+
    | ``kmax``  | float |     1.8 | IRA matching cutoff |
    +-----------+-------+---------+---------------------+

5.1 Choosing kmax
~~~~~~~~~~~~~~~~~

.. table::

    +-------------------+------------+
    | System Type       | kmax Range |
    +===================+============+
    | Small molecules   |    1.5-2.0 |
    +-------------------+------------+
    | Medium molecules  |    2.0-3.0 |
    +-------------------+------------+
    | Difficult mapping |    3.0-5.0 |
    +-------------------+------------+

6 NEB Parameters
----------------

6.1 Minimization
~~~~~~~~~~~~~~~~

.. code:: yaml

    neb:
      minimization:
        max_iterations: 2000
        converged_force: 0.0514221  # eV/Å
        opt_method: lbfgs
        max_move: 0.1  # Å

.. table::

    +---------------------+--------+-----------+------------------------+
    | Parameter           | Type   |   Default | Description            |
    +=====================+========+===========+========================+
    | ``max_iterations``  | int    |      2000 | Max minimization steps |
    +---------------------+--------+-----------+------------------------+
    | ``converged_force`` | float  |    0.0514 | Force tolerance (eV/Å) |
    +---------------------+--------+-----------+------------------------+
    | ``opt_method``      | string | ``lbfgs`` | Optimizer              |
    +---------------------+--------+-----------+------------------------+
    | ``max_move``        | float  |       0.1 | Max step size (Å)      |
    +---------------------+--------+-----------+------------------------+

6.2 Optimization
~~~~~~~~~~~~~~~~

.. code:: yaml

    neb:
      optimization:
        images: 18
        max_iterations: 1000
        converged_force: 0.0514221
        opt_method: lbfgs
        max_move: 0.1

        # Energy-weighted springs
        energy_weighted: true
        ew_ksp_min: 0.972  # eV/Å²
        ew_ksp_max: 9.72   # eV/Å²
        ew_trigger: 0.5    # eV

        # Climbing image
        climbing_image_method: true
        ci_after_rel: 0.8

        # MMF refinement
        ci_mmf: true
        ci_mmf_nsteps: 1000

        # IDPP initializer
        sidpp_growth_alpha: 0.33

.. table::

    +---------------------------+-------+---------+-------------------------+
    | Parameter                 | Type  | Default | Description             |
    +===========================+=======+=========+=========================+
    | ``images``                | int   |      18 | Number of NEB images    |
    +---------------------------+-------+---------+-------------------------+
    | ``max_iterations``        | int   |    1000 | Max NEB iterations      |
    +---------------------------+-------+---------+-------------------------+
    | ``converged_force``       | float |  0.0514 | Force tolerance         |
    +---------------------------+-------+---------+-------------------------+
    | ``energy_weighted``       | bool  |    true | Energy-weighted springs |
    +---------------------------+-------+---------+-------------------------+
    | ``ew_ksp_min``            | float |   0.972 | Min spring constant     |
    +---------------------------+-------+---------+-------------------------+
    | ``ew_ksp_max``            | float |    9.72 | Max spring constant     |
    +---------------------------+-------+---------+-------------------------+
    | ``climbing_image_method`` | bool  |    true | Enable CI               |
    +---------------------------+-------+---------+-------------------------+
    | ``ci_mmf``                | bool  |    true | MMF refinement          |
    +---------------------------+-------+---------+-------------------------+

6.3 Choosing Number of Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. table::

    +---------------------+--------+
    | System Complexity   | Images |
    +=====================+========+
    | Simple (3-5 atoms)  |  12-16 |
    +---------------------+--------+
    | Medium (6-15 atoms) |  18-24 |
    +---------------------+--------+
    | Complex (16+ atoms) |  24-30 |
    +---------------------+--------+

7 Plotting Parameters
---------------------

.. code:: yaml

    plotting:
      plot_structures: true
      facecolor: white
      title: ""

      figure:
        figsize: [8, 6]
        dpi: 300
        zoom_ratio: 0.3

      fonts:
        base: 12

      ira_kmax: 14  # For 2D RMSD

.. table::

    +---------------------+-------+---------+-----------------------+
    | Parameter           | Type  | Default | Description           |
    +=====================+=======+=========+=======================+
    | ``plot_structures`` | bool  |    true | Show structure insets |
    +---------------------+-------+---------+-----------------------+
    | ``zoom_ratio``      | float |     0.3 | Inset zoom level      |
    +---------------------+-------+---------+-----------------------+
    | ``ira_kmax``        | float |      14 | RMSD calculation kmax |
    +---------------------+-------+---------+-----------------------+

8 Path Configuration
--------------------

.. code:: yaml

    paths:
      models: results/models
      endpoints: results/endpoints
      neb: results/neb
      idpp: results/idpp
      plots: results/plots
      cache: results/cache

All paths are relative to working directory.
