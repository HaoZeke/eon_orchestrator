=========
Changelog
=========

    :Date: 2026-03-13


1 Changelog
-----------

All notable changes to NEB Orchestrator are documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.1.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

2 [Unreleased]
--------------

2.1 Added
~~~~~~~~~

- Initial workflow structure with modular Snakemake rules

- PET-MAD/uPET model retrieval from HuggingFace

- IRA alignment for endpoint preparation

- CI-NEB optimization with energy-weighted springs

- MMF refinement at climbing image

- 1D and 2D visualization with rgpycrumbs

- Example HCN isomerization system

- GitHub Actions CI/CD workflows

- Sphinx documentation with Shibuya theme

2.2 Changed
~~~~~~~~~~~

- None yet

2.3 Deprecated
~~~~~~~~~~~~~~

- None yet

2.4 Removed
~~~~~~~~~~~

- None yet

2.5 Fixed
~~~~~~~~~

- None yet

2.6 Security
~~~~~~~~~~~~

- None yet

3 [0.1.0] - 2026-03-13
----------------------

3.1 Added
~~~~~~~~~

- Initial release

- Core workflow orchestration

- Seven modular rule files

- Six conda environment specifications

- Comprehensive configuration with defaults

- Tutorial documentation (Diataxis structure)

- Reference documentation

- Example system (HCN isomerization)

4 Version History
-----------------

.. table::

    +---------+------------+-----------------+
    | Version |       Date | Description     |
    +=========+============+=================+
    |   0.1.0 | 2026-03-13 | Initial release |
    +---------+------------+-----------------+

5 Upcoming Features (Roadmap)
-----------------------------

5.1 Planned for v0.2.0
~~~~~~~~~~~~~~~~~~~~~~

- DFT single-point validation step

- Multiple model ensemble support

- Descriptor-based extrapolation detection

- Additional example systems

- Performance benchmarks

5.2 Under Consideration
~~~~~~~~~~~~~~~~~~~~~~~

- QM/MM support for enzymatic systems

- Surface reaction templates

- Automated parameter tuning

- MLflow experiment tracking integration

- Real-time workflow monitoring dashboard

6 Migration Guide
-----------------

6.1 From v0.1.0 to v0.2.0 (Planned)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No breaking changes expected. New features will be additive.

7 Contributors
--------------

- Built on eOn (`https://eondocs.org <https://eondocs.org>`_)

- Uses PET-MAD (`https://huggingface.co/lab-cosmo/pet-mad <https://huggingface.co/lab-cosmo/pet-mad>`_)

- Visualization with rgpycrumbs
