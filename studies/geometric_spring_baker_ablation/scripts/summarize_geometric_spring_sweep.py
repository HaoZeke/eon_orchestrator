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


def summarize_case(case_dir: Path) -> dict[str, object]:
    results = parse_results(case_dir / "results.dat")
    neb_rows = parse_neb_dat(case_dir / "neb.dat")

    image_pairs = []
    idx = 0
    while f"image{idx}_energy" in results:
        image_pairs.append((idx, safe_float(results[f"image{idx}_energy"])))
        idx += 1

    saddle_image, barrier = max(image_pairs, key=lambda item: item[1])
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

    termination = int(safe_float(results.get("termination_reason")))
    product_delta = safe_float(results.get(f"image{len(image_pairs) - 1}_energy"))
    kinks = kink_indices(parse_neb_con(case_dir / "neb.con"))
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
        "total_force_calls": int(safe_float(results.get("total_force_calls"))),
        "neb_force_calls": int(safe_float(results.get("force_calls_neb"))),
        "time_seconds": safe_float(results.get("time_seconds")),
        "number_of_extrema": int(safe_float(results.get("number_of_extrema"))),
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


@click.command()
@click.option("--sweep-root", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output-csv", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--output-md", required=True, type=click.Path(dir_okay=False, path_type=Path))
def main(sweep_root: Path, output_csv: Path, output_md: Path) -> None:
    rows = [
        summarize_case(path)
        for path in sorted(sweep_root.glob("*/*/images_*"))
        if (path / "results.dat").exists()
        and (path / "neb.dat").exists()
        and (path / "neb.con").exists()
    ]
    rows.sort(key=lambda row: (str(row["system"]), str(row["spring_mode"]), int(row["images"])))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(rows, output_md)


if __name__ == "__main__":
    main()
