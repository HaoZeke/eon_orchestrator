#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8.1",
#   "pyyaml>=6.0",
# ]
# ///
"""Validate that the Baker ablation is pinned to the archived NEB/MMF contract."""

from __future__ import annotations

import hashlib
from pathlib import Path

import click
import yaml


EXPECTED_MODEL_SHA256 = (
    "636e1d22f998f5868046f141238216022ccde2c6e2474b7d85ff1bb265580ed2"
)


def require_equal(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise click.ClickException(f"{label}: expected {expected!r}, found {actual!r}")


def require_close(label: str, actual: object, expected: float) -> None:
    try:
        actual_float = float(actual)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(f"{label}: expected {expected!r}, found {actual!r}") from exc
    if abs(actual_float - expected) > 1.0e-12:
        raise click.ClickException(f"{label}: expected {expected!r}, found {actual!r}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@click.command()
@click.option(
    "--repo-root",
    default=".",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--archive",
    default="../nebmmf_repro/nebmmf_archive.tar.xz",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def main(repo_root: Path, archive: Path) -> None:
    study_root = repo_root / "studies/geometric_spring_baker_ablation"
    config = yaml.safe_load((study_root / "config.yaml").read_text())

    require_equal("model.name", config["model"]["name"], "pet-mad-s-v1.5.0")
    require_equal("model.type", config["model"]["type"], "pet-mad-s")
    require_equal("compute.device", config["compute"]["device"], "cuda")

    archive_cfg = config.get("archive", {})
    require_equal("archive.path", archive_cfg.get("path"), str(archive))
    require_equal(
        "archive.model_path",
        archive_cfg.get("model_path"),
        "results/00_models/pet-mad-s-v1.5.0.pt",
    )
    require_equal("archive.model_sha256", archive_cfg.get("model_sha256"), EXPECTED_MODEL_SHA256)
    require_equal("archive.use_endpoints", archive_cfg.get("use_endpoints"), True)
    require_equal("archive.endpoint_root", archive_cfg.get("endpoint_root"), "results/01_endpoints")

    opt = config["neb"]["optimization"]
    require_equal("max_iterations", opt["max_iterations"], 1000)
    require_close("converged_force", opt["converged_force"], 0.05)
    require_close("max_move", opt["max_move"], 0.1)
    require_close("ci_after_rel", opt["ci_after_rel"], 0.8)
    require_close("ci_mmf_after_rel", opt["ci_mmf_after_rel"], 0.31)
    require_close("ci_mmf_angle", opt["ci_mmf_angle"], 0.85)
    require_equal("ci_mmf_ci_stability_count", opt["ci_mmf_ci_stability_count"], 5)

    archive_model = repo_root / config["paths"]["models"] / config["model"]["name"]
    archive_model = archive_model.with_suffix(".pt")
    if archive_model.is_file():
        require_equal("extracted model sha256", sha256(archive_model), EXPECTED_MODEL_SHA256)

    workflow = (study_root / "workflow/geometric_spring_density.smk").read_text()
    for needle in (
        "extract_archive_file",
        "archive_endpoint_path",
        "ci_mmf_after_rel",
        "ci_mmf_angle",
        "ci_mmf_ci_stability_count",
    ):
        if needle not in workflow:
            raise click.ClickException(f"workflow is missing {needle!r}")

    click.echo("archive contract ok")


if __name__ == "__main__":
    main()
