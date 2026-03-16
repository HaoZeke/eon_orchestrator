===============
Developer Notes
===============

    :Date: 2026-03-14


1 Extending the Workflow
------------------------

1.1 Adding New Rules
~~~~~~~~~~~~~~~~~~~~

Rules are in ``workflow/rules/*.smk``. Each rule should:

1. Have clear docstring explaining purpose

2. Use wildcards for system-agnostic operation

3. Specify inputs/outputs explicitly

4. Use conda environments for reproducibility

Example rule template:

.. code:: python

    rule my_new_rule:
        """
        Description of what this rule does.

        Inputs:
            - input1: Description
        Outputs:
            - output1: Description
        """
        input:
            input1=config['paths']['neb'] + '/{system}/input.con',
        output:
            output1=config['paths']['neb'] + '/{system}/output.dat',
        params:
            # Parameters from config
            param1=config.get('my_section', {}).get('param1', 'default'),
        shell:
            """
            my_command {input.input1} {output.output1} --param {params.param1}
            """

1.2 Rule Categories
~~~~~~~~~~~~~~~~~~~

- ``get_model.smk`` - Model retrieval

- ``align_endpoints.smk`` - IRA alignment

- ``minimize.smk`` - Geometry optimization

- ``generate_idpp.smk`` - IDPP path generation

- ``run_neb.smk`` - NEB optimization

- ``visualize.smk`` - Plotting

- ``validate_path.smk`` - Path validation

1.3 Adding to Target Rule
~~~~~~~~~~~~~~~~~~~~~~~~~

Update ``rule all`` in ``workflow/Snakefile`` to include new outputs:

.. code:: python

    rule all:
        input:
            expand(
                [
                    # Existing outputs...
                    config['paths']['plots'] + '/{system}/my_new_plot.png',
                ],
                system=list(config.get('systems', {}).keys())
            )

2 Modifying Parameters
----------------------

2.1 Configuration Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. ``config/config.yaml`` - Global defaults

2. ``examples/*/config.yaml`` - Example-specific overrides

3. Command-line: ``--config systems.my_system.param=value``

2.2 Key Parameters
~~~~~~~~~~~~~~~~~~

.. table::

    +----------------------+---------------------+---------+---------------------------+
    | Section              | Parameter           | Default | Description               |
    +======================+=====================+=========+===========================+
    | ``neb.optimization`` | ``images``          |      18 | Number of NEB images      |
    +----------------------+---------------------+---------+---------------------------+
    | ``neb.optimization`` | ``converged_force`` |  0.0514 | Force tolerance (eV/Å)    |
    +----------------------+---------------------+---------+---------------------------+
    | ``neb.optimization`` | ``energy_weighted`` |    true | Energy-weighted springs   |
    +----------------------+---------------------+---------+---------------------------+
    | ``alignment``        | ``kmax``            |     1.8 | IRA matching cutoff (Å⁻¹) |
    +----------------------+---------------------+---------+---------------------------+
    | ``plotting.figure``  | ``zoom_ratio``      |     0.3 | Structure inset zoom      |
    +----------------------+---------------------+---------+---------------------------+
    | ``plotting``         | ``ira_kmax``        |      14 | RMSD calculation kmax     |
    +----------------------+---------------------+---------+---------------------------+

2.3 Testing Parameter Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    # Dry-run to check DAG changes
    pixi run validate

    # Run single system
    snakemake --configfile my_config.yaml -c4
    # Force re-run with new params
    snakemake --configfile my_config.yaml -c4 --use-conda --rerun-incomplete

3 Using as Snakemake Module
---------------------------

3.1 Basic Module Usage
~~~~~~~~~~~~~~~~~~~~~~

In your workflow's ``Snakefile``:

.. code:: python

    # Import NEB Orchestrator as module
    module neb_orchestrator:
        snakefile: "path/to/eon_orchestrator/workflow/Snakefile"
        config: config["neb"]  # Your NEB config section

    # Use rules from module
    use rule * from neb_orchestrator as neb_*

3.2 Your Configuration
~~~~~~~~~~~~~~~~~~~~~~

In your ``config.yaml``:

.. code:: yaml

    neb:
      systems:
        my_reaction:
          reactant: /path/to/reactant.con
          product: /path/to/product.con
          use_ira: true

      model:
        name: pet-mad-xs-v1.5.0
        version: v1.5.0

      compute:
        device: cpu  # or cuda

      neb:
        optimization:
          images: 18
          converged_force: 0.0514221

3.3 Chaining with Your Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    # Your workflow
    rule all:
        input:
            "analysis/my_reaction/summary.txt"

    # Run NEB first
    rule run_neb:
        input:
            neb_results=rules.neb_run_neb.output.results_dat
        output:
            "analysis/{system}/summary.txt"
        script:
            "scripts/analyze_neb.py"

3.4 Overriding Specific Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    # Use your custom visualization instead
    use rule run_neb from neb_orchestrator as neb_run_neb
    use rule * from neb_orchestrator as neb_*  # Other rules

    rule my_custom_viz:
        input:
            neb_run_neb.output.results_dat
        output:
            "plots/{system}/custom.png"
        script:
            "scripts/my_viz.py"

