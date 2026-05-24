# -*- mode: snakemake; -*-
"""Baker-set image-density ablation for the geometric NEB spring."""

import hashlib
from pathlib import Path
from rgpycrumbs.eon.helpers import write_eon_config
import json
import os
import shutil
import subprocess
import tarfile


STUDY_ROOT = config.get("study_root", "studies/geometric_spring_baker_ablation")
GEOM_ARCHIVE = config.get("archive", {})
GEOM_ARCHIVE_PATH = GEOM_ARCHIVE.get("path")
GEOM_ARCHIVE_MODEL_PATH = GEOM_ARCHIVE.get("model_path")
GEOM_ARCHIVE_MODEL_SHA256 = GEOM_ARCHIVE.get("model_sha256")
GEOM_ARCHIVE_ENDPOINT_ROOT = config.get("paths", {}).get(
    "archive_endpoints",
    f"{STUDY_ROOT}/resources/nebmmf_archive_endpoints",
)
GEOM_ARCHIVE_REFERENCE_ROOT = config.get("paths", {}).get(
    "archive_reference",
    f"{STUDY_ROOT}/results/archive_reference",
)
GEOM_ARCHIVE_REFERENCE_METHODS = list(GEOM_ARCHIVE.get("reference_methods", []))
GEOM_ARCHIVE_REFERENCE_IMAGES = [
    str(x) for x in GEOM_ARCHIVE.get("reference_images", [])
]
GEOM_SWEEP = config.get("sweeps", {}).get("geometric_spring_density", {})
GEOM_SWEEP_NAME = "geometric_spring_density"
GEOM_SWEEP_SYSTEMS = list(
    GEOM_SWEEP.get("systems", list(config.get("systems", {}).keys()))
)
GEOM_SWEEP_IMAGES = [str(x) for x in GEOM_SWEEP.get("images", [18, 36, 54, 72, 90])]
GEOM_SWEEP_MODES = GEOM_SWEEP.get(
    "spring_modes",
    {
        "hookean": {
            "geometric_spring": False,
            "energy_weighted": False,
            "spring": 5.0,
        },
        "hookean_energy_weighted": {
            "geometric_spring": False,
            "energy_weighted": True,
            "spring": 5.0,
        },
        "geometric": {
            "geometric_spring": True,
            "energy_weighted": False,
            "spring": 5.0,
        },
    },
)
GEOM_SWEEP_MODE_NAMES = list(GEOM_SWEEP_MODES.keys())
GEOM_SWEEP_MODE_BASELINES = {
    name: mode.get("baseline_mode")
    for name, mode in GEOM_SWEEP_MODES.items()
    if mode.get("baseline_mode")
}
GEOM_SWEEP_MODE_BASELINES_JSON = json.dumps(GEOM_SWEEP_MODE_BASELINES, sort_keys=True)
GEOM_SWEEP_ROOT = (
    config.get("paths", {}).get("sweeps", f"{STUDY_ROOT}/results/sweeps")
    + f"/{GEOM_SWEEP_NAME}"
)
GEOM_SWEEP_EXPECTED_CASES = (
    len(GEOM_SWEEP_SYSTEMS) * len(GEOM_SWEEP_MODE_NAMES) * len(GEOM_SWEEP_IMAGES)
)
GEOM_ARCHIVE_REFERENCE_EXPECTED_CASES = (
    len(GEOM_SWEEP_SYSTEMS)
    * len(GEOM_ARCHIVE_REFERENCE_METHODS)
    * len(GEOM_ARCHIVE_REFERENCE_IMAGES)
)
GEOM_VISUALS = GEOM_SWEEP.get("visuals", {})
GEOM_VISUAL_SYSTEMS = list(GEOM_VISUALS.get("systems", GEOM_SWEEP_SYSTEMS))
GEOM_VISUAL_IMAGES = [str(x) for x in GEOM_VISUALS.get("images", [90])]
GEOM_VISUAL_MODES = list(GEOM_VISUALS.get("spring_modes", GEOM_SWEEP_MODE_NAMES))
GEOM_VISUAL_PLOT_TYPES = list(
    GEOM_VISUALS.get("plot_types", ["profile_path", "profile_index", "landscape_rmsd"])
)
GEOM_VISUAL_EXPECTED_PLOTS = (
    len(GEOM_VISUAL_SYSTEMS)
    * len(GEOM_VISUAL_MODES)
    * len(GEOM_VISUAL_IMAGES)
    * len(GEOM_VISUAL_PLOT_TYPES)
)
UV_RUNNER = config.get("tools", {}).get("uv", "uv")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_archive_file(archive_path, member, output_path, expected_sha256=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:*") as archive:
        source = archive.extractfile(member)
        if source is None:
            raise FileNotFoundError(f"{archive_path}: missing archive member {member}")
        with output_path.open("wb") as handle:
            shutil.copyfileobj(source, handle)
    if expected_sha256 is not None:
        actual_sha256 = sha256_file(output_path)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"{output_path}: expected sha256 {expected_sha256}, got {actual_sha256}"
            )


