=========
Tutorials
=========


Step-by-step guides for running NEB calculations.

Start with `HCN Isomerization <hcn.rst>`_ to validate your installation,
then work through increasing complexity.

.. toctree::
   :maxdepth: 1

   hcn
   sn2
   vinyl_alcohol
   diels_alder
   adding_systems

Examples by Complexity
----------------------

Beginner (1-5 atoms)
~~~~~~~~~~~~~~~~~~~~

- `HCN → HNC Isomerization <hcn.rst>`_

  - 3 atoms, linear H-transfer

  - Validates installation

  - Expected barrier: ~1.8 eV

  - Run: ``pixi run -e eon hcn``

Intermediate (6-10 atoms)
~~~~~~~~~~~~~~~~~~~~~~~~~

- `S\_N2 Reaction <sn2.rst>`_

  - 6 atoms, backside attack

  - Demonstrates IRA value

  - Expected barrier: ~1.1 eV

  - Run: ``pixi run -e eon sn2``

- `Vinyl Alcohol Tautomerization <vinyl_alcohol.rst>`_

  - 8 atoms, H-transfer

  - Keto-enol tautomerization

  - Expected barrier: ~2.2 eV

  - Run: ``pixi run -e eon vinyl-alcohol``

Advanced (10+ atoms)
~~~~~~~~~~~~~~~~~~~~

- `Diels-Alder Reaction <diels_alder.rst>`_

  - 16 atoms, ring closure

  - Multi-molecular reaction

  - Expected barrier: ~1.2 eV

  - Run: ``pixi run -e eon diels-alder``

Your Own System
---------------

- `Add Your Own System <adding_systems.rst>`_ - Complete step-by-step guide

  - Structure preparation

  - Configuration

  - Validation

  - Troubleshooting

Common Issues
-------------

.. table::

    +----------------------+--------------------------------------+
    | Problem              | Solution                             |
    +======================+======================================+
    | eonclient not found  | Install with ``pixi install -e eon`` |
    +----------------------+--------------------------------------+
    | Plotting fails       | Check ``RGPYCRUMBS_AUTO_DEPS=1``     |
    +----------------------+--------------------------------------+
    | High barrier (>5 eV) | Check atom permutation               |
    +----------------------+--------------------------------------+
    | NEB doesn't converge | Increase images, reduce max\_move    |
    +----------------------+--------------------------------------+

Next Steps
----------

- `Parameter Guide <../parameter_guide.rst>`_ - Choosing NEB parameters

- `Developer Notes <../devnotes.rst>`_ - Extending the workflow

- `Reference <../reference/>`_ - API documentation
