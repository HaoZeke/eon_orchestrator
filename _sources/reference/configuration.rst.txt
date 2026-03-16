=======================
Configuration Reference
=======================

    :Date: 2026-03-13

.. contents::


1 Configuration Reference
-------------------------

Complete reference for ``config/config.yaml`` parameters.

2 System Definitions
--------------------

2.1 ``systems``
~~~~~~~~~~~~~~~

Dictionary of chemical systems to process.

2.1.1 Structure
^^^^^^^^^^^^^^^

.. code:: yaml

    systems:
      system_name:
        reactant: structures/reactant.con  # Path to reactant .con file
        product: structures/product.con    # Path to product .con file
        use_ira: true
        saddle: structures/saddle.con  # Optional: for 2D plots

2.1.2 Parameters
^^^^^^^^^^^^^^^^

.. table::

    +--------------+---------+----------+----------+-------------------------------------+
    | Parameter    | Type    | Required | Default  | Description                         |
    +==============+=========+==========+==========+=====================================+
    | ``reactant`` | string  | Yes      | -        | Path to reactant .con file          |
    +--------------+---------+----------+----------+-------------------------------------+
    | ``product``  | string  | Yes      | -        | Path to product .con file           |
    +--------------+---------+----------+----------+-------------------------------------+
    | ``use_ira``  | boolean | No       | ``true`` | Enable IRA alignment                |
    +--------------+---------+----------+----------+-------------------------------------+
    | ``saddle``   | string  | No       | -        | Path to saddle point (for 2D plots) |
    +--------------+---------+----------+----------+-------------------------------------+

2.1.3 Example
^^^^^^^^^^^^^

.. code:: yaml

    systems:
      hcn_isom:
        reactant: /data/hcn.con
        product: /data/hnc.con
        use_ira: true

      proton_transfer:
        reactant: /data/pt_reactant.con
        product: /data/pt_product.con
        use_ira: true
        saddle: /data/pt_saddle.con

3 Model Configuration
---------------------

3.1 ``model``
~~~~~~~~~~~~~

Machine learning potential settings.

3.1.1 Parameters
^^^^^^^^^^^^^^^^

.. table::

    +-------------+--------+----------+--------------------+--------------------------------------+
    | Parameter   | Type   | Required | Default            | Description                          |
    +=============+========+==========+====================+======================================+
    | ``name``    | string | Yes      | ``pet-mad-v1.1.0`` | Model filename                       |
    +-------------+--------+----------+--------------------+--------------------------------------+
    | ``version`` | string | Yes      | ``v1.1.0``         | HuggingFace version tag              |
    +-------------+--------+----------+--------------------+--------------------------------------+
    | ``type``    | string | No       | ``pet-mad``        | Model type (``pet-mad`` or ``upet``) |
    +-------------+--------+----------+--------------------+--------------------------------------+

3.1.2 Available Models
^^^^^^^^^^^^^^^^^^^^^^

- ``pet-mad-v1.1.0``: PET-MAD v1.1.0 (recommended)

- ``pet-mad-v1.0.0``: PET-MAD v1.0.0 (legacy)

- ``upet``: Universal PET (experimental)

3.1.3 Example
^^^^^^^^^^^^^

.. code:: yaml

    model:
      name: pet-mad-v1.1.0
      version: v1.1.0
      type: pet-mad

4 Compute Settings
------------------

4.1 ``compute``
~~~~~~~~~~~~~~~

Hardware and device configuration.

4.1.1 Parameters
^^^^^^^^^^^^^^^^

.. table::

    +------------+--------+----------+----------+----------------------------+
    | Parameter  | Type   | Required | Default  | Options                    |
    +============+========+==========+==========+============================+
    | ``device`` | string | No       | ``cuda`` | ``cuda``, ``cpu``, ``mps`` |
    +------------+--------+----------+----------+----------------------------+

4.1.2 Device Selection
^^^^^^^^^^^^^^^^^^^^^^

- ``cuda``: NVIDIA GPU (recommended for performance)

- ``cpu``: CPU-only (slower but universally available)

- ``mps``: Apple Silicon (M1/M2/M3)

4.1.3 Example
^^^^^^^^^^^^^