def archive_endpoint_path(wildcards, endpoint):
    return f"{GEOM_ARCHIVE_ENDPOINT_ROOT}/{wildcards.system}/{endpoint}.con"


def geom_case_endpoint(wildcards, endpoint):
    if GEOM_ARCHIVE.get("use_endpoints", False):
        return archive_endpoint_path(wildcards, endpoint)
    return config["systems"][wildcards.system][endpoint]


def geom_archive_endpoint_outputs(endpoint):
    if not GEOM_ARCHIVE.get("use_endpoints", False):
        return []
    return expand(
        GEOM_ARCHIVE_ENDPOINT_ROOT + "/{system}/" + endpoint + ".con",
        system=GEOM_SWEEP_SYSTEMS,
    )


def geom_sweep_outputs(filename):
    return expand(
        GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}/" + filename,
        system=GEOM_SWEEP_SYSTEMS,
        spring_mode=GEOM_SWEEP_MODE_NAMES,
        images=GEOM_SWEEP_IMAGES,
    )


def geom_visual_outputs(filename):
    return expand(
        GEOM_SWEEP_ROOT + "/figures/{system}/{spring_mode}/images_{images}/{plot_type}/" + filename,
        system=GEOM_VISUAL_SYSTEMS,
        spring_mode=GEOM_VISUAL_MODES,
        images=GEOM_VISUAL_IMAGES,
        plot_type=GEOM_VISUAL_PLOT_TYPES,
    )


def geom_archive_reference_outputs(filename):
    if not GEOM_ARCHIVE_REFERENCE_METHODS or not GEOM_ARCHIVE_REFERENCE_IMAGES:
        return []
    return expand(
        GEOM_ARCHIVE_REFERENCE_ROOT
        + "/{system}/archive_{method}/images_{images}/"
        + filename,
        system=GEOM_SWEEP_SYSTEMS,
        method=GEOM_ARCHIVE_REFERENCE_METHODS,
        images=GEOM_ARCHIVE_REFERENCE_IMAGES,
    )


rule download_study_petmad_model:
    """Prepare the PET-MAD model used by the ablation."""
    input:
        archive=GEOM_ARCHIVE_PATH,
    output:
        f"{config['paths']['models']}/{config['model']['name']}.pt",
    params:
        model_name=config["model"]["name"],
        ckpt=f"{config['paths']['models']}/{config['model']['name']}.ckpt",
    threads: 2
    resources:
        runtime=config.get("resources", {}).get("analysis", {}).get("runtime", 90),
        mem_mb=config.get("resources", {}).get("analysis", {}).get("mem_mb", 32000),
        cpus_per_task=2,
        tasks=1,
        gpu=0,
    run:
        if GEOM_ARCHIVE_MODEL_PATH:
            extract_archive_file(
                input.archive,
                GEOM_ARCHIVE_MODEL_PATH,
                output[0],
                GEOM_ARCHIVE_MODEL_SHA256,
            )
        else:
            Path(config["paths"]["models"]).mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "curl",
                    "-fL",
                    "-o",
                    params.ckpt,
                    f"https://huggingface.co/lab-cosmo/upet/resolve/main/models/{params.model_name}.ckpt",
                ],
                check=True,
            )
            subprocess.run(["mtt", "export", params.ckpt], check=True)
            shutil.move(f"{params.model_name}.pt", output[0])


