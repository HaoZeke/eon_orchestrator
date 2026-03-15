==========================
HCN Isomerization Tutorial
==========================

    :Date: 2026-03-14


1 Overview
----------

HCN → HNC isomerization is the simplest NEB example (3 atoms). Use this to validate your installation.

2 Reaction
----------

Linear hydrogen cyanide isomerizes to hydrogen isocyanide:

HCN (reactant) → [TS] → HNC (product)

Expected barrier: ~1.8 eV with PET-MAD-XS v1.5.0

3 Running the Example
---------------------

.. code:: bash

    cd eon_orchestrator

    # Dry-run (validates workflow, no eOn needed)
    pixi run validate

    # Full calculation (requires eOn)
    pixi run -e eon hcn

4 Expected Outputs
------------------

4.1 NEB Results
~~~~~~~~~~~~~~~

.. code:: bash

    cat results/neb/hcn_isom/results.dat

Should show:

- 18-20 images

- Barrier around image 9-10 (climbing image)

- Energy ~0.07-0.09 eV above reactant

4.2 Plots
~~~~~~~~~

- ``results/plots/hcn_isom/1D_path.png`` - Energy profile

- ``results/plots/hcn_isom/1D_index.png`` - Energy vs image index

5 IRA Alignment
---------------

For this simple linear isomerization, IRA provides minimal benefit. The real value is shown in more complex examples (SN2, Diels-Alder).

6 Next Steps
------------

After validating with HCN:

1. Try `SN2 reaction <sn2.rst>`_ (6 atoms, backside attack)

2. Try `Vinyl alcohol <vinyl_alcohol.rst>`_ (8 atoms, H-transfer)

3. Try `Diels-Alder <diels_alder.rst>`_ (16 atoms, ring closure)