.. code:: yaml

    compute:
      device: cuda

5 Alignment Parameters
----------------------

5.1 ``alignment``
~~~~~~~~~~~~~~~~~

IRA (Iterative Rotational Alignment) settings.

5.1.1 Parameters
^^^^^^^^^^^^^^^^

.. table::

    +-----------+-------+----------+---------+----------+--------------------------------+
    | Parameter | Type  | Required | Default |    Range | Description                    |
    +===========+=======+==========+=========+==========+================================+
    | ``kmax``  | float | No       |     1.8 | 1.0-14.0 | Rotation matching cutoff (Å⁻¹) |
    +-----------+-------+----------+---------+----------+--------------------------------+

5.1.2 Guidelines
^^^^^^^^^^^^^^^^

- **Small molecules** (<20 atoms): 1.5-2.0 Å⁻¹

- **Medium molecules** (20-50 atoms): 2.0-3.0 Å⁻¹

- **Difficult systems**: 3.0-5.0 Å⁻¹

- **2D visualization**: 14 Å⁻¹ (fixed)

5.1.3 Example
^^^^^^^^^^^^^

.. code:: yaml

    alignment:
      kmax: 1.8

6 NEB Parameters
----------------

6.1 ``neb``
~~~~~~~~~~~

Complete NEB calculation settings.

6.1.1 ``neb.minimization``
^^^^^^^^^^^^^^^^^^^^^^^^^^

Endpoint geometry optimization.

.. table::

    +---------------------+--------+-----------+----------------------------+
    | Parameter           | Type   |   Default | Description                |
    +=====================+========+===========+============================+
    | ``max_iterations``  | int    |      2000 | Maximum optimization steps |
    +---------------------+--------+-----------+----------------------------+
    | ``converged_force`` | float  | 0.0514221 | Force threshold (eV/Å)     |
    +---------------------+--------+-----------+----------------------------+
    | ``opt_method``      | string | ``lbfgs`` | Optimizer method           |
    +---------------------+--------+-----------+----------------------------+
    | ``max_move``        | float  |       0.1 | Maximum step size (Å)      |
    +---------------------+--------+-----------+----------------------------+

6.1.2 ``neb.optimization``
^^^^^^^^^^^^^^^^^^^^^^^^^^

NEB calculation parameters.

.. table::

    +---------------------+--------+-----------+------------------------+
    | Parameter           | Type   |   Default | Description            |
    +=====================+========+===========+========================+
    | ``images``          | int    |        18 | Number of NEB images   |
    +---------------------+--------+-----------+------------------------+
    | ``max_iterations``  | int    |      1000 | Maximum NEB iterations |
    +---------------------+--------+-----------+------------------------+
    | ``converged_force`` | float  | 0.0514221 | Force threshold (eV/Å) |
    +---------------------+--------+-----------+------------------------+
    | ``opt_method``      | string | ``lbfgs`` | Optimizer method       |
    +---------------------+--------+-----------+------------------------+
    | ``max_move``        | float  |       0.1 | Maximum step size (Å)  |
    +---------------------+--------+-----------+------------------------+

6.1.2.1 Energy-Weighted Springs
:::::::::::::::::::::::::::::::

.. table::

    +---------------------+-------+----------+---------------------------------+
    | Parameter           | Type  |  Default | Description                     |
    +=====================+=======+==========+=================================+
    | ``energy_weighted`` | bool  | ``true`` | Enable energy weighting         |
    +---------------------+-------+----------+---------------------------------+
    | ``ew_ksp_min``      | float |    0.972 | Minimum spring constant (eV/Å²) |
    +---------------------+-------+----------+---------------------------------+
    | ``ew_ksp_max``      | float |     9.72 | Maximum spring constant (eV/Å²) |
    +---------------------+-------+----------+---------------------------------+
    | ``ew_trigger``      | float |      0.5 | Energy threshold (eV)           |
    +---------------------+-------+----------+---------------------------------+

6.1.2.2 Climbing Image
::::::::::::::::::::::

