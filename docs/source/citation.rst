============================
How to Cite NEB Orchestrator
============================

    :Author: `Rohit Goswami <https://rgoswami.me>`_


How to Cite NEB Orchestrator
----------------------------

If you use NEB Orchestrator in your research, please cite the relevant papers based on methodology used.

Software Citation
~~~~~~~~~~~~~~~~~

cite:[goswami2026neborchestrator]

NEB Methods
~~~~~~~~~~~

When using the enhanced CI-NEB workflow:

cite:[goswami2026neb]

Enhanced Climbing Image NEB method with Hessian eigenmode alignment for improved saddle point convergence.

Visualization Methods
~~~~~~~~~~~~~~~~~~~~~

When using 2D reaction valley projection for visualization:

cite:[goswami2026valley]

The method maps NEB trajectories onto a two-dimensional projection defined by
permutation-corrected RMSD from reactant and product configurations, with a
rotated coordinate frame decomposing into reaction progress (``s``) and orthogonal
deviation (``d``).

Gaussian Process Methods
~~~~~~~~~~~~~~~~~~~~~~~~

When using GP-accelerated saddle searches or surface fitting:

cite:[goswami2025gpr goswami2025pruning]

- GPR-accelerated saddle point searches with efficient implementation

- Adaptive pruning for increased robustness and reduced computational overhead

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

When using Bayesian hierarchical models for performance analysis:

cite:[goswami2025bayesian]

Combined Citation
~~~~~~~~~~~~~~~~~

For papers using the complete workflow with all features:

cite:[goswami2026neborchestrator goswami2026neb goswami2026valley goswami2025gpr goswami2025pruning goswami2025bayesian]

Acknowledgments
~~~~~~~~~~~~~~~

.. code:: text

    NEB calculations were performed using the NEB Orchestrator workflow 
    (https://github.com/HaoZeke/eon_orchestrator). Enhanced CI-NEB method was employed 
    with Hessian eigenmode alignment [cite:@goswami2026neb]. Reaction path 
    visualization used the 2D reaction valley projection method [cite:@goswami2026valley]. 
    Gaussian process acceleration followed [cite:@goswami2025gpr @goswami2025pruning].

Related Software
~~~~~~~~~~~~~~~~

eOn
^^^

cite:[peterson2016]

PET-MAD
^^^^^^^

cite:[peterson2023petmad]

rgpycrumbs
^^^^^^^^^^

cite:[goswami2024rgpycrumbs]

chemparseplot
^^^^^^^^^^^^^

cite:[goswami2024chemparseplot]

metatensor/metatomic
^^^^^^^^^^^^^^^^^^^^

cite:[bigiMetatensorMetatomicFoundational2026]

See Also
~~~~~~~~

- `Main Documentation <../index.rst>`_

- `Tutorials <tutorials/index.rst>`_

- `README <../README.rst>`_