rule extract_geometric_spring_archive_endpoint:
    """Extract archive-minimized endpoints for a Baker system."""
    input:
        archive=GEOM_ARCHIVE_PATH,
    output:
        reactants=geom_archive_endpoint_outputs("reactant"),
        products=geom_archive_endpoint_outputs("product"),
    params:
        endpoint_root=GEOM_ARCHIVE.get("endpoint_root", "results/01_endpoints"),
    threads: 1
    resources:
        runtime=15,
        mem_mb=2000,
        cpus_per_task=1,
        tasks=1,
        gpu=0,
    run:
        with tarfile.open(input.archive, "r:*") as archive:
            members = {
                f"{params.endpoint_root}/{system}/{endpoint}.con": Path(
                    GEOM_ARCHIVE_ENDPOINT_ROOT
                )
                / system
                / f"{endpoint}.con"
                for system in GEOM_SWEEP_SYSTEMS
                for endpoint in ("reactant", "product")
            }
            pending = dict(members)
            for member in archive:
                target = pending.pop(member.name, None)
                if target is None:
                    continue
                source = archive.extractfile(member)
                if source is None:
                    raise FileNotFoundError(
                        f"{input.archive}: missing archive member {member.name}"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as handle:
                    shutil.copyfileobj(source, handle)
                if not pending:
                    break
            if pending:
                sample = "\n".join(sorted(pending)[:20])
                suffix = "" if len(pending) <= 20 else f"\n... {len(pending) - 20} more"
                raise FileNotFoundError(
                    f"{input.archive}: missing archive endpoint files:\n{sample}{suffix}"
                )


rule extract_geometric_spring_archive_reference:
    """Extract exact archived NEB/MMF reference outputs."""
    input:
        archive=GEOM_ARCHIVE_PATH,
    output:
        results=geom_archive_reference_outputs("results.dat"),
        con=geom_archive_reference_outputs("neb.con"),
        neb=geom_archive_reference_outputs("neb.dat"),
    params:
        reference_root=GEOM_ARCHIVE.get("reference_root", "results/03_neb"),
    threads: 1
    resources:
        runtime=15,
        mem_mb=2000,
        cpus_per_task=1,
        tasks=1,
        gpu=0,
    run:
        with tarfile.open(input.archive, "r:*") as archive:
            members = {
                f"{params.reference_root}/{system}/{method}/{filename}": Path(
                    GEOM_ARCHIVE_REFERENCE_ROOT
                )
                / system
                / f"archive_{method}"
                / f"images_{images}"
                / filename
                for system in GEOM_SWEEP_SYSTEMS
                for method in GEOM_ARCHIVE_REFERENCE_METHODS
                for images in GEOM_ARCHIVE_REFERENCE_IMAGES
                for filename in ("results.dat", "neb.con", "neb.dat")
            }
            pending = dict(members)
            for member in archive:
                target = pending.pop(member.name, None)
                if target is None:
                    continue
                source = archive.extractfile(member)
                if source is None:
                    raise FileNotFoundError(
                        f"{input.archive}: missing archive member {member.name}"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as handle:
                    shutil.copyfileobj(source, handle)
                if not pending:
                    break
            if pending:
                sample = "\n".join(sorted(pending)[:20])
                suffix = "" if len(pending) <= 20 else f"\n... {len(pending) - 20} more"
                raise FileNotFoundError(
                    f"{input.archive}: missing archive reference files:\n{sample}{suffix}"
                )


rule run_geometric_spring_density_case:
    """Run one Baker-system image-count/spring-mode case."""
    input:
        reactant=lambda wildcards: geom_case_endpoint(wildcards, "reactant"),
        product=lambda wildcards: geom_case_endpoint(wildcards, "product"),
        model=f"{config['paths']['models']}/{config['model']['name']}.pt",
    output:
        results_dat=GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}/results.dat",
        neb_con=GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}/neb.con",
        neb_dat=GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}/neb.dat",
    params:
        opath=GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}",
        device=config["compute"]["device"],
        max_iterations=config.get("neb", {}).get("optimization", {}).get("max_iterations", 2000),
        converged_force=config.get("neb", {}).get("optimization", {}).get("converged_force", 0.0514221),
        opt_method=config.get("neb", {}).get("optimization", {}).get("opt_method", "lbfgs"),
        max_move=config.get("neb", {}).get("optimization", {}).get("max_move", 0.05),
        ew_ksp_min=config.get("neb", {}).get("optimization", {}).get("ew_ksp_min", 0.972),
        ew_ksp_max=config.get("neb", {}).get("optimization", {}).get("ew_ksp_max", 9.72),
        ew_trigger=config.get("neb", {}).get("optimization", {}).get("ew_trigger", 0.5),
        climbing_image_method=config.get("neb", {}).get("optimization", {}).get("climbing_image_method", True),
        ci_after_rel=config.get("neb", {}).get("optimization", {}).get("ci_after_rel", 0.5),
        ci_mmf=config.get("neb", {}).get("optimization", {}).get("ci_mmf", True),
        ci_mmf_after_rel=config.get("neb", {}).get("optimization", {}).get("ci_mmf_after_rel", 0.5),
        ci_mmf_angle=config.get("neb", {}).get("optimization", {}).get("ci_mmf_angle", 0.9),
        ci_mmf_nsteps=config.get("neb", {}).get("optimization", {}).get("ci_mmf_nsteps", 1000),
        ci_mmf_ci_stability_count=config.get("neb", {}).get("optimization", {}).get("ci_mmf_ci_stability_count", 5),
        ci_mmf_penalty_strength=config.get("neb", {}).get("optimization", {}).get("ci_mmf_penalty_strength"),
        ci_mmf_penalty_base=config.get("neb", {}).get("optimization", {}).get("ci_mmf_penalty_base"),
        mep_relax_default=config.get("neb", {}).get("optimization", {}).get("mep_relax", False),
        mep_relax_after=config.get("neb", {}).get("optimization", {}).get("mep_relax_after", 0.2),
        mep_relax_after_rel=config.get("neb", {}).get("optimization", {}).get("mep_relax_after_rel", 0.5),
        mep_relax_interval=config.get("neb", {}).get("optimization", {}).get("mep_relax_interval", 10),
        mep_relax_mode_iterations=config.get("neb", {}).get("optimization", {}).get("mep_relax_mode_iterations", 4),
        mep_relax_min_kink=config.get("neb", {}).get("optimization", {}).get("mep_relax_min_kink", 0.2),
        mep_relax_step_factor=config.get("neb", {}).get("optimization", {}).get("mep_relax_step_factor", 0.5),
        mep_relax_curvature_floor=config.get("neb", {}).get("optimization", {}).get("mep_relax_curvature_floor", 0.0001),
        mep_relax_max_tangent_alignment=config.get("neb", {}).get("optimization", {}).get("mep_relax_max_tangent_alignment", 0.5),
        sidpp_growth_alpha=config.get("neb", {}).get("optimization", {}).get("sidpp_growth_alpha", 0.33),
        doubly_nudged_default=config.get("neb", {}).get("optimization", {}).get("doubly_nudged", False),
        elastic_band_default=config.get("neb", {}).get("optimization", {}).get("elastic_band", False),
        om_default=config.get("neb", {}).get("optimization", {}).get("onsager_machlup", False),
        om_optimize_k=config.get("neb", {}).get("optimization", {}).get("om_optimize_k", True),
        om_k_scale=config.get("neb", {}).get("optimization", {}).get("om_k_scale", 1.0),
        om_k_min=config.get("neb", {}).get("optimization", {}).get("om_k_min", 0.1),
        om_k_max=config.get("neb", {}).get("optimization", {}).get("om_k_max", 100.0),
        mode_cfg=lambda wildcards: GEOM_SWEEP_MODES[wildcards.spring_mode],
    threads: config.get("resources", {}).get("neb", {}).get("cpus_per_task", 8)
    resources:
        runtime=config.get("resources", {}).get("neb", {}).get("runtime", 180),
        mem_mb=config.get("resources", {}).get("neb", {}).get("mem_mb", 64000),
        cpus_per_task=config.get("resources", {}).get("neb", {}).get("cpus_per_task", 8),
        tasks=1,
        gpu=config.get("resources", {}).get("neb", {}).get(
            "gpu",
            1 if config.get("compute", {}).get("device") == "cuda" else 0,
        ),
    run:
        thread_count = str(threads)
        os.environ["OMP_NUM_THREADS"] = thread_count
        os.environ["OPENBLAS_NUM_THREADS"] = thread_count
        os.environ["MKL_NUM_THREADS"] = thread_count
        os.environ["VECLIB_MAXIMUM_THREADS"] = thread_count
        os.environ["NUMEXPR_NUM_THREADS"] = thread_count
        os.environ["BLIS_NUM_THREADS"] = thread_count

        mode_cfg = dict(params.mode_cfg)
        out_path = Path(params.opath)
        out_path.mkdir(parents=True, exist_ok=True)

        spring = float(mode_cfg.get("spring", config.get("neb", {}).get("optimization", {}).get("spring", 5.0)))
        geometric = bool(mode_cfg.get("geometric_spring", False))
        energy_weighted = bool(mode_cfg.get("energy_weighted", False))
        doubly_nudged = bool(mode_cfg.get("doubly_nudged", params.doubly_nudged_default))
        elastic_band = bool(mode_cfg.get("elastic_band", params.elastic_band_default))
        onsager_machlup = bool(mode_cfg.get("onsager_machlup", params.om_default))
        mep_relax = bool(mode_cfg.get("mep_relax", params.mep_relax_default))
        ci_mmf = bool(mode_cfg.get("ci_mmf", params.ci_mmf))
        ci_mmf_after_rel = float(mode_cfg.get("ci_mmf_after_rel", params.ci_mmf_after_rel))
        ci_mmf_angle = float(mode_cfg.get("ci_mmf_angle", params.ci_mmf_angle))
        ci_mmf_nsteps = int(mode_cfg.get("ci_mmf_nsteps", params.ci_mmf_nsteps))
        ci_mmf_ci_stability_count = int(
            mode_cfg.get(
                "ci_mmf_ci_stability_count",
                params.ci_mmf_ci_stability_count,
            )
        )
        ci_mmf_penalty_strength = mode_cfg.get(
            "ci_mmf_penalty_strength",
            params.ci_mmf_penalty_strength,
        )
        ci_mmf_penalty_base = mode_cfg.get(
            "ci_mmf_penalty_base",
            params.ci_mmf_penalty_base,
        )

        neb_parameters = {
            "images": int(wildcards.images),
            "spring": spring,
            "energy_weighted": str(energy_weighted).lower(),
            "ew_ksp_min": params.ew_ksp_min,
            "ew_ksp_max": params.ew_ksp_max,
            "ew_trigger": params.ew_trigger,
            "geometric_spring": str(geometric).lower(),
            "elastic_band": str(elastic_band).lower(),
            "doubly_nudged": str(doubly_nudged).lower(),
            "onsager_machlup": str(onsager_machlup).lower(),
            "om_optimize_k": str(params.om_optimize_k).lower(),
            "om_k_scale": params.om_k_scale,
            "om_k_min": params.om_k_min,
            "om_k_max": params.om_k_max,
            "initializer": "sidpp",
            "oversampling": "false",
            "oversampling_factor": 8,
            "sidpp_growth_alpha": params.sidpp_growth_alpha,
            "minimize_endpoints": "false",
            "climbing_image_method": str(params.climbing_image_method).lower(),
            "climbing_image_converged_only": "true",
            "ci_after": 0.5,
            "ci_after_rel": params.ci_after_rel,
            "ci_mmf": str(ci_mmf).lower(),
            "ci_mmf_after": 0.1,
            "ci_mmf_after_rel": ci_mmf_after_rel,
            "ci_mmf_angle": ci_mmf_angle,
            "ci_mmf_nsteps": ci_mmf_nsteps,
            "ci_mmf_ci_stability_count": ci_mmf_ci_stability_count,
            "mep_relax": str(mep_relax).lower(),
            "mep_relax_after": params.mep_relax_after,
            "mep_relax_after_rel": params.mep_relax_after_rel,
            "mep_relax_interval": params.mep_relax_interval,
            "mep_relax_mode_iterations": params.mep_relax_mode_iterations,
            "mep_relax_min_kink": params.mep_relax_min_kink,
            "mep_relax_step_factor": params.mep_relax_step_factor,
            "mep_relax_curvature_floor": params.mep_relax_curvature_floor,
            "mep_relax_max_tangent_alignment": params.mep_relax_max_tangent_alignment,
        }
        if ci_mmf_penalty_strength is not None:
            neb_parameters["ci_mmf_penalty_strength"] = ci_mmf_penalty_strength
        if ci_mmf_penalty_base is not None:
            neb_parameters["ci_mmf_penalty_base"] = ci_mmf_penalty_base

        neb_settings = {
            "Main": {
                "job": "nudged_elastic_band",
                "random_seed": 706253457,
            },
            "Potential": {
                "potential": "metatomic",
            },
            "Metatomic": {
                "model_path": str(Path(input.model).absolute()),
                "device": params.device,
            },
            "Nudged Elastic Band": neb_parameters,
            "Dimer": {
                "improved": "true",
                "opt_method": "cg",
                "remove_rotation": "false",
                "converged_angle": 10.0,
            },
            "Optimizer": {
                "max_iterations": params.max_iterations,
                "opt_method": params.opt_method,
                "max_move": params.max_move,
                "converged_force": params.converged_force,
            },
            "Debug": {
                "write_movies": "true",
            },
        }

        write_eon_config(out_path, neb_settings)
        shutil.copy2(os.path.abspath(input.reactant), out_path / "reactant.con")
        shutil.copy2(os.path.abspath(input.product), out_path / "product.con")

        eonbin = os.environ.get("EONCLIENT", "eonclient")
        if os.path.sep in eonbin:
            eon_exec = eonbin
            if not os.access(eon_exec, os.X_OK):
                raise FileNotFoundError(f"EONCLIENT is not executable: {eon_exec}")
        else:
            eon_exec = shutil.which(eonbin)
            if eon_exec is None:
                raise FileNotFoundError(f"Cannot find eOn executable on PATH: {eonbin}")

        subprocess.run([eon_exec], cwd=out_path, check=True)

        for produced in (output.results_dat, output.neb_con, output.neb_dat):
            produced_path = Path(produced)
            if not produced_path.is_file() or produced_path.stat().st_size == 0:
                raise RuntimeError(f"Missing or empty eOn output: {produced_path}")


