================
Quickstart Guide
================

    :Date: 2026-03-14


1 Prerequisites
---------------

1. pixi installed (`https://pixi.sh <https://pixi.sh>`_)

2. Git

2 Installation
--------------

.. code:: bash

    # Clone repository
    git clone https://github.com/HaoZeke/eon_orchestrator.git
    cd eon_orchestrator

    # Install dependencies (includes eOn)
    pixi install -e eon

3 Quick Validation
------------------

Test workflow without running NEB (no eOn client needed):

.. code:: bash

    pixi run validate

Expected: Shows DAG with ~10 jobs

4 Run Your First NEB
--------------------

.. code:: bash

    # HCN isomerization (3 atoms, ~2 min)
    pixi run -e eon hcn

    # Check results
    cat results/neb/hcn_isom/results.dat
    ls -lh results/plots/hcn_isom/

5 Available Examples
--------------------

.. table::

    +-----------------------------------+-------------+-------+--------+
    | Command                           | System      | Atoms | Time   |
    +===================================+=============+=======+========+
    | ``pixi run -e eon hcn``           | HCN → HNC   |     3 | 2 min  |
    +-----------------------------------+-------------+-------+--------+
    | ``pixi run -e eon sn2``           | F⁻ + CH₃F   |     6 | 3 min  |
    +-----------------------------------+-------------+-------+--------+
    | ``pixi run -e eon vinyl-alcohol`` | Enol → Keto |     8 | 5 min  |
    +-----------------------------------+-------------+-------+--------+
    | ``pixi run -e eon diels-alder``   | Diels-Alder |    16 | 10 min |
    +-----------------------------------+-------------+-------+--------+

6 Your Own System
-----------------

1. Copy example config:

.. code:: bash

    cp examples/hcn_isom/config.yaml my_system.yaml

1. Edit paths to your structures:

.. code:: yaml

    systems:
      my_reaction:
        reactant: /path/to/reactant.con
        product: /path/to/product.con
        use_ira: true

1. Run:

#+begin\ :sub:`src`\ bash
snakemake --configfile my\ :sub:`system.yaml`\ -c4#+end\ :sub:`src`\

7 Next Steps
------------

- `HCN Tutorial <tutorials/hcn.rst>`_ - Detailed walkthrough

- `Parameter Guide <parameter_guide.rst>`_ - Choosing NEB parameters

- `Developer Notes <devnotes.rst>`_ - Extending the workflow

8 Citation
----------

R. Goswami, M. Gunde, and H. Jónsson, arXiv:2601.12630 (2026).
doi: `10.48550/arXiv.2601.12630 <https://doi.org/10.48550/arXiv.2601.12630>`_
