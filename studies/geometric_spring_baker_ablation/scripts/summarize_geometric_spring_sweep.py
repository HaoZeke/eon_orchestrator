#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8.1",
# ]
# ///
"""Summarize geometric-spring NEB image-density sweeps."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import click


FIELDNAMES = [
    "system",
    "spring_mode",
    "images",
    "success",
    "termination_reason",
    "barrier_eV",
    "saddle_image",
    "product_delta_eV",
    "max_projected_force_eVA",
    "total_force_calls",
    "neb_force_calls",
    "time_seconds",
    "number_of_extrema",
    "spacing_mean",
    "spacing_cv",
    "spacing_ratio",
    "kink_mean",
    "kink_p95",
    "kink_max",
]
CASE_OUTPUTS = ("results.dat", "neb.dat", "neb.con")


class CaseSummaryError(ValueError):
    """Raised when a case directory cannot be summarized."""


def parse_results(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        parts = raw_line.split(maxsplit=1)
        if len(parts) == 2:
            value, key = parts
            data[key] = value
    return data


def parse_neb_dat(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if not lines:
        return rows
    header = lines[0].split()
    for line in lines[1:]:
        values = line.split()
        if len(values) != len(header):
            continue
        rows.append({name: float(value) for name, value in zip(header, values)})
    return rows


def parse_neb_con(path: Path) -> list[list[tuple[float, float, float]]]:
    lines = path.read_text().splitlines()
    frames: list[list[tuple[float, float, float]]] = []
    idx = 0
    while idx + 8 < len(lines):
        try:
            n_components = int(lines[idx + 6].strip())
            counts = [int(value) for value in lines[idx + 7].split()]
        except ValueError:
            idx += 1
            continue
        if len(counts) != n_components:
            idx += 1
            continue

        cursor = idx + 9
        coords: list[tuple[float, float, float]] = []
        ok = True
        for count in counts:
            cursor += 2
            if cursor + count > len(lines):
                ok = False
                break
            for line in lines[cursor : cursor + count]:
                parts = line.split()
                if len(parts) < 3:
                    ok = False
                    break
                try:
                    coords.append((float(parts[0]), float(parts[1]), float(parts[2])))
                except ValueError:
                    ok = False
                    break
            if not ok:
                break
            cursor += count
        if ok and coords:
            frames.append(coords)
            idx = cursor
        else:
            idx += 1
    return frames


def flatten(frame: list[tuple[float, float, float]]) -> list[float]:
    return [value for xyz in frame for value in xyz]


def vec_sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def vec_norm(vec: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vec))


def unit(vec: list[float]) -> list[float] | None:
    norm = vec_norm(vec)
    if norm <= 0.0 or not math.isfinite(norm):
        return None
    return [value / norm for value in vec]


def kink_indices(frames: list[list[tuple[float, float, float]]]) -> list[float]:
    flat = [flatten(frame) for frame in frames]
    values: list[float] = []
    for prev_frame, frame, next_frame in zip(flat, flat[1:], flat[2:]):
        prev_edge = unit(vec_sub(frame, prev_frame))
        next_edge = unit(vec_sub(next_frame, frame))
        if prev_edge is None or next_edge is None:
            continue
        values.append(vec_norm(vec_sub(next_edge, prev_edge)))
    return values


def quantile(values: list[float], q: float) -> float:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return math.nan
    if len(finite) == 1:
        return finite[0]
    position = (len(finite) - 1) * q
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return finite[lo]
    weight = position - lo
    return finite[lo] * (1.0 - weight) + finite[hi] * weight


def safe_float(value: str | None) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except ValueError:
        return math.nan


def require_case_file(case_dir: Path, filename: str) -> Path:
    path = case_dir / filename
    if not path.is_file():
        raise CaseSummaryError(f"{case_dir}: missing {filename}")
    if path.stat().st_size == 0:
        raise CaseSummaryError(f"{case_dir}: empty {filename}")
    return path


def required_float(results: dict[str, str], key: str, case_dir: Path) -> float:
    value = safe_float(results.get(key))
    if not math.isfinite(value):
        raise CaseSummaryError(f"{case_dir}: missing or invalid {key}")
    return value


def required_int(results: dict[str, str], key: str, case_dir: Path) -> int:
    return int(required_float(results, key, case_dir))


def summarize_case(case_dir: Path) -> dict[str, object]:
    for filename in CASE_OUTPUTS:
        require_case_file(case_dir, filename)

    results = parse_results(case_dir / "results.dat")
    neb_rows = parse_neb_dat(case_dir / "neb.dat")
    if not results:
        raise CaseSummaryError(f"{case_dir}: results.dat has no key-value rows")
    if not neb_rows:
        raise CaseSummaryError(f"{case_dir}: neb.dat has no data rows")

    image_pairs = []
    idx = 0
    while f"image{idx}_energy" in results:
        image_pairs.append((idx, safe_float(results[f"image{idx}_energy"])))
        idx += 1

    finite_image_pairs = [(idx, energy) for idx, energy in image_pairs if math.isfinite(energy)]
    if not finite_image_pairs:
        raise CaseSummaryError(f"{case_dir}: no finite image energies in results.dat")

    saddle_image, barrier = max(finite_image_pairs, key=lambda item: item[1])
    projected = [
        safe_float(value)
        for key, value in results.items()
        if key.startswith("image") and key.endswith("_projected_force")
    ]

    coords = [row["rxn_coord"] for row in neb_rows if "rxn_coord" in row]
    spacings = [b - a for a, b in zip(coords, coords[1:]) if b > a]
    spacing_mean = sum(spacings) / len(spacings) if spacings else math.nan
    if spacings and spacing_mean > 0.0:
        variance = sum((x - spacing_mean) ** 2 for x in spacings) / len(spacings)
        spacing_cv = math.sqrt(variance) / spacing_mean
        spacing_ratio = max(spacings) / min(spacings)
    else:
        spacing_cv = math.nan
        spacing_ratio = math.nan

    termination = required_int(results, "termination_reason", case_dir)
    product_delta = safe_float(results.get(f"image{len(image_pairs) - 1}_energy"))
    kinks = kink_indices(parse_neb_con(case_dir / "neb.con"))
    if not kinks:
        raise CaseSummaryError(f"{case_dir}: neb.con did not yield finite kink metrics")
    kink_mean = sum(kinks) / len(kinks) if kinks else math.nan

    return {
        "system": case_dir.parent.parent.name,
        "spring_mode": case_dir.parent.name,
        "images": int(case_dir.name.removeprefix("images_")),
        "success": termination == 0,
        "termination_reason": termination,
        "barrier_eV": barrier,
        "saddle_image": saddle_image,
        "product_delta_eV": product_delta,
        "max_projected_force_eVA": max(projected) if projected else math.nan,
        "total_force_calls": required_int(results, "total_force_calls", case_dir),
        "neb_force_calls": required_int(results, "force_calls_neb", case_dir),
        "time_seconds": safe_float(results.get("time_seconds")),
        "number_of_extrema": required_int(results, "number_of_extrema", case_dir),
        "spacing_mean": spacing_mean,
        "spacing_cv": spacing_cv,
        "spacing_ratio": spacing_ratio,
        "kink_mean": kink_mean,
        "kink_p95": quantile(kinks, 0.95),
        "kink_max": max(kinks) if kinks else math.nan,
    }


def format_value(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.6g}"
    return str(value)


def write_markdown(rows: list[dict[str, object]], path: Path) -> None:
    columns = [
        "system",
        "spring_mode",
        "images",
        "success",
        "barrier_eV",
        "saddle_image",
        "max_projected_force_eVA",
        "neb_force_calls",
        "spacing_cv",
        "kink_mean",
        "kink_p95",
        "spacing_ratio",
        "number_of_extrema",
    ]
    lines = [
        "# Geometric spring density sweep",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(format_value(row[col]) for col in columns) + " |")
    lines.append("")
    path.write_text("\n".join(lines))


def metric_delta(
    row: dict[str, object],
    baseline: dict[str, object],
    metric: str,
) -> float:
    value = row.get(metric)
    baseline_value = baseline.get(metric)
    if not isinstance(value, (int, float)) or not isinstance(
        baseline_value,
        (int, float),
    ):
        return math.nan
    return float(value) - float(baseline_value)


def write_real_data_approval(
    rows: list[dict[str, object]],
    path: Path,
    mode_baselines: dict[str, str],
) -> None:
    index = {
        (str(row["system"]), str(row["spring_mode"]), int(row["images"])): row
        for row in rows
    }
    comparisons: list[dict[str, object]] = []
    missing: list[str] = []
    for row in rows:
        mode = str(row["spring_mode"])
        baseline_mode = mode_baselines.get(mode)
        if not baseline_mode:
            continue
        key = (str(row["system"]), baseline_mode, int(row["images"]))
        baseline = index.get(key)
        if baseline is None:
            missing.append(
                f"{row['system']} images_{row['images']} {mode}->{baseline_mode}"
            )
            continue
        comparisons.append(
            {
                "system": row["system"],
                "images": row["images"],
                "mode": mode,
                "baseline_mode": baseline_mode,
                "success": row["success"],
                "baseline_success": baseline["success"],
                "delta_barrier_eV": metric_delta(row, baseline, "barrier_eV"),
                "delta_force_eVA": metric_delta(row, baseline, "max_projected_force_eVA"),
                "delta_neb_force_calls": metric_delta(row, baseline, "neb_force_calls"),
                "delta_kink_p95": metric_delta(row, baseline, "kink_p95"),
                "delta_extrema": metric_delta(row, baseline, "number_of_extrema"),
            }
        )
    if missing:
        sample = "\n".join(missing[:20])
        suffix = "" if len(missing) <= 20 else f"\n... {len(missing) - 20} more"
        raise click.ClickException(f"Missing real-data baselines:\n{sample}{suffix}")

    aggregate: dict[tuple[str, str], list[dict[str, object]]] = {}
    for comparison in comparisons:
        key = (str(comparison["mode"]), str(comparison["baseline_mode"]))
        aggregate.setdefault(key, []).append(comparison)

    lines = [
        "case: baker_petmad_layered_neb",
        f"summary_rows: {len(rows)}",
        f"comparisons: {len(comparisons)}",
        "",
        "mode_baselines:",
    ]
    for mode, baseline_mode in sorted(mode_baselines.items()):
        lines.append(f"  {mode}: {baseline_mode}")

    lines.extend(
        [
            "",
            "aggregate:",
            (
                "mode,baseline,n,success,baseline_success,"
                "mean_delta_force_eVA,mean_delta_kink_p95,"
                "mean_delta_neb_force_calls,mean_delta_extrema"
            ),
        ]
    )
    for (mode, baseline_mode), group in sorted(aggregate.items()):
        n = len(group)

        def mean(metric: str) -> float:
            values = [
                float(item[metric])
                for item in group
                if isinstance(item[metric], (int, float))
                and math.isfinite(float(item[metric]))
            ]
            return sum(values) / len(values) if values else math.nan

        success = sum(1 for item in group if bool(item["success"]))
        baseline_success = sum(1 for item in group if bool(item["baseline_success"]))
        lines.append(
            ",".join(
                [
                    mode,
                    baseline_mode,
                    str(n),
                    str(success),
                    str(baseline_success),
                    f"{mean('delta_force_eVA'):.6g}",
                    f"{mean('delta_kink_p95'):.6g}",
                    f"{mean('delta_neb_force_calls'):.6g}",
                    f"{mean('delta_extrema'):.6g}",
                ]
            )
        )

    lines.extend(
        [
            "",
            "comparison_rows:",
            (
                "system,images,mode,baseline,success,baseline_success,"
                "delta_barrier_eV,delta_force_eVA,delta_neb_force_calls,"
                "delta_kink_p95,delta_extrema"
            ),
        ]
    )
    for item in sorted(
        comparisons,
        key=lambda entry: (
            str(entry["system"]),
            int(entry["images"]),
            str(entry["mode"]),
        ),
    ):
        lines.append(
            ",".join(
                [
                    str(item["system"]),
                    str(item["images"]),
                    str(item["mode"]),
                    str(item["baseline_mode"]),
                    str(item["success"]).lower(),
                    str(item["baseline_success"]).lower(),
                    f"{float(item['delta_barrier_eV']):.6g}",
                    f"{float(item['delta_force_eVA']):.6g}",
                    f"{float(item['delta_neb_force_calls']):.6g}",
                    f"{float(item['delta_kink_p95']):.6g}",
                    f"{float(item['delta_extrema']):.6g}",
                ]
            )
        )
    lines.append("")
    path.write_text("\n".join(lines))


def validate_rows(rows: list[dict[str, object]], expected_count: int | None) -> None:
    if not rows:
        raise click.ClickException("No complete case directories were summarized")

    keys = [(row["system"], row["spring_mode"], row["images"]) for row in rows]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        sample = ", ".join(str(item) for item in duplicates[:5])
        raise click.ClickException(f"Duplicate summary rows: {sample}")

    if expected_count is not None and len(rows) != expected_count:
        raise click.ClickException(
            f"Expected {expected_count} summary rows, found {len(rows)}"
        )


@click.command()
@click.option(
    "--sweep-root",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--output-csv",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
)
@click.option(
    "--output-md",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
)
@click.option("--output-approval", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--mode-baselines-json",
    default="{}",
    help="JSON mapping of mode to baseline mode.",
)
@click.option(
    "--expected-count",
    type=int,
    default=None,
    help="Fail unless this many rows are summarized.",
)
def main(
    sweep_root: Path,
    output_csv: Path,
    output_md: Path,
    output_approval: Path | None,
    mode_baselines_json: str,
    expected_count: int | None,
) -> None:
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for path in sorted(sweep_root.glob("*/*/images_*")):
        try:
            rows.append(summarize_case(path))
        except CaseSummaryError as exc:
            errors.append(str(exc))
    if errors:
        sample = "\n".join(errors[:20])
        suffix = "" if len(errors) <= 20 else f"\n... {len(errors) - 20} more"
        raise click.ClickException(
            f"Failed to summarize {len(errors)} cases:\n{sample}{suffix}"
        )

    rows.sort(
        key=lambda row: (
            str(row["system"]),
            str(row["spring_mode"]),
            int(row["images"]),
        )
    )
    validate_rows(rows, expected_count)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(rows, output_md)
    if output_approval is not None:
        try:
            mode_baselines = json.loads(mode_baselines_json)
        except json.JSONDecodeError as exc:
            raise click.ClickException(f"Invalid --mode-baselines-json: {exc}") from exc
        if not isinstance(mode_baselines, dict):
            raise click.ClickException("--mode-baselines-json must decode to an object")
        write_real_data_approval(
            rows,
            output_approval,
            {str(key): str(value) for key, value in mode_baselines.items()},
        )


if __name__ == "__main__":
    main()