rule summarize_geometric_spring_archive_reference:
    """Summarize exact archive reference outputs into CSV and Markdown tables."""
    input:
        results=geom_archive_reference_outputs("results.dat"),
        con=geom_archive_reference_outputs("neb.con"),
        neb=geom_archive_reference_outputs("neb.dat"),
    output:
        csv=GEOM_ARCHIVE_REFERENCE_ROOT + "/summary.csv",
        markdown=GEOM_ARCHIVE_REFERENCE_ROOT + "/summary.md",
    params:
        expected_count=GEOM_ARCHIVE_REFERENCE_EXPECTED_CASES,
    threads: 1
    resources:
        runtime=30,
        mem_mb=4000,
        cpus_per_task=1,
        tasks=1,
        gpu=0,
    shell:
        """
        {UV_RUNNER} run --script {STUDY_ROOT}/scripts/summarize_geometric_spring_sweep.py \
          --sweep-root {GEOM_ARCHIVE_REFERENCE_ROOT} \
          --output-csv {output.csv} \
          --output-md {output.markdown} \
          --expected-count {params.expected_count}
        """


rule summarize_geometric_spring_density:
    """Summarize the density sweep into CSV and Markdown tables."""
    input:
        results=geom_sweep_outputs("results.dat"),
        con=geom_sweep_outputs("neb.con"),
        neb=geom_sweep_outputs("neb.dat"),
    output:
        csv=GEOM_SWEEP_ROOT + "/summary.csv",
        markdown=GEOM_SWEEP_ROOT + "/summary.md",
        approval=GEOM_SWEEP_ROOT + "/real_data_approval.txt",
    params:
        expected_count=GEOM_SWEEP_EXPECTED_CASES,
        mode_baselines_json=GEOM_SWEEP_MODE_BASELINES_JSON,
    threads: 1
    resources:
        runtime=30,
        mem_mb=4000,
        cpus_per_task=1,
        tasks=1,
        gpu=0,
    shell:
        """
        {UV_RUNNER} run --script {STUDY_ROOT}/scripts/summarize_geometric_spring_sweep.py \
          --sweep-root {GEOM_SWEEP_ROOT} \
          --output-csv {output.csv} \
          --output-md {output.markdown} \
          --output-approval {output.approval} \
          --mode-baselines-json '{params.mode_baselines_json}' \
          --expected-count {params.expected_count}
        """