.. table::

    +---------------------------+-------+----------+-----------------------------+
    | Parameter                 | Type  | Default  | Description                 |
    +===========================+=======+==========+=============================+
    | ``climbing_image_method`` | bool  | ``true`` | Enable CI method            |
    +---------------------------+-------+----------+-----------------------------+
    | ``ci_after_rel``          | float | 0.8      | Relative convergence for CI |
    +---------------------------+-------+----------+-----------------------------+

6.1.2.3 MMF Refinement
::::::::::::::::::::::

.. table::

    +-------------------+------+----------+----------------------+
    | Parameter         | Type | Default  | Description          |
    +===================+======+==========+======================+
    | ``ci_mmf``        | bool | ``true`` | Enable MMF at CI     |
    +-------------------+------+----------+----------------------+
    | ``ci_mmf_nsteps`` | int  | 1000     | MMF refinement steps |
    +-------------------+------+----------+----------------------+

6.1.2.4 SIDPP Initializer
:::::::::::::::::::::::::

.. table::

    +------------------------+-------+---------+-----------------------+
    | Parameter              | Type  | Default | Description           |
    +========================+=======+=========+=======================+
    | ``sidpp_growth_alpha`` | float |    0.33 | Path growth step size |
    +------------------------+-------+---------+-----------------------+

6.1.3 ``neb.idpp``
^^^^^^^^^^^^^^^^^^

Legacy IDPP path generation (optional).

.. table::

    +---------------------------------+------+---------+---------------------+
    | Parameter                       | Type | Default | Description         |
    +=================================+======+=========+=====================+
    | ``number_of_intermediate_imgs`` | int  |      10 | Intermediate images |
    +---------------------------------+------+---------+---------------------+

6.1.4 Example
^^^^^^^^^^^^^

.. code:: yaml

    neb:
      minimization:
        max_iterations: 2000
        converged_force: 0.0514221
        opt_method: lbfgs
        max_move: 0.1

      optimization:
        images: 18
        max_iterations: 1000
        converged_force: 0.0514221
        opt_method: lbfgs
        max_move: 0.1

        energy_weighted: true
        ew_ksp_min: 0.972
        ew_ksp_max: 9.72
        ew_trigger: 0.5

        climbing_image_method: true
        ci_after_rel: 0.8

        ci_mmf: true
        ci_mmf_nsteps: 1000

        sidpp_growth_alpha: 0.33

      idpp:
        number_of_intermediate_imgs: 10

7 Visualization Parameters
--------------------------

7.1 ``plotting``
~~~~~~~~~~~~~~~~

Plot generation settings.

7.1.1 General
^^^^^^^^^^^^^

.. table::

    +---------------------+--------+-----------+---------------------------+
    | Parameter           | Type   | Default   | Description               |
    +=====================+========+===========+===========================+
    | ``plot_structures`` | bool   | ``true``  | Overlay atomic structures |
    +---------------------+--------+-----------+---------------------------+
    | ``facecolor``       | string | ``white`` | Background color          |
    +---------------------+--------+-----------+---------------------------+
    | ``title``           | string | ``""``    | Plot title prefix         |
    +---------------------+--------+-----------+---------------------------+

7.1.2 Figure Settings
^^^^^^^^^^^^^^^^^^^^^

.. table::

    +----------------+-------+------------+-----------------------+
    | Parameter      | Type  |    Default | Description           |
    +================+=======+============+=======================+
    | ``figsize``    | list  | ``[8, 6]`` | Figure size (inches)  |
    +----------------+-------+------------+-----------------------+
    | ``dpi``        | int   |        300 | Output resolution     |
    +----------------+-------+------------+-----------------------+
    | ``zoom_ratio`` | float |        1.0 | Structure zoom factor |
    +----------------+-------+------------+-----------------------+

7.1.3 Fonts
^^^^^^^^^^^

.. table::

    +-----------+------+---------+----------------+
    | Parameter | Type | Default | Description    |
    +===========+======+=========+================+
    | ``base``  | int  |      12 | Base font size |
    +-----------+------+---------+----------------+

7.1.4 Structure Overlays
^^^^^^^^^^^^^^^^^^^^^^^^

