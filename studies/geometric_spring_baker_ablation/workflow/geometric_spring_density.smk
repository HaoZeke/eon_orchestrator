# -*- mode: snakemake; -*-
"""Baker-set image-density ablation for the geometric NEB spring."""

from pathlib import Path
from rgpycrumbs.eon.helpers import write_eon_config
import os
import shutil
import subprocess


STUDY_ROOT = config.get("study_root", "studies/geometric_spring_baker_ablation")
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
GEOM_SWEEP_ROOT = (
    config.get("paths", {}).get("sweeps", f"{STUDY_ROOT}/results/sweeps")
    + f"/{GEOM_SWEEP_NAME}"
)
GEOM_VISUALS = GEOM_SWEEP.get("visuals", {})
GEOM_VISUAL_SYSTEMS = list(GEOM_VISUALS.get("systems", GEOM_SWEEP_SYSTEMS))
GEOM_VISUAL_IMAGES = [str(x) for x in GEOM_VISUALS.get("images", [90])]
GEOM_VISUAL_MODES = list(GEOM_VISUALS.get("spring_modes", GEOM_SWEEP_MODE_NAMES))
GEOM_VISUAL_PLOT_TYPES = list(
    GEOM_VISUALS.get("plot_types", ["profile_path", "profile_index", "landscape_rmsd"])
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


rule download_study_petmad_model:
    """Fetch and export the PET-MAD model used by the ablation."""
    output:
        protected(f"{config['paths']['models']}/{config['model']['name']}.pt"),
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
    shell:
        """
        mkdir -p {config[paths][models]}
        curl -fL -o {params.ckpt} \
          'https://huggingface.co/lab-cosmo/pet-mad/resolve/{config[model][version]}/models/{params.model_name}.ckpt'
        mtt export {params.ckpt}
        mv {params.model_name}.pt {output}
        """


rule run_geometric_spring_density_case:
    """Run one Baker-system image-count/spring-mode case."""
    input:
        reactant=lambda wildcards: config["systems"][wildcards.system]["reactant"],
        product=lambda wildcards: config["systems"][wildcards.system]["product"],
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
        ci_mmf_nsteps=config.get("neb", {}).get("optimization", {}).get("ci_mmf_nsteps", 1000),
        sidpp_growth_alpha=config.get("neb", {}).get("optimization", {}).get("sidpp_growth_alpha", 0.33),
        mode_cfg=lambda wildcards: GEOM_SWEEP_MODES[wildcards.spring_mode],
    threads: config.get("resources", {}).get("neb", {}).get("cpus_per_task", 8)
    resources:
        runtime=config.get("resources", {}).get("neb", {}).get("runtime", 180),
        mem_mb=config.get("resources", {}).get("neb", {}).get("mem_mb", 64000),
        cpus_per_task=config.get("resources", {}).get("neb", {}).get("cpus_per_task", 8),
        tasks=1,
        gpu=0,
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
            "Nudged Elastic Band": {
                "images": int(wildcards.images),
                "spring": spring,
                "energy_weighted": str(energy_weighted).lower(),
                "ew_ksp_min": params.ew_ksp_min,
                "ew_ksp_max": params.ew_ksp_max,
                "ew_trigger": params.ew_trigger,
                "geometric_spring": str(geometric).lower(),
                "initializer": "sidpp",
                "sidpp_growth_alpha": params.sidpp_growth_alpha,
                "minimize_endpoints": "false",
                "climbing_image_method": str(params.climbing_image_method).lower(),
                "climbing_image_converged_only": "true",
                "ci_after": 0.5,
                "ci_after_rel": params.ci_after_rel,
                "ci_mmf": str(params.ci_mmf).lower(),
                "ci_mmf_after": 0.1,
                "ci_mmf_after_rel": params.ci_after_rel,
                "ci_mmf_penalty_strength": 1.5,
                "ci_mmf_penalty_base": 0.4,
                "ci_mmf_angle": 0.9,
                "ci_mmf_nsteps": params.ci_mmf_nsteps,
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
        subprocess.run([eonbin], cwd=out_path, check=True)


rule summarize_geometric_spring_density:
    """Summarize the density sweep into CSV and Markdown tables."""
    input:
        results=geom_sweep_outputs("results.dat"),
        neb=geom_sweep_outputs("neb.dat"),
    output:
        csv=GEOM_SWEEP_ROOT + "/summary.csv",
        markdown=GEOM_SWEEP_ROOT + "/summary.md",
    threads: 1
    resources:
        runtime=30,
        mem_mb=4000,
        cpus_per_task=1,
        tasks=1,
        gpu=0,
    shell:
        """
        uv run --script {STUDY_ROOT}/scripts/summarize_geometric_spring_sweep.py \
          --sweep-root {GEOM_SWEEP_ROOT} \
          --output-csv {output.csv} \
          --output-md {output.markdown}
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
        uv run --script {STUDY_ROOT}/scripts/analyze_geometric_spring_ablation.py \
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
    threads: 1
    resources:
        runtime=15,
        mem_mb=2000,
        cpus_per_task=1,
        tasks=1,
        gpu=0,
    shell:
        """
        uv run --script {STUDY_ROOT}/scripts/write_geometric_spring_visual_manifest.py \
          --sweep-root {GEOM_SWEEP_ROOT} \
          --output {output.manifest}
        """
