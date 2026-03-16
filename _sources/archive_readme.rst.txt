=============================
NEB Orchestrator Data Archive
=============================


Data archive for "Reproducible orchestration of best practices for reaction
path optimization with the nudged elastic band" (MethodsX, 2026).

Rehydrating
-----------

Extract at the repository root to recreate the computation state:

.. code:: bash

    git clone https://github.com/HaoZeke/eon_orchestrator
    cd eon_orchestrator
    tar -xJf neb_orchestrator_data.tar.xz

All Snakemake targets will show as up-to-date after extraction.

Data layout
-----------

.. code:: text

    results/
      models/
        pet-mad-xs-v1.5.0.pt          # PET-MAD ML potential (PyTorch, 20 MB)
      endpoints/{system}/
        reactant_pre_aligned.con       # Raw aligned endpoint (eOn .con)
        product_pre_aligned.con
        reactant_minimized.con         # After geometry optimization
        product_minimized.con
        reactant.con                   # Final (post-minimization IRA alignment)
        product.con
      neb/{system}/
        config.ini                     # eOn configuration used for this run
        results.dat                    # Summary: barrier, force calls, convergence
        neb.con                        # Final NEB band (all images, eOn .con)
        neb.dat                        # Final image energies and forces
        neb_NNN.dat                    # Per-iteration energy/force data (plain text)
        neb_path_NNN.con               # Per-iteration path snapshots (eOn .con)
        climb.con                      # Climbing image geometry
      plots/{system}/
        1D_path.png                    # Energy vs cumulative RMSD
        1D_index.png                   # Energy vs image index
        2D_rmsd.png                    # 2D RMSD landscape projection
      cache/{system}/
        ...                            # Intermediate files from visualization
    config/
      config.yaml                      # Default workflow parameters
    examples/*/config.yaml             # Per-system parameter overrides
    README.org                         # Repository documentation

Systems
-------

.. table::

    +--------------------+-------+-----------+----------------------------------+--------+
    | System             | Atoms | Formula   | Transition                       | Images |
    +====================+=======+===========+==================================+========+
    | hcn\_isom          |     3 | HCN       | HCN to HNC proton transfer       |     18 |
    +--------------------+-------+-----------+----------------------------------+--------+
    | sn2\_f\_ch3f       |     6 | CH3F2     | F- + CH3F backside attack        |     17 |
    +--------------------+-------+-----------+----------------------------------+--------+
    | diels\_alder       |    16 | C6H10     | Butadiene + ethylene [4+2]       |     20 |
    +--------------------+-------+-----------+----------------------------------+--------+
    | vinyl\_alcohol     |     7 | C2H4O     | Keto-enol tautomerization        |     17 |
    +--------------------+-------+-----------+----------------------------------+--------+
    | alanine\_dipeptide |    22 | C6H12N2O2 | C7eq to C5 conformational change |     21 |
    +--------------------+-------+-----------+----------------------------------+--------+

File formats
------------

``.con``
    eOn configuration format (plain text, positions + cell + atom types).
    Readable with ASE: ``ase.io.read("file.con")``.

``.dat``
    Plain text, space-delimited columns (energy, force, projected force).

``.ini``
    Plain text INI format (eOn run configuration).

``.pt``
    PyTorch serialized model (PET-MAD v1.5.0 ML potential).
    Loadable with ``torch.load("file.pt")`` or via metatrain/metatomic.

``.png``
    PNG images (300 DPI, publication quality).

``.yaml``
    YAML configuration files.

Reproducing from scratch
------------------------

To regenerate all results (requires eOn client):

.. code:: bash

    pixi install -e eon
    pixi run -e eon hcn           # ~1 min
    pixi run -e eon sn2           # ~1 min
    pixi run -e eon diels-alder   # ~2 min
    pixi run -e eon vinyl-alcohol # ~2 min
    pixi run -e eon alanine       # ~8 min

Software versions
-----------------

- eOn: >= 2.12.0

- PET-MAD: v1.5.0 (lab-cosmo/pet-mad on HuggingFace)

- rgpycrumbs: >= 0.1.0

- Snakemake: >= 9.0

- Python: 3.11-3.12

License
-------

MIT. See LICENSE in the repository.

Citation
--------

See CITATION.cff in the repository.
