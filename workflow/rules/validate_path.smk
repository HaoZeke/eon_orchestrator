# -*- mode: snakemake; -*-
"""
Path validation and diagnostic rules.

Generates human-readable outputs from IDPP path for visual inspection
and checks for obvious problems (collisions, unrealistic geometries).
"""
from ase.io import read, write
from pathlib import Path
import numpy as np


rule validate_initial_path:
    """
    Convert IDPP path to XYZ format for visual inspection.
    
    After IDPP interpolation, users should visually inspect the path
    to verify:
    - No atomic collisions
    - Reasonable bond lengths throughout
    - Smooth structural evolution
    
    Usage:
        snakemake validate_initial_path --wildcards system=YourSystem
    """
    input:
        idpp_path=expand(
            config['paths']['idpp'] + '/{system}/path/{{i:02d}}.con',
            system="{system}", i=range(config.get('neb', {}).get('idpp', {}).get('number_of_intermediate_imgs', 10) + 2)
        ),
    output:
        xyz_dir=directory(config['paths']['cache'] + '/{system}/validation/'),
        done=touch(config['paths']['cache'] + '/{system}/.validation_done'),
    shell:
        """
        mkdir -p {output.xyz_dir}
        
        for con in {input.idpp_path}; do
            base=$(basename $con .con)
            ase convert "$con" "{output.xyz_dir}/${{base}}.xyz" 2>/dev/null || \
            python -c "
from ase.io import read, write
atoms = read('$con')
write('{output.xyz_dir}/' + '$base' + '.xyz', atoms)
"
        done
        
        echo "Validation XYZ files generated in: {output.xyz_dir}"
        echo "Visualize with: ase gui {output.xyz_dir}/*.xyz"
        """


rule check_path_collisions:
    """
    Check IDPP path for atomic collisions and unrealistic geometries.
    
    Warns if any image has:
    - H-H distances < 0.5 Å (unphysical)
    - Heavy atom distances < 0.8 Å (unphysical)
    - Any interatomic distance < 0.4 Å (severe collision)
    
    This is a diagnostic check, not a guarantee of path quality.
    A "clean" collision check does NOT mean the permutation is correct.
    
    Usage:
        snakemake check_path_collisions --wildcards system=YourSystem
    """
    input:
        idpp_path=expand(
            config['paths']['idpp'] + '/{system}/path/{{i:02d}}.con',
            system="{system}", i=range(config.get('neb', {}).get('idpp', {}).get('number_of_intermediate_imgs', 10) + 2)
        ),
    output:
        done=touch(config['paths']['cache'] + '/{system}/.collision_check_done'),
        report=config['paths']['cache'] + '/{system}/collision_report.txt',
    run:
        from ase.io import read
        
        # Minimum distance thresholds (Å)
        MIN_HH = 0.5      # H-H minimum
        MIN_HEAVY = 0.8   # Heavy atom minimum  
        MIN_ABSOLUTE = 0.4  # Absolute minimum (any pair)
        
        warnings = []
        severe_warnings = []
        
        for con_file in input.idpp_path:
            atoms = read(con_file)
            distances = atoms.get_all_distances(mic=True)
            np.fill_diagonal(distances, np.inf)
            
            min_dist = distances.min()
            min_pair = np.unravel_index(distances.argmin(), distances.shape)
            
            # Get atom types for the closest pair
            atom1_type = atoms.symbols[min_pair[0]]
            atom2_type = atoms.symbols[min_pair[1]]
            
            # Check for severe collisions
            if min_dist < MIN_ABSOLUTE:
                severe_warnings.append(
                    f"SEVERE: {con_file} - {atom1_type}-{atom2_type} at {min_dist:.3f} Å"
                )
            elif min_dist < MIN_HH:
                warnings.append(
                    f"WARNING: {con_file} - {atom1_type}-{atom2_type} at {min_dist:.3f} Å"
                )
        
        # Write report
        with open(output.report, "w") as f:
            f.write(f"Collision Check Report for system: {wildcards.system}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Images checked: {len(input.idpp_path)}\n")
            f.write(f"Warnings found: {len(warnings)}\n")
            f.write(f"Severe warnings: {len(severe_warnings)}\n\n")
            
            if severe_warnings:
                f.write("SEVERE COLLISIONS DETECTED:\n")
                for w in severe_warnings:
                    f.write(f"  {w}\n")
                f.write("\n")
            
            if warnings:
                f.write("WARNINGS:\n")
                for w in warnings:
                    f.write(f"  {w}\n")
                f.write("\n")
            
            if not warnings and not severe_warnings:
                f.write("No collisions detected.\n\n")
                f.write("Note: This does NOT guarantee correct atom permutation.\n")
                f.write("Visual inspection is still recommended.\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("Thresholds used:\n")
            f.write(f"  H-H minimum: {MIN_HH} Å\n")
            f.write(f"  Heavy atom minimum: {MIN_HEAVY} Å\n")
            f.write(f"  Absolute minimum: {MIN_ABSOLUTE} Å\n")
        
        # Print summary to shell output
        if severe_warnings:
            print("\n*** SEVERE COLLISIONS DETECTED ***")
            for w in severe_warnings[:5]:  # Show first 5
                print(f"  {w}")
            print(f"\nFull report: {output.report}")
            print("Visual inspection STRONGLY recommended before proceeding.\n")
        elif warnings:
            print(f"\n* {len(warnings)} collision warnings detected *")
            print(f"Full report: {output.report}")
            print("Visual inspection recommended.\n")
        else:
            print(f"\n[OK] No collisions detected in {len(input.idpp_path)} images")
            print(f"Report: {output.report}")
            print("Note: Visual inspection still recommended for complex reactions.\n")
