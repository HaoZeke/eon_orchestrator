=========================
Parameter Selection Guide
=========================

    :Date: 2026-03-13


1 Overview
----------

This document provides recommended parameter values for NEB Orchestrator based on system type and reaction class. These are starting points, not universal rules. Visual inspection of results is always required.

2 Recommended Parameters by System Type
---------------------------------------

.. table::

    +-------------------+------+--------+------------------------+---------------+-------------------------------+
    | System Size       | kmax | Images | Force Threshold (eV/Å) | Cell Size (Å) | Notes                         |
    +===================+======+========+========================+===============+===============================+
    | 5-20 atoms        |  1.8 |  12-16 |                  0.051 | 25³           | Standard organic molecules    |
    +-------------------+------+--------+------------------------+---------------+-------------------------------+
    | 20-50 atoms       |  2.5 |  18-24 |                  0.051 | 25³           | Medium systems                |
    +-------------------+------+--------+------------------------+---------------+-------------------------------+
    | 50+ atoms         |  3.0 |  24-30 |                  0.026 | 30³           | Large, complex systems        |
    +-------------------+------+--------+------------------------+---------------+-------------------------------+
    | H-transfer        |  1.5 |  12-16 |                  0.051 | 25³           | Soft modes, try multiple kmax |
    +-------------------+------+--------+------------------------+---------------+-------------------------------+
    | Pericyclic        |  2.0 |  18-24 |                  0.051 | 25³           | Inspect path carefully        |
    +-------------------+------+--------+------------------------+---------------+-------------------------------+
    | Surface reactions |  2.5 |  18-24 |                  0.051 | 30³           | Requires PBC modifications    |
    +-------------------+------+--------+------------------------+---------------+-------------------------------+

3 Parameter Descriptions
------------------------

3.1 IRA kmax (Å⁻¹)
~~~~~~~~~~~~~~~~~~

Controls permutation matching strictness in Iterative Rotational Alignment.

- **Low (1.0-1.5)**: Strict matching, works for well-behaved small molecules

- **Medium (1.5-2.5)**: Default range, balances strictness with flexibility

- **High (2.5-5.0)**: Loose matching for difficult atom mapping, may introduce errors

**When to adjust**:

- If IRA fails to find alignment: increase kmax

- If alignment looks chemically wrong: decrease kmax

- For symmetric molecules: try multiple values (1.5, 2.0, 2.5)

3.2 Number of NEB Images
~~~~~~~~~~~~~~~~~~~~~~~~

Total images including endpoints (reactant + product + intermediates).

- **12-16 images**: Simple reactions (single bond break/form)

- **18-24 images**: Moderate complexity (multiple bond changes)

- **24-30 images**: Complex rearrangements (pericyclic, sigmatropic)

**Trade-offs**:

- More images → better path resolution, higher computational cost

- Fewer images → faster, may miss intermediate features

3.3 Force Convergence Threshold (eV/Å)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **0.051 eV/Å** (10⁻³ Ha/Bohr): Standard, sufficient for most applications

- **0.026 eV/Å** (0.5×10⁻³ Ha/Bohr): High precision, kinetics studies

- **0.102 eV/Å** (2×10⁻³ Ha/Bohr): Quick screening, not for publication

3.4 Cell Size (Å)
~~~~~~~~~~~~~~~~~

Artificial box size for gas-phase calculations. Must be large enough to avoid periodic boundary artifacts.

- **20-25 Å**: Small molecules (<20 atoms)

- **25-30 Å**: Medium molecules (20-50 atoms)

- **30-40 Å**: Large molecules (>50 atoms)

**Rule of thumb**: At least 10 Å vacuum between molecule and box edge in all directions.

3.5 SIDPP Growth α
~~~~~~~~~~~~~~~~~~

Step size for adding new images in Sequential IDPP.

- **Default (0.33)**: Works for most systems

- **Lower (0.2-0.3)**: More conservative growth, better for complex reactions

- **Higher (0.4-0.5)**: Faster path generation, may introduce collisions

**When to adjust**: If IDPP path has atomic collisions, reduce α.

4 Decision Framework
--------------------

