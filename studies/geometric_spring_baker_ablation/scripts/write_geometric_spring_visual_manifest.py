#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8.1",
# ]
# ///
"""Write a manifest for rendered geometric-spring ablation figures."""

from __future__ import annotations

from pathlib import Path

import click


def parse_plot_path(sweep_root: Path, plot: Path) -> dict[str, str]:
    rel = plot.relative_to(sweep_root / "figures")
    parts = rel.parts
    return {
        "system": parts[0],
        "spring_mode": parts[1],
        "images": parts[2].removeprefix("images_"),
        "plot_type": parts[3],
        "path": str(plot),
    }


def validate_rows(rows: list[dict[str, str]], expected_count: int | None) -> None:
    if not rows:
        raise click.ClickException("No rendered plots found")

    keys = [
        (row["system"], row["spring_mode"], row["images"], row["plot_type"])
        for row in rows
    ]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        sample = ", ".join(str(item) for item in duplicates[:5])
        raise click.ClickException(f"Duplicate manifest rows: {sample}")

    if expected_count is not None and len(rows) != expected_count:
        raise click.ClickException(
            f"Expected {expected_count} rendered plots, found {len(rows)}"
        )


@click.command()
@click.option("--sweep-root", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--expected-count", type=int, default=None, help="Fail unless this many plots are found.")
def main(sweep_root: Path, output: Path, expected_count: int | None) -> None:
    plots = sorted((sweep_root / "figures").glob("*/*/images_*/*/plot.png"))
    rows = [parse_plot_path(sweep_root, plot) for plot in plots]
    validate_rows(rows, expected_count)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as handle:
        handle.write("system\tspring_mode\timages\tplot_type\tpath\n")
        for row in rows:
            handle.write(
                f"{row['system']}\t{row['spring_mode']}\t{row['images']}\t{row['plot_type']}\t{row['path']}\n"
            )


if __name__ == "__main__":
    main()