.. table::

    +-----------------------+-------+---------+-------------------------+
    | Parameter             | Type  | Default | Description             |
    +=======================+=======+=========+=========================+
    | ``draw_reactant.x``   | float |     0.2 | X position (normalized) |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_reactant.y``   | float |     0.1 | Y position (normalized) |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_reactant.rad`` | float |    0.15 | Circle radius           |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_product.x``    | float |     0.8 | X position              |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_product.y``    | float |     0.1 | Y position              |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_product.rad``  | float |    0.15 | Circle radius           |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_saddle.x``     | float |     0.5 | X position              |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_saddle.y``     | float |     0.6 | Y position              |
    +-----------------------+-------+---------+-------------------------+
    | ``draw_saddle.rad``   | float |    0.15 | Circle radius           |
    +-----------------------+-------+---------+-------------------------+

7.1.5 Advanced
^^^^^^^^^^^^^^

.. table::

    +--------------+-------+---------+------------------------+
    | Parameter    | Type  | Default | Description            |
    +==============+=======+=========+========================+
    | ``ira_kmax`` | float |      14 | IRA kmax for 2D plots  |
    +--------------+-------+---------+------------------------+
    | ``aserot``   | float |       0 | ASE rotation (degrees) |
    +--------------+-------+---------+------------------------+

7.1.6 Example
^^^^^^^^^^^^^

.. code:: yaml

    plotting:
      plot_structures: true
      facecolor: white
      title: "HCN → HNC"

      figure:
        figsize: [8, 6]
        dpi: 300
        zoom_ratio: 1.0

      fonts:
        base: 12

      draw_reactant:
        x: 0.2
        y: 0.1
        rad: 0.15

      draw_product:
        x: 0.8
        y: 0.1
        rad: 0.15

      draw_saddle:
        x: 0.5
        y: 0.6
        rad: 0.15

      ira_kmax: 14
      aserot: 0

8 Path Configuration
--------------------

8.1 ``paths``
~~~~~~~~~~~~~

Output directory structure.

8.1.1 Parameters
^^^^^^^^^^^^^^^^

.. table::

    +---------------+--------+-----------------------+-----------------------+
    | Parameter     | Type   | Default               | Description           |
    +===============+========+=======================+=======================+
    | ``models``    | string | ``results/models``    | ML potential storage  |
    +---------------+--------+-----------------------+-----------------------+
    | ``endpoints`` | string | ``results/endpoints`` | Endpoint structures   |
    +---------------+--------+-----------------------+-----------------------+
    | ``neb``       | string | ``results/neb``       | NEB outputs           |
    +---------------+--------+-----------------------+-----------------------+
    | ``idpp``      | string | ``results/idpp``      | IDPP paths            |
    +---------------+--------+-----------------------+-----------------------+
    | ``plots``     | string | ``results/plots``     | Visualization outputs |
    +---------------+--------+-----------------------+-----------------------+
    | ``cache``     | string | ``results/cache``     | Cache files           |
    +---------------+--------+-----------------------+-----------------------+

8.1.2 Example
^^^^^^^^^^^^^

.. code:: yaml

    paths:
      models: results/models
      endpoints: results/endpoints
      neb: results/neb
      idpp: results/idpp
      plots: results/plots
      cache: results/cache

9 Complete Configuration Example
--------------------------------

.. code:: yaml

    systems:
      hcn_isom:
        reactant: /data/hcn.con
        product: /data/hnc.con
        use_ira: true

    model:
      name: pet-mad-v1.1.0
      version: v1.1.0
      type: pet-mad

    compute:
      device: cuda

    alignment:
      kmax: 1.8

    neb:
      minimization:
        max_iterations: 2000
        converged_force: 0.0514221
        opt_method: lbfgs
        max_move: 0.1

      optimization:
        images: 18
        max_iterations: 1000
        converged_force: 0.0514221
        energy_weighted: true
        ew_ksp_min: 0.972
        ew_ksp_max: 9.72
        climbing_image_method: true
        ci_mmf: true
        sidpp_growth_alpha: 0.33

    plotting:
      plot_structures: true
      figure:
        figsize: [8, 6]
        dpi: 300

    paths:
      models: results/models
      endpoints: results/endpoints
      neb: results/neb
      plots: results/plots