4 Directory Structure
---------------------

.. code:: text

    workflow/
    ├── Snakefile              # Main entry point, rule all
    ├── rules/
    │   ├── get_model.smk      # Model retrieval
    │   ├── align_endpoints.smk # IRA alignment
    │   ├── minimize.smk       # Endpoint minimization
    │   ├── generate_idpp.smk  # IDPP path (optional)
    │   ├── run_neb.smk        # NEB optimization
    │   ├── visualize.smk      # Plotting
    │   └── validate_path.smk  # Path validation
    └── envs/
        ├── model.yaml         # Model retrieval env
        ├── alignment.yaml     # IRA alignment env
        ├── minimize.yaml      # Minimization env
        ├── idpp.yaml          # IDPP env
        ├── neb.yaml           # NEB optimization env
        └── visualize.yaml     # Plotting env

5 Conda Environments
--------------------

Each rule has its own environment in ``workflow/envs/*.yaml``. Environments are:

- Minimal (only required dependencies)

- Pinned to specific versions for reproducibility

- Automatically managed by Snakemake ``--use-conda``

5.1 Adding Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

Edit the appropriate ``workflow/envs/*.yaml``:

.. code:: yaml

    name: neb-optimization
    channels:
      - conda-forge
      - metatensor
    dependencies:
      - python=3.11
      - pip
      - pip:
          - eonclient>=0.1.0
          - your-new-package>=1.0.0

6 Debugging
-----------

6.1 Common Issues
~~~~~~~~~~~~~~~~~

.. table::

    +---------------------------+--------------------------------------------------+
    | Problem                   | Solution                                         |
    +===========================+==================================================+
    | ``MissingInputException`` | Check file paths in config                       |
    +---------------------------+--------------------------------------------------+
    | ``RuleException``         | Check rule docstring for expected inputs         |
    +---------------------------+--------------------------------------------------+
    | Conda env fails           | Run ``snakemake --conda-create-envs-only`` first |
    +---------------------------+--------------------------------------------------+
    | Plotting fails            | Check ``RGPYCRUMBS_AUTO_DEPS=1`` is set          |
    +---------------------------+--------------------------------------------------+

6.2 Verbose Output
~~~~~~~~~~~~~~~~~~

.. code:: bash

    # Show full traceback
    snakemake --configfile config.yaml -c4 --use-conda --verbose

    # Show conda env creation
    snakemake --conda-create-envs-only
    # Dry-run with reasons
    snakemake -n --configfile config.yaml --reason

7 Testing
---------

7.1 Validate Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    # Check YAML syntax
    pixi run lint

    # Validate workflow DAG
    pixi run validate

7.2 Test Single System
~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    # Run HCN example (fastest)
    pixi run -e eon hcn

    # Check outputs
    ls results/neb/hcn_isom/
    cat results/neb/hcn_isom/results.dat

8 Citation
----------

When extending or using this workflow:

::

    R. Goswami, M. Gunde, and H. Jónsson, "Enhanced climbing image nudged elastic band method with hessian eigenmode alignment," arXiv:2601.12630, Jan. 2026. doi: `10.48550/arXiv.2601.12630 <https://doi.org/10.48550/arXiv.2601.12630>`_.

9 Adding New Systems
--------------------

9.1 Quick Checklist
~~~~~~~~~~~~~~~~~~~

1. Prepare reactant/product structures (same atom order!)

2. Copy example config: ``cp examples/hcn_isom/config.yaml my_system.yaml``

3. Edit paths and system name

4. Validate: ``snakemake --configfile my_system.yaml -n``

5. Run: ``snakemake --configfile my_system.yaml -c4 --use-conda``

9.2 Common Mistakes
~~~~~~~~~~~~~~~~~~~

.. table::

    +------------------+----------------------+------------------------------+
    | Mistake          | Symptom              | Fix                          |
    +==================+======================+==============================+
    | Wrong atom order | Barrier >5 eV        | Reorder atoms to match       |
    +------------------+----------------------+------------------------------+
    | Missing box      | eOn error            | Add 25 Å cubic box           |
    +------------------+----------------------+------------------------------+
    | Too few images   | NEB doesn't converge | Use 18-24 for medium systems |
    +------------------+----------------------+------------------------------+
    | kmax too low     | IRA alignment fails  | Try kmax=2.5-3.0             |
    +------------------+----------------------+------------------------------+

9.3 System Size Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. table::

    +-------+--------+------+------------+
    | Atoms | Images | kmax | Time (CPU) |
    +=======+========+======+============+
    |   3-5 |  12-16 |  1.8 | 2-5 min    |
    +-------+--------+------+------------+
    |  6-10 |  18-20 |  2.0 | 5-10 min   |
    +-------+--------+------+------------+
    | 11-20 |  20-24 |  2.5 | 10-20 min  |
    +-------+--------+------+------------+
    |   20+ |  24-30 |  3.0 | 20+ min    |
    +-------+--------+------+------------+

See `Adding Your Own System <tutorials/adding_systems.rst>`_ for detailed guide.