rule analyze_geometric_spring_density:
    """Run Stan post-processing for the Baker-set image-density ablation."""
    input:
        csv=GEOM_SWEEP_ROOT + "/summary.csv",
    output:
        markdown=GEOM_SWEEP_ROOT + "/bayesian_summary.md",
        samples=GEOM_SWEEP_ROOT + "/posterior_samples.csv",
    params:
        chains=GEOM_SWEEP.get("bayes", {}).get("chains", 4),
        samples=GEOM_SWEEP.get("bayes", {}).get("samples", 1000),
        warmup=GEOM_SWEEP.get("bayes", {}).get("warmup", 1000),
    threads: config.get("resources", {}).get("analysis", {}).get("cpus_per_task", 4)
    resources:
        runtime=config.get("resources", {}).get("analysis", {}).get("runtime", 90),
        mem_mb=config.get("resources", {}).get("analysis", {}).get("mem_mb", 32000),
        cpus_per_task=config.get("resources", {}).get("analysis", {}).get("cpus_per_task", 4),
        tasks=1,
        gpu=0,
    shell:
        """
        {UV_RUNNER} run --script {STUDY_ROOT}/scripts/analyze_geometric_spring_ablation.py \
          --summary-csv {input.csv} \
          --output-md {output.markdown} \
          --posterior-csv {output.samples} \
          --chains {params.chains} \
          --samples {params.samples} \
          --warmup {params.warmup}
        """