.. code:: text

    Start with defaults for your system size
            ↓
    Run workflow with default parameters
            ↓
    Visualize IDPP path (ase gui results/idpp/*/path/*.xyz)
            ↓
        ┌───┴───┐
        │       │
      Good    Bad
        │       │
        │       └─→ Try different kmax (1.5, 2.0, 2.5)
        │           Re-run alignment + IDPP
        │           Re-inspect
        │
        ↓
    Run full NEB optimization
        ↓
    Validate saddle (dimer search, DFT single-point)

5 Why Not Bayesian Optimization?
--------------------------------

5.1 The Temptation\*\*
~~~~~~~~~~~~~~~~~~~~~~

It's natural to ask: "Why not use Optuna or similar tools to automatically find optimal parameters?"

5.2 Why It Doesn't Work Here\*\*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **No automated objective function**

   - What metric determines "good" parameters?

   - Final energy? → Doesn't indicate correct mechanism

   - Convergence speed? → Fast convergence to wrong saddle is worse

   - Barrier height? → No reference value for novel reactions

   - Collision count? → Binary (pass/fail), not continuous for optimization

2. **High computational cost**

   - Bayesian optimization needs 20-50 trials to beat grid search

   - Each trial = full NEB calculation (hours to days)

   - Total time: weeks of compute vs. hours for 3-value grid search

3. **Low-dimensional search space**

   - Only 3-4 meaningful parameters

   - Most have weak sensitivity (SIDPP α)

   - Grid search with 3 values each is sufficient

4. **Human validation still required**

   - No automated metric correlates with "correct chemistry"

   - Visual inspection always needed

   - Automation provides false sense of security

5.3 When Bayesian Optimization **Would** Help\*\*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- High-throughput screening (1000+ reactions)

- Automated quality metric (comparison to known barriers)

- Cheap objective evaluation (MLIP, not DFT)

- Many parameters (10+ hyperparameters)

None of these apply to typical NEB workflow usage.

5.4 Current Best Approach\*\*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simple grid search with visual inspection:

.. code:: bash

    # Try 3 kmax values
    for kmax in 1.5 2.0 2.5; do
        snakemake --config alignment.kmax=$kmax \
                  --wildcards system=YourSystem
    done

    # Inspect all 3 paths
    ase gui results/idpp/YourSystem_kmax*/path/*.xyz

    # Pick best, run full NEB

Time: 3 × NEB runtime + 10 min inspection

6 Examples by Reaction Class
----------------------------

6.1 Proton Transfer (H-transfer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: yaml

    systems:
      h_transfer:
        reactant: path/to/reactant.con
        product: path/to/product.con
        use_ira: true

    alignment:
      kmax: 1.5  # Strict matching for light atoms

    neb:
      optimization:
        images: 12
        converged_force: 0.0514221

**Notes**: H atoms have soft modes. Try kmax = 1.5, 1.8, 2.0 and compare.

6.2 Pericyclic Reactions (Claisen, Cope, Diels-Alder)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: yaml

    alignment:
      kmax: 2.0  # Medium strictness

    neb:
      optimization:
        images: 18-24  # More images for complex path

**Notes**: 

- Backbone permutation critical

- Visual inspection mandatory

- Consider manual permutation based on mechanism

6.3 Isomerization (Simple)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: yaml

    alignment:
      kmax: 1.8  # Default works fine

    neb:
      optimization:
        images: 12-16

**Notes**: Usually straightforward, default parameters sufficient.

6.4 Surface Reactions
~~~~~~~~~~~~~~~~~~~~~

.. code:: yaml

    # Requires modified workflow for PBC
    alignment:
      kmax: 2.5
      # cell_size: not applicable (use slab model)

    neb:
      optimization:
        images: 18-24
        converged_force: 0.0514221

**Notes**: 

- Current workflow targets gas-phase only

- Surface reactions need PBC modifications

- Larger cell in surface-normal direction

7 Troubleshooting
-----------------

7.1 Problem: IRA alignment fails\*\*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Error about permutation matching, very high RMSD

**Solutions**:

1. Increase kmax (try 2.5, 3.0, 4.0)

2. Check for missing atoms or different formulas

3. Manually verify atom ordering in input files

7.2 Problem: IDPP path has collisions\*\*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Atoms unrealistically close (< 0.5 Å)

**Solutions**:

1. Reduce SIDPP α (try 0.25, 0.2)

2. Increase number of images

3. Check endpoint alignment (may be wrong permutation)

7.3 Problem: NEB doesn't converge\*\*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Max iterations reached, forces still high

**Solutions**:

1. Increase max\ :sub:`iterations`\ (2000, 3000)

2. Add more images (better path resolution)

3. Check initial path quality (may be too far from MEP)

4. Reduce max\ :sub:`move`\ (0.05 instead of 0.1)

7.4 Problem: Wrong saddle point\*\*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Saddle geometry doesn't match expected mechanism

**Solutions**:

1. Suspect permutation error

2. Try different kmax values

3. Manually permute based on chemical intuition

4. Launch dimer from multiple IDPP images

5. Compare with literature/reference calculations

8 References
------------

- IRA algorithm: Gunde et al., J. Chem. Inf. Model. 2021, 61, 5446-5457

- SIDPP: Schmerwitz et al., J. Chem. Theory Comput. 2024, 20, 1, 155-163

- NEB: Jonsson et al., 1998; Henkelman et al., J. Chem. Phys. 2000, 113, 9901

- L-BFGS: Liu & Nocedal, 1989

9 See Also
----------

- `Permutation Sensitivity <devnotes.rst>`_ - Detailed discussion of alignment limitations

- `Claisen Example <../examples/wip/claisen/README.rst>`_ - Case study in permutation challenges

- `rgpycrumbs documentation <https://rgpycrumbs.rgoswami.me>`_ - IRA alignment implementation details
