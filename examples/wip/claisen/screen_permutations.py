#!/usr/bin/env python3
"""
Permutation screening for Claisen rearrangement.

Generates atom permutations and evaluates with 3-point IDPP to find
low-barrier candidates for full NEB calculation.

Usage:
    python screen_permutations.py reactant.con product.con --n-permutations 50
"""
import argparse
from pathlib import Path
from ase import Atoms
from ase.io import read, write
from ase.neb import NEB
from ase.optimize import LBFGS
import numpy as np
from scipy.optimize import linear_sum_assignment


def read_con(path: str) -> Atoms:
    """Read eOn .con file as ASE Atoms."""
    atoms = read(path, format="espresso-in")
    return atoms


def write_con(atoms: Atoms, path: str) -> None:
    """Write ASE Atoms as eOn .con file."""
    write(path, atoms, format="espresso-in")


def minimize_rotation_and_translation(ref: Atoms, mobile: Atoms) -> None:
    """Align mobile to ref by minimizing RMSD."""
    from rgpycrumbs.eon.alignment import minimize_rotation_and_translation
    minimize_rotation_and_translation(ref, mobile)


def calculate_barrier(ref: Atoms, mobile: Atoms, calc) -> float:
    """
    Calculate IDPP midpoint energy as cheap barrier estimate.
    
    Uses 3-image NEB with IDPP interpolation. The middle image
    energy approximates the barrier (relative to endpoints).
    """
    minimize_rotation_and_translation(ref, mobile)
    images = [ref, ref.copy(), mobile]
    neb = NEB(images)
    neb.interpolate("idpp", mic=ref.pbc.any())
    images[1].calc = calc
    return images[1].get_potential_energy()


def generate_permutation(atoms: Atoms, perm: np.ndarray) -> Atoms:
    """Apply permutation to atom indices."""
    permuted = atoms.copy()
    permuted.positions = atoms.positions[perm]
    permuted.numbers = atoms.numbers[perm]
    return permuted


def hungarian_permutation(ref: Atoms, mobile: Atoms) -> np.ndarray:
    """Find optimal atom permutation using Hungarian algorithm."""
    from scipy.spatial.distance import cdist
    
    # Build cost matrix (distance between all atom pairs)
    cost = cdist(ref.positions, mobile.positions, metric="euclidean")
    
    # Solve assignment problem
    row_ind, col_ind = linear_sum_assignment(cost)
    return col_ind


def random_rotation_matrix() -> np.ndarray:
    """Generate random orthonormal rotation matrix."""
    from scipy.stats import ortho_group
    return ortho_group.rvs(3)


def main():
    parser = argparse.ArgumentParser(description="Screen permutations for NEB")
    parser.add_argument("reactant", type=str, help="Reactant .con file")
    parser.add_argument("product", type=str, help="Product .con file")
    parser.add_argument("--n-permutations", "-n", type=int, default=50,
                       help="Number of permutations to try")
    parser.add_argument("--output", "-o", type=str, default="candidates",
                       help="Output directory for candidates")
    parser.add_argument("--top", "-t", type=int, default=5,
                       help="Number of top candidates to save")
    args = parser.parse_args()
    
    # Read structures
    reactant = read_con(args.reactant)
    product = read_con(args.product)
    
    # Set up calculator (single-point energy)
    from metatomic.torch import MetatomicCalculator
    calc = MetatomicCalculator(
        model_path="pet-mad-v1.1.0.pt",
        device="cpu"
    )
    
    # Generate and evaluate permutations
    candidates = []
    
    # 1. Direct Hungarian (no rotation)
    perm = hungarian_permutation(reactant, product)
    product_perm = generate_permutation(product, perm)
    barrier = calculate_barrier(reactant, product_perm, calc)
    candidates.append(("Hungarian", barrier, perm, product_perm))
    
    # 2. Random rotations + Hungarian
    print(f"Screening {args.n_permutations} permutations...")
    for i in range(args.n_permutations):
        # Apply random rotation to product
        R = random_rotation_matrix()
        product_rot = product.copy()
        product_rot.positions = product.positions @ R.T
        
        # Find permutation for rotated structure
        perm = hungarian_permutation(reactant, product_rot)
        product_perm = generate_permutation(product, perm)
        
        # Evaluate barrier
        barrier = calculate_barrier(reactant, product_perm, calc)
        candidates.append((f"Rot{i:03d}", barrier, perm, product_perm))
        
        if (i + 1) % 10 == 0:
            print(f"  Evaluated {i + 1}/{args.n_permutations} permutations")
    
    # Sort by barrier (ascending)
    candidates.sort(key=lambda x: x[1])
    
    # Output results
    print(f"\n--- Top {args.top} Candidates ---")
    outdir = Path(args.output)
    outdir.mkdir(exist_ok=True)
    
    for rank, (name, barrier, perm, atoms) in enumerate(candidates[:args.top]):
        # Calculate relative barrier (vs reactant)
        reactant.calc = calc
        E_react = reactant.get_potential_energy()
        delta_E = barrier - E_react
        
        print(f"Rank {rank + 1}: {name} | ΔE‡ = {delta_E:+.3f} eV | E = {barrier:.4f} eV")
        
        # Save candidate
        outpath = outdir / f"candidate_{rank + 1:02d}_{name}.con"
        write_con(atoms, str(outpath))
    
    # Save summary
    summary_path = outdir / "screening_summary.txt"
    with open(summary_path, "w") as f:
        f.write("Permutation Screening Results\n")
        f.write("=" * 50 + "\n")
        f.write(f"Reactant: {args.reactant}\n")
        f.write(f"Product: {args.product}\n")
        f.write(f"Permutations tested: {args.n_permutations + 1}\n")
        f.write("\n")
        f.write("Rank | Name      | Barrier (eV) | ΔE‡ (eV)\n")
        f.write("-" * 50 + "\n")
        for rank, (name, barrier, perm, atoms) in enumerate(candidates[:args.top]):
            delta_E = barrier - E_react
            f.write(f"{rank + 1:4d} | {name:9s} | {barrier:12.4f} | {delta_E:+8.3f}\n")
    
    print(f"\nSaved top {args.top} candidates to {outdir}/")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