rule render_geometric_spring_density_visual:
    """Render one NEB profile or RMSD landscape with rgpycrumbs."""
    input:
        con=GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}/neb.con",
        dat=GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}/neb.dat",
    output:
        plot=GEOM_SWEEP_ROOT + "/figures/{system}/{spring_mode}/images_{images}/{plot_type}/plot.png",
    params:
        case_dir=GEOM_SWEEP_ROOT + "/{system}/{spring_mode}/images_{images}",
        cache=GEOM_SWEEP_ROOT + "/figures_cache/{system}/{spring_mode}/images_{images}/{plot_type}",
        facecolor=config.get("plotting", {}).get("facecolor", "white"),
        dpi=config.get("plotting", {}).get("figure", {}).get("dpi", 300),
        zoom_ratio=config.get("plotting", {}).get("figure", {}).get("zoom_ratio", 0.4),
        fontsize_base=config.get("plotting", {}).get("fonts", {}).get("base", 12),
        ira_kmax=config.get("plotting", {}).get("ira_kmax", 14),
        plot_type=lambda wildcards: "landscape" if wildcards.plot_type == "landscape_rmsd" else "profile",
        rc_mode=lambda wildcards: "rmsd" if wildcards.plot_type == "landscape_rmsd" else wildcards.plot_type.removeprefix("profile_"),
    threads: config.get("resources", {}).get("figures", {}).get("cpus_per_task", 4)
    resources:
        runtime=config.get("resources", {}).get("figures", {}).get("runtime", 60),
        mem_mb=config.get("resources", {}).get("figures", {}).get("mem_mb", 32000),
        cpus_per_task=config.get("resources", {}).get("figures", {}).get("cpus_per_task", 4),
        tasks=1,
        gpu=0,
    shell:
        """
        mkdir -p {params.cache}
        ROOT_DIR=$PWD
        cd {params.cache}
        python -m rgpycrumbs.cli eon plt-neb \
            --con-file "$ROOT_DIR/{input.con}" \
            --output-file "$ROOT_DIR/{output.plot}" \
            --plot-type "{params.plot_type}" \
            --rc-mode "{params.rc_mode}" \
            --plot-structures crit_points \
            --facecolor "{params.facecolor}" \
            --input-dat-pattern "$ROOT_DIR/{params.case_dir}/neb_*.dat" \
            --input-path-pattern "$ROOT_DIR/{params.case_dir}/neb_path_*.con" \
            --landscape-path all \
            --surface-type grad_imq \
            --show-pts \
            --dpi {params.dpi} \
            --zoom-ratio {params.zoom_ratio} \
            --fontsize-base {params.fontsize_base} \
            --ira-kmax {params.ira_kmax} \
            --show-legend
        """


rule manifest_geometric_spring_density_visuals:
    """Collect rendered sweep figures into a manifest."""
    input:
        plots=geom_visual_outputs("plot.png"),
    output:
        manifest=GEOM_SWEEP_ROOT + "/figures/manifest.tsv",
    params:
        expected_count=GEOM_VISUAL_EXPECTED_PLOTS,
    threads: 1
    resources:
        runtime=15,
        mem_mb=2000,
        cpus_per_task=1,
        tasks=1,
        gpu=0,
    shell:
        """
        {UV_RUNNER} run --script {STUDY_ROOT}/scripts/write_geometric_spring_visual_manifest.py \
          --sweep-root {GEOM_SWEEP_ROOT} \
          --output {output.manifest} \
          --expected-count {params.expected_count}
        """
