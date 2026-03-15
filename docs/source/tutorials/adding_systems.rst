======================
Adding Your Own System
======================

    :Date: 2026-03-14


1 Overview
----------

This guide shows how to run NEB calculations for your own molecular system.

2 Prerequisites
---------------

1. Reactant structure (.con or .xyz format)

2. Product structure (.con or .xyz format)

3. Consistent atom ordering between reactant and product

3 Step 1: Prepare Structures
----------------------------

3.1 Format Requirements
~~~~~~~~~~~~~~~~~~~~~~~

Structures must be in eOn .con format or XYZ format:

.. code:: text

    # XYZ format example
    8
    Vinyl alcohol reactant
    C       1.164677    -0.148453    -0.000063
    C      -0.234846     0.398467    -0.000072
    O      -1.230293    -0.277273    -0.000759
    H       1.700217     0.223795    -0.879975
    H       1.699762     0.222662     0.880605
    H      -0.313062     1.507686     0.000618
    H       1.150482    -1.238676    -0.000768
    H      -2.154321     0.345678     0.000123

3.2 Atom Ordering
~~~~~~~~~~~~~~~~~

**Critical**: Reactant and product must have the same atom order.

Correct (H atom maps to H atom):

.. code:: text

    Reactant: C1 C2 O3 H4 H5 H6 H7 H8
    Product:  C1 C2 O3 H4 H5 H6 H7 H8

Incorrect (atoms scrambled):

.. code:: text

    Reactant: C1 C2 O3 H4 H5 H6 H7 H8
    Product:  C2 C1 O3 H5 H4 H8 H7 H6  # Wrong!

3.3 Box Size
~~~~~~~~~~~~

For gas-phase molecules, use a 25 Å cubic box:

.. code:: text

    25.000000   25.000000   25.000000 
    90.000000   90.000000   90.000000

4 Step 2: Create Configuration
------------------------------

Copy an example and modify:

.. code:: bash

    cd eon_orchestrator
    cp examples/hcn_isom/config.yaml my_system.yaml

Edit ``my_system.yaml``:

.. code:: yaml

    systems:
      my_reaction:  # Your system name
        reactant: /absolute/path/to/reactant.xyz
        product: /absolute/path/to/product.xyz
        use_ira: true  # Enable IRA alignment

    model:
      name: pet-mad-xs-v1.5.0
      version: v1.5.0
      type: pet-mad-xs

    compute:
      device: cpu  # or cuda if you have GPU

    # Adjust for your system size
    neb:
      optimization:
        images: 18  # 12-16 for small, 18-24 for medium, 24-30 for large

5 Step 3: Validate Configuration
--------------------------------

.. code:: bash

    # Check YAML syntax
    yamllint my_system.yaml

    # Dry-run workflow (no eOn needed)
    snakemake --configfile my_system.yaml -n

Expected output: Shows ~10 jobs in DAG

6 Step 4: Run NEB Calculation
-----------------------------

#+begin\ :sub:`src`\ bash

snakemake --configfile my\ :sub:`system.yaml`\ -c4#+end\ :sub:`src`\

7 Step 5: Check Results
-----------------------

.. code:: bash

    # Check NEB converged
    cat results/neb/my_reaction/results.dat

    # View plots
    ls results/plots/my_reaction/
    # Should have: 1D_path.png, 1D_index.png, 2D_rmsd.png

7.1 Expected Barrier Range
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. table::

    +---------------+-----------------+
    | System Type   | Typical Barrier |
    +===============+=================+
    | Isomerization | 0.5-2.5 eV      |
    +---------------+-----------------+
    | H-transfer    | 0.3-1.5 eV      |
    +---------------+-----------------+
    | Bond breaking | 1.0-3.0 eV      |
    +---------------+-----------------+
    | Ring closure  | 0.8-2.0 eV      |
    +---------------+-----------------+

If barrier > 5 eV, check:

1. Atom ordering (most common issue)

2. Structure quality (no steric clashes)

3. IRA alignment (try different kmax)

8 Troubleshooting
-----------------

8.1 High Barrier (>5 eV)
~~~~~~~~~~~~~~~~~~~~~~~~

Most likely cause: wrong atom permutation

Solution:

1. Visualize IDPP path: ``ase gui results/idpp/my_reaction/path/*.xyz``

2. Check for atomic collisions

3. Manually reorder atoms if needed

8.2 NEB Doesn't Converge
~~~~~~~~~~~~~~~~~~~~~~~~

Try:

.. code:: yaml

    neb:
      optimization:
        images: 24  # Increase from 18
        max_iterations: 2000  # Increase from 1000
        max_move: 0.05  # Reduce from 0.1

8.3 IRA Alignment Fails
~~~~~~~~~~~~~~~~~~~~~~~

Try higher kmax:

.. code:: yaml

    alignment:
      kmax: 3.0  # Increase from 1.8

9 Example: Adding Formaldehyde Isomerization
--------------------------------------------

9.1 1. Prepare Structures
~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``formaldehyde/reactant.xyz`` and ``formaldehyde/product.xyz``

9.2 2. Create Config
~~~~~~~~~~~~~~~~~~~~

.. code:: yaml

    systems:
      formaldehyde:
        reactant: /path/to/formaldehyde/reactant.xyz
        product: /path/to/formaldehyde/product.xyz
        use_ira: true

    model:
      name: pet-mad-xs-v1.5.0
      version: v1.5.0

    compute:
      device: cpu

    neb:
      optimization:
        images: 16  # 6 atoms, simple reaction

9.3 3. Run
~~~~~~~~~~

#+begin\ :sub:`src`\ bash
snakemake --configfile formaldehyde/config.yaml -c4#+end\ :sub:`src`\

10 Next Steps
-------------

- `Parameter Guide <../parameter_guide.rst>`_ - Fine-tune parameters

- `Developer Notes <../devnotes.rst>`_ - Advanced usage

- `Reference <../reference/>`_ - Full parameter documentation
