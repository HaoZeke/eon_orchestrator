#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8.1",
#   "numpy>=1.26",
#   "pandas>=2.2",
#   "pystan>=3.10,<4",
# ]
# ///
"""Bayesian Stan analysis for the geometric-spring Baker ablation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import click
import numpy as np
import pandas as pd
import stan


SUCCESS_STAN = r"""
data {
  int<lower=1> N;
  int<lower=1> M;
  array[N] int<lower=1, upper=M> mode;
  vector[N] x;
  array[N] int<lower=0, upper=1> success;
}
parameters {
  vector[M] alpha;
  vector[M] beta;
}
model {
  alpha ~ normal(0, 2);
  beta ~ normal(0, 1.5);
  for (n in 1:N) {
    success[n] ~ bernoulli_logit(alpha[mode[n]] + beta[mode[n]] * x[n]);
  }
}
generated quantities {
  vector[M] p_success_at_90;
  for (m in 1:M) {
    p_success_at_90[m] = inv_logit(alpha[m]);
  }
}
"""


REGRESSION_STAN = r"""
data {
  int<lower=1> N;
  int<lower=1> M;
  array[N] int<lower=1, upper=M> mode;
  vector[N] x;
  vector[N] y;
}
parameters {
  vector[M] mu_at_90;
  vector[M] slope;
  vector<lower=0>[M] sigma;
}
model {
  mu_at_90 ~ normal(0, 5);
  slope ~ normal(0, 2);
  sigma ~ exponential(1);
  for (n in 1:N) {
    y[n] ~ normal(mu_at_90[mode[n]] + slope[mode[n]] * x[n], sigma[mode[n]]);
  }
}
"""


@dataclass(frozen=True)
class MetricSpec:
    name: str
    title: str
    smaller_is_better: bool


METRICS = [
    MetricSpec("log_neb_force_calls", "NEB force-call scaling", True),
    MetricSpec("log_barrier_error_ev", "Barrier-error scaling", True),
    MetricSpec("log_spacing_cv", "Spacing variation", True),
]


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def read_summary(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["success_bool"] = frame["success"].map(parse_bool)
    for column in ["images", "barrier_eV", "neb_force_calls", "spacing_cv"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    max_images = frame["images"].max()
    frame["x_log_density"] = np.log(frame["images"] / max_images)
    return frame


def add_barrier_reference(frame: pd.DataFrame) -> pd.DataFrame:
    refs: dict[str, float] = {}
    max_images = frame["images"].max()
    for system, group in frame.groupby("system"):
        preferred = group[
            (group["spring_mode"] == "geometric")
            & (group["images"] == max_images)
            & group["success_bool"]
            & group["barrier_eV"].notna()
        ]["barrier_eV"]
        fallback = group[
            (group["images"] == max_images)
            & group["success_bool"]
            & group["barrier_eV"].notna()
        ]["barrier_eV"]
        if not preferred.empty:
            refs[system] = float(preferred.iloc[0])
        elif not fallback.empty:
            refs[system] = float(fallback.median())

    annotated = frame.copy()
    annotated["barrier_reference_eV"] = annotated["system"].map(refs)
    annotated["barrier_abs_error_eV"] = (
        annotated["barrier_eV"] - annotated["barrier_reference_eV"]
    ).abs()
    return annotated


def success_data(frame: pd.DataFrame, modes: list[str]) -> dict[str, object]:
    mode_index = {mode: i + 1 for i, mode in enumerate(modes)}
    return {
        "N": int(len(frame)),
        "M": int(len(modes)),
        "mode": [mode_index[mode] for mode in frame["spring_mode"]],
        "x": frame["x_log_density"].astype(float).tolist(),
        "success": frame["success_bool"].astype(int).tolist(),
    }


def metric_data(frame: pd.DataFrame, modes: list[str], metric: str) -> dict[str, object] | None:
    metric_frame = frame[frame["success_bool"]].copy()
    if metric == "log_neb_force_calls":
        metric_frame = metric_frame[metric_frame["neb_force_calls"] > 0].copy()
        metric_frame["y"] = np.log(metric_frame["neb_force_calls"])
    elif metric == "log_barrier_error_ev":
        metric_frame = metric_frame[metric_frame["barrier_abs_error_eV"].notna()].copy()
        metric_frame["y"] = np.log(metric_frame["barrier_abs_error_eV"] + 1.0e-6)
    elif metric == "log_spacing_cv":
        metric_frame = metric_frame[metric_frame["spacing_cv"].notna() & (metric_frame["spacing_cv"] >= 0)].copy()
        metric_frame["y"] = np.log(metric_frame["spacing_cv"] + 1.0e-6)
    else:
        raise ValueError(f"unknown metric: {metric}")

    metric_frame = metric_frame[np.isfinite(metric_frame["y"])]
    if len(metric_frame) < len(modes) + 2:
        return None

    mode_index = {mode: i + 1 for i, mode in enumerate(modes)}
    return {
        "N": int(len(metric_frame)),
        "M": int(len(modes)),
        "mode": [mode_index[mode] for mode in metric_frame["spring_mode"]],
        "x": metric_frame["x_log_density"].astype(float).tolist(),
        "y": metric_frame["y"].astype(float).tolist(),
    }


def sample_model(
    program: str,
    data: dict[str, object],
    *,
    seed: int,
    chains: int,
    samples: int,
    warmup: int,
) -> pd.DataFrame:
    posterior = stan.build(program, data=data, random_seed=seed)
    fit = posterior.sample(num_chains=chains, num_samples=samples, num_warmup=warmup)
    return fit.to_frame()


def vector_columns(frame: pd.DataFrame, base: str, modes: list[str]) -> dict[str, pd.Series]:
    resolved: dict[str, pd.Series] = {}
    for index, mode in enumerate(modes, start=1):
        pattern = re.compile(rf"^{re.escape(base)}(?:\.|:|\[){index}\]?$")
        matches = [column for column in frame.columns if pattern.match(column)]
        if not matches and base in frame.columns and len(modes) == 1:
            matches = [base]
        if not matches:
            preview = ", ".join(map(str, frame.columns[:20]))
            raise KeyError(f"missing Stan column for {base}[{index}]; first columns: {preview}")
        resolved[mode] = pd.to_numeric(frame[matches[0]], errors="coerce")
    return resolved


def finite_draws(series: pd.Series) -> np.ndarray:
    values = series.to_numpy(dtype=float)
    return values[np.isfinite(values)]


def interval(values: np.ndarray) -> str:
    if len(values) == 0:
        return "n/a"
    return f"{np.median(values):.4g} [{np.quantile(values, 0.05):.4g}, {np.quantile(values, 0.95):.4g}]"


def probability(lhs: np.ndarray, rhs: np.ndarray, op: str) -> float:
    n = min(len(lhs), len(rhs))
    if n == 0:
        return math.nan
    if op == "greater":
        return float(np.mean(lhs[:n] > rhs[:n]))
    if op == "less":
        return float(np.mean(lhs[:n] < rhs[:n]))
    raise ValueError(op)


def write_samples(
    path: Path,
    modes: list[str],
    success_fit: pd.DataFrame,
    regression_fits: dict[str, pd.DataFrame],
) -> None:
    rows: list[dict[str, object]] = []
    for parameter in ["p_success_at_90", "beta"]:
        by_mode = vector_columns(success_fit, parameter, modes)
        name = "success_slope" if parameter == "beta" else parameter
        for mode, draws in by_mode.items():
            for sample, value in enumerate(finite_draws(draws)):
                rows.append(
                    {
                        "sample": sample,
                        "family": "success",
                        "metric": "success",
                        "spring_mode": mode,
                        "parameter": name,
                        "value": value,
                    }
                )

    for metric, fit in regression_fits.items():
        for parameter in ["mu_at_90", "slope", "sigma"]:
            by_mode = vector_columns(fit, parameter, modes)
            for mode, draws in by_mode.items():
                for sample, value in enumerate(finite_draws(draws)):
                    rows.append(
                        {
                            "sample": sample,
                            "family": "gaussian",
                            "metric": metric,
                            "spring_mode": mode,
                            "parameter": parameter,
                            "value": value,
                        }
                    )

    pd.DataFrame(rows).to_csv(path, index=False)


def write_markdown(
    path: Path,
    frame: pd.DataFrame,
    modes: list[str],
    success_fit: pd.DataFrame,
    regression_fits: dict[str, pd.DataFrame],
) -> None:
    success_p = {mode: finite_draws(draws) for mode, draws in vector_columns(success_fit, "p_success_at_90", modes).items()}
    success_slope = {mode: finite_draws(draws) for mode, draws in vector_columns(success_fit, "beta", modes).items()}
    lines = [
        "# Bayesian geometric-spring Baker ablation",
        "",
        "The success model is a Bernoulli-logit Stan model with spring-mode intercepts and spring-mode log-density slopes. "
        "The continuous models are Gaussian Stan regressions on log(image_count / max_image_count) with spring-mode intercepts, slopes, and residual scales.",
        "",
        "## Success at 90 images",
        "",
        "| spring_mode | successes | runs | p_success_at_90 | density slope |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for mode in modes:
        mode_rows = frame[frame["spring_mode"] == mode]
        lines.append(
            f"| {mode} | {int(mode_rows['success_bool'].sum())} | {len(mode_rows)} | "
            f"{interval(success_p[mode])} | {interval(success_slope[mode])} |"
        )

    if "geometric" in modes:
        lines.extend(["", "## Pairwise posterior probabilities", ""])
        for mode in modes:
            if mode == "geometric":
                continue
            prob = probability(success_p["geometric"], success_p[mode], "greater")
            if np.isfinite(prob):
                lines.append(f"- P(p_success_at_90(geometric) > p_success_at_90({mode})) = {prob:.3f}")

    metric_by_name = {metric.name: metric for metric in METRICS}
    for metric_name, fit in regression_fits.items():
        spec = metric_by_name[metric_name]
        mu = {mode: finite_draws(draws) for mode, draws in vector_columns(fit, "mu_at_90", modes).items()}
        slope = {mode: finite_draws(draws) for mode, draws in vector_columns(fit, "slope", modes).items()}
        sigma = {mode: finite_draws(draws) for mode, draws in vector_columns(fit, "sigma", modes).items()}

        lines.extend(["", f"## {spec.title}", ""])
        lines.append("| spring_mode | log response at 90 images | density slope | sigma |")
        lines.append("| --- | ---: | ---: | ---: |")
        for mode in modes:
            lines.append(
                f"| {mode} | {interval(mu[mode])} | {interval(slope[mode])} | {interval(sigma[mode])} |"
            )
        if "geometric" in modes and spec.smaller_is_better:
            for mode in modes:
                if mode == "geometric":
                    continue
                prob = probability(mu["geometric"], mu[mode], "less")
                if np.isfinite(prob):
                    lines.append(f"- P(geometric has lower 90-image response than {mode}) = {prob:.3f}")

    lines.append("")
    path.write_text("\n".join(lines))


@click.command()
@click.option("--summary-csv", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output-md", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--posterior-csv", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--chains", default=4, show_default=True, type=int)
@click.option("--samples", default=1000, show_default=True, type=int)
@click.option("--warmup", default=1000, show_default=True, type=int)
@click.option("--seed", default=706253457, show_default=True, type=int)
def main(
    summary_csv: Path,
    output_md: Path,
    posterior_csv: Path,
    chains: int,
    samples: int,
    warmup: int,
    seed: int,
) -> None:
    frame = add_barrier_reference(read_summary(summary_csv))
    modes = sorted(frame["spring_mode"].unique())

    success_fit = sample_model(
        SUCCESS_STAN,
        success_data(frame, modes),
        seed=seed,
        chains=chains,
        samples=samples,
        warmup=warmup,
    )

    regression_fits: dict[str, pd.DataFrame] = {}
    for offset, metric in enumerate(METRICS, start=1):
        data = metric_data(frame, modes, metric.name)
        if data is None:
            continue
        regression_fits[metric.name] = sample_model(
            REGRESSION_STAN,
            data,
            seed=seed + offset,
            chains=chains,
            samples=samples,
            warmup=warmup,
        )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    posterior_csv.parent.mkdir(parents=True, exist_ok=True)
    write_samples(posterior_csv, modes, success_fit, regression_fits)
    write_markdown(output_md, frame, modes, success_fit, regression_fits)


if __name__ == "__main__":
    main()
