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
  int<lower=1> S;
  array[N] int<lower=1, upper=M> mode;
  array[N] int<lower=1, upper=S> system;
  vector[N] x;
  array[N] int<lower=0, upper=1> success;
  real x90;
}
parameters {
  real alpha0;
  vector[M] alpha_mode;
  vector[M] beta_mode;
  vector[S] z_system;
  real<lower=0> sigma_system;
}
transformed parameters {
  vector[S] a_system = sigma_system * z_system;
}
model {
  alpha0 ~ normal(0, 2);
  alpha_mode ~ normal(0, 1);
  beta_mode ~ normal(0, 1);
  z_system ~ normal(0, 1);
  sigma_system ~ exponential(1);
  for (n in 1:N) {
    success[n] ~ bernoulli_logit(
      alpha0 + a_system[system[n]] + alpha_mode[mode[n]]
      + beta_mode[mode[n]] * x[n]
    );
  }
}
generated quantities {
  vector[M] p_success_at_36;
  vector[M] p_success_at_90;
  for (m in 1:M) {
    p_success_at_36[m] = inv_logit(alpha0 + alpha_mode[m]);
    p_success_at_90[m] = inv_logit(alpha0 + alpha_mode[m] + beta_mode[m] * x90);
  }
}
"""


COUNT_STAN = r"""
data {
  int<lower=1> N;
  int<lower=1> M;
  int<lower=1> S;
  array[N] int<lower=1, upper=M> mode;
  array[N] int<lower=1, upper=S> system;
  vector[N] x;
  array[N] int<lower=0> count;
  real x90;
}
parameters {
  real alpha0;
  vector[M] alpha_mode;
  vector[M] beta_mode;
  vector[S] z_system;
  real<lower=0> sigma_system;
  vector<lower=0>[M] phi_mode;
}
transformed parameters {
  vector[S] a_system = sigma_system * z_system;
}
model {
  alpha0 ~ normal(log(1000), 3);
  alpha_mode ~ normal(0, 1.5);
  beta_mode ~ normal(0, 1);
  z_system ~ normal(0, 1);
  sigma_system ~ exponential(1);
  phi_mode ~ exponential(0.2);
  for (n in 1:N) {
    count[n] ~ neg_binomial_2_log(
      alpha0 + a_system[system[n]] + alpha_mode[mode[n]]
      + beta_mode[mode[n]] * x[n],
      phi_mode[mode[n]]
    );
  }
}
generated quantities {
  vector[M] log_mu_at_36;
  vector[M] log_mu_at_90;
  for (m in 1:M) {
    log_mu_at_36[m] = alpha0 + alpha_mode[m];
    log_mu_at_90[m] = alpha0 + alpha_mode[m] + beta_mode[m] * x90;
  }
}
"""


STUDENT_T_STAN = r"""
data {
  int<lower=1> N;
  int<lower=1> M;
  int<lower=1> S;
  array[N] int<lower=1, upper=M> mode;
  array[N] int<lower=1, upper=S> system;
  vector[N] x;
  vector[N] y;
  real x90;
}
parameters {
  real alpha0;
  vector[M] alpha_mode;
  vector[M] beta_mode;
  vector[S] z_system;
  real<lower=0> sigma_system;
  vector<lower=0>[M] sigma_mode;
}
transformed parameters {
  vector[S] a_system = sigma_system * z_system;
}
model {
  alpha0 ~ normal(0, 5);
  alpha_mode ~ normal(0, 2);
  beta_mode ~ normal(0, 1);
  z_system ~ normal(0, 1);
  sigma_system ~ exponential(1);
  sigma_mode ~ exponential(1);
  for (n in 1:N) {
    y[n] ~ student_t(
      4,
      alpha0 + a_system[system[n]] + alpha_mode[mode[n]]
      + beta_mode[mode[n]] * x[n],
      sigma_mode[mode[n]]
    );
  }
}
generated quantities {
  vector[M] mu_at_36;
  vector[M] mu_at_90;
  for (m in 1:M) {
    mu_at_36[m] = alpha0 + alpha_mode[m];
    mu_at_90[m] = alpha0 + alpha_mode[m] + beta_mode[m] * x90;
  }
}
"""


@dataclass(frozen=True)
class MetricSpec:
    name: str
    title: str
    family: str
    response_column: str
    smaller_is_better: bool


METRICS = [
    MetricSpec(
        "neb_force_calls",
        "NEB force-call counts",
        "negative_binomial",
        "neb_force_calls",
        True,
    ),
    MetricSpec(
        "log_barrier_error_ev",
        "Barrier-error scaling",
        "student_t",
        "barrier_abs_error_eV",
        True,
    ),
    MetricSpec(
        "log_spacing_cv",
        "Spacing variation",
        "student_t",
        "spacing_cv",
        True,
    ),
    MetricSpec(
        "log_kink_mean",
        "Mean kink-index scaling",
        "student_t",
        "kink_mean",
        True,
    ),
]


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def read_summary(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["success_bool"] = frame["success"].map(parse_bool)
    numeric_columns = [
        "images",
        "barrier_eV",
        "neb_force_calls",
        "spacing_cv",
        "kink_mean",
    ]
    for column in numeric_columns:
        if column not in frame:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["x_log_density"] = np.log(frame["images"] / 36.0)
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


def index_values(values: pd.Series) -> dict[str, int]:
    return {value: index + 1 for index, value in enumerate(sorted(values.unique()))}


def base_data(frame: pd.DataFrame, modes: list[str], systems: list[str]) -> dict[str, object]:
    mode_index = {mode: i + 1 for i, mode in enumerate(modes)}
    system_index = {system: i + 1 for i, system in enumerate(systems)}
    return {
        "N": int(len(frame)),
        "M": int(len(modes)),
        "S": int(len(systems)),
        "mode": [mode_index[mode] for mode in frame["spring_mode"]],
        "system": [system_index[system] for system in frame["system"]],
        "x": frame["x_log_density"].astype(float).tolist(),
        "x90": math.log(90.0 / 36.0),
    }


def success_data(frame: pd.DataFrame, modes: list[str], systems: list[str]) -> dict[str, object]:
    data = base_data(frame, modes, systems)
    data["success"] = frame["success_bool"].astype(int).tolist()
    return data


def count_data(
    frame: pd.DataFrame,
    modes: list[str],
    systems: list[str],
    metric: MetricSpec,
) -> dict[str, object] | None:
    metric_frame = frame[frame[metric.response_column] > 0].copy()
    if len(metric_frame) < len(modes) + len(systems):
        return None
    data = base_data(metric_frame, modes, systems)
    data["count"] = metric_frame[metric.response_column].round().astype(int).tolist()
    return data


def continuous_data(
    frame: pd.DataFrame,
    modes: list[str],
    systems: list[str],
    metric: MetricSpec,
) -> dict[str, object] | None:
    metric_frame = frame[frame["success_bool"]].copy()
    metric_frame = metric_frame[
        metric_frame[metric.response_column].notna()
        & (metric_frame[metric.response_column] >= 0)
    ].copy()
    metric_frame["y"] = np.log(metric_frame[metric.response_column] + 1.0e-6)
    metric_frame = metric_frame[np.isfinite(metric_frame["y"])]
    if len(metric_frame) < len(modes) + len(systems):
        return None
    data = base_data(metric_frame, modes, systems)
    data["y"] = metric_frame["y"].astype(float).tolist()
    return data


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
            raise KeyError(
                f"missing Stan column for {base}[{index}]; first columns: {preview}"
            )
        resolved[mode] = pd.to_numeric(frame[matches[0]], errors="coerce")
    return resolved


def finite_draws(series: pd.Series) -> np.ndarray:
    values = series.to_numpy(dtype=float)
    return values[np.isfinite(values)]


def interval(values: np.ndarray) -> str:
    if len(values) == 0:
        return "n/a"
    return (
        f"{np.median(values):.4g} "
        f"[{np.quantile(values, 0.05):.4g}, {np.quantile(values, 0.95):.4g}]"
    )


def probability(lhs: np.ndarray, rhs: np.ndarray, op: str) -> float:
    n = min(len(lhs), len(rhs))
    if n == 0:
        return math.nan
    if op == "greater":
        return float(np.mean(lhs[:n] > rhs[:n]))
    if op == "less":
        return float(np.mean(lhs[:n] < rhs[:n]))
    raise ValueError(op)


def ratio(lhs_log: np.ndarray, rhs_log: np.ndarray) -> np.ndarray:
    n = min(len(lhs_log), len(rhs_log))
    if n == 0:
        return np.array([], dtype=float)
    return np.exp(lhs_log[:n] - rhs_log[:n])


def append_vector_draws(
    rows: list[dict[str, object]],
    fit: pd.DataFrame,
    modes: list[str],
    *,
    family: str,
    metric: str,
    parameters: list[str],
) -> None:
    for parameter in parameters:
        by_mode = vector_columns(fit, parameter, modes)
        for mode, draws in by_mode.items():
            for sample, value in enumerate(finite_draws(draws)):
                rows.append(
                    {
                        "sample": sample,
                        "family": family,
                        "metric": metric,
                        "spring_mode": mode,
                        "parameter": parameter,
                        "value": value,
                    }
                )


def write_samples(
    path: Path,
    modes: list[str],
    success_fit: pd.DataFrame,
    metric_fits: dict[str, pd.DataFrame],
    metric_specs: dict[str, MetricSpec],
) -> None:
    rows: list[dict[str, object]] = []
    append_vector_draws(
        rows,
        success_fit,
        modes,
        family="bernoulli",
        metric="success",
        parameters=["p_success_at_36", "p_success_at_90", "beta_mode"],
    )
    for metric_name, fit in metric_fits.items():
        spec = metric_specs[metric_name]
        parameters = (
            ["log_mu_at_36", "log_mu_at_90", "beta_mode", "phi_mode"]
            if spec.family == "negative_binomial"
            else ["mu_at_36", "mu_at_90", "beta_mode", "sigma_mode"]
        )
        append_vector_draws(
            rows,
            fit,
            modes,
            family=spec.family,
            metric=metric_name,
            parameters=parameters,
        )

    pd.DataFrame(rows).to_csv(path, index=False)


def write_success_section(
    lines: list[str],
    frame: pd.DataFrame,
    modes: list[str],
    success_fit: pd.DataFrame,
) -> None:
    p36 = {
        mode: finite_draws(draws)
        for mode, draws in vector_columns(success_fit, "p_success_at_36", modes).items()
    }
    p90 = {
        mode: finite_draws(draws)
        for mode, draws in vector_columns(success_fit, "p_success_at_90", modes).items()
    }
    slope = {
        mode: finite_draws(draws)
        for mode, draws in vector_columns(success_fit, "beta_mode", modes).items()
    }
    lines.extend(
        [
            "## Success model",
            "",
            "| spring_mode | successes | runs | p_success_36 | p_success_90 | density slope |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for mode in modes:
        mode_rows = frame[frame["spring_mode"] == mode]
        lines.append(
            f"| {mode} | {int(mode_rows['success_bool'].sum())} | {len(mode_rows)} | "
            f"{interval(p36[mode])} | {interval(p90[mode])} | {interval(slope[mode])} |"
        )

    if "geometric" in modes:
        lines.extend(["", "Success contrasts at 90 images:", ""])
        for mode in modes:
            if mode == "geometric":
                continue
            prob = probability(p90["geometric"], p90[mode], "greater")
            if np.isfinite(prob):
                lines.append(
                    f"- P(p_success_90(geometric) > p_success_90({mode})) = {prob:.3f}"
                )


def write_metric_section(
    lines: list[str],
    modes: list[str],
    spec: MetricSpec,
    fit: pd.DataFrame,
) -> None:
    if spec.family == "negative_binomial":
        value36_name = "log_mu_at_36"
        value90_name = "log_mu_at_90"
        scale_name = "phi_mode"
        value_label = "log mean count"
    else:
        value36_name = "mu_at_36"
        value90_name = "mu_at_90"
        scale_name = "sigma_mode"
        value_label = "log response"

    value36 = {
        mode: finite_draws(draws)
        for mode, draws in vector_columns(fit, value36_name, modes).items()
    }
    value90 = {
        mode: finite_draws(draws)
        for mode, draws in vector_columns(fit, value90_name, modes).items()
    }
    slope = {
        mode: finite_draws(draws)
        for mode, draws in vector_columns(fit, "beta_mode", modes).items()
    }
    scale = {
        mode: finite_draws(draws)
        for mode, draws in vector_columns(fit, scale_name, modes).items()
    }

    lines.extend(["", f"## {spec.title}", ""])
    lines.append(
        f"| spring_mode | {value_label} 36 | {value_label} 90 | density slope | scale |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for mode in modes:
        lines.append(
            f"| {mode} | {interval(value36[mode])} | {interval(value90[mode])} | "
            f"{interval(slope[mode])} | {interval(scale[mode])} |"
        )

    if "geometric" in modes and spec.smaller_is_better:
        lines.extend(["", "Geometric-to-comparator posterior ratios:", ""])
        for image_label, values in [("36", value36), ("90", value90)]:
            for mode in modes:
                if mode == "geometric":
                    continue
                draws = ratio(values["geometric"], values[mode])
                prob = float(np.mean(draws < 1.0)) if len(draws) else math.nan
                if np.isfinite(prob):
                    lines.append(
                        f"- {image_label} images vs {mode}: "
                        f"ratio {interval(draws)}, P(ratio < 1) = {prob:.3f}"
                    )


def write_markdown(
    path: Path,
    frame: pd.DataFrame,
    modes: list[str],
    success_fit: pd.DataFrame,
    metric_fits: dict[str, pd.DataFrame],
) -> None:
    metric_by_name = {metric.name: metric for metric in METRICS}
    lines = [
        "# Bayesian geometric-spring Baker ablation",
        "",
        "The analysis fits a Bernoulli-logit success model, a negative-binomial "
        "force-call model, and Student-t models for log barrier error, spacing "
        "variation, and kink index.  Each model uses Baker-system random "
        "intercepts and spring-mode density slopes on log(image_count / 36).",
        "",
    ]
    write_success_section(lines, frame, modes, success_fit)
    for metric_name, fit in metric_fits.items():
        write_metric_section(lines, modes, metric_by_name[metric_name], fit)

    lines.append("")
    path.write_text("\n".join(lines))


@click.command()
@click.option(
    "--summary-csv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--output-md", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--posterior-csv",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
)
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
    systems = sorted(frame["system"].unique())
    metric_by_name = {metric.name: metric for metric in METRICS}

    success_fit = sample_model(
        SUCCESS_STAN,
        success_data(frame, modes, systems),
        seed=seed,
        chains=chains,
        samples=samples,
        warmup=warmup,
    )

    metric_fits: dict[str, pd.DataFrame] = {}
    for offset, metric in enumerate(METRICS, start=1):
        data = (
            count_data(frame, modes, systems, metric)
            if metric.family == "negative_binomial"
            else continuous_data(frame, modes, systems, metric)
        )
        if data is None:
            continue
        program = COUNT_STAN if metric.family == "negative_binomial" else STUDENT_T_STAN
        metric_fits[metric.name] = sample_model(
            program,
            data,
            seed=seed + offset,
            chains=chains,
            samples=samples,
            warmup=warmup,
        )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    posterior_csv.parent.mkdir(parents=True, exist_ok=True)
    write_samples(posterior_csv, modes, success_fit, metric_fits, metric_by_name)
    write_markdown(output_md, frame, modes, success_fit, metric_fits)


if __name__ == "__main__":
    main()
